import ast
import glob
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'models')
MODEL_DIR = os.path.abspath(MODEL_DIR)

class ModelVisitor(ast.NodeVisitor):
    def __init__(self):
        self.current_class = None
        self.models = {}  # class_name -> {attr_name: (target, back_populates)}

    def visit_ClassDef(self, node):
        cls = node.name
        self.current_class = cls
        self.models.setdefault(cls, {})
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                # attribute name
                if len(stmt.targets) != 1:
                    continue
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    attr_name = target.id
                else:
                    continue
                # look for Call to relationship
                if isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, 'id', '') == 'relationship':
                    # first arg: class name or variable
                    target_class = None
                    back_pop = None
                    if stmt.value.args:
                        arg0 = stmt.value.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            target_class = arg0.value
                    for kw in stmt.value.keywords:
                        if kw.arg == 'back_populates' and isinstance(kw.value, ast.Constant):
                            back_pop = kw.value.value
                    if target_class:
                        self.models[cls][attr_name] = (target_class, back_pop)
        self.generic_visit(node)

def load_models():
    visitor = ModelVisitor()
    pyfiles = glob.glob(os.path.join(MODEL_DIR, '*.py'))
    for p in pyfiles:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                src = f.read()
            tree = ast.parse(src, filename=p)
            visitor.visit(tree)
        except Exception as e:
            print(f"Failed to parse {p}: {e}")
    return visitor.models


def check(models):
    problems = []
    # reverse map for quick lookup: class -> set of attr names
    for cls, attrs in models.items():
        for attr, (target, back) in attrs.items():
            if target not in models:
                problems.append(f"Class {cls}.{attr} references unknown target class '{target}'")
                continue
            # look for back attribute on target
            target_attrs = models[target]
            if back is None:
                problems.append(f"Class {cls}.{attr} -> {target} has no back_populates set")
                continue
            if back not in target_attrs:
                problems.append(f"Class {cls}.{attr} -> {target} expects back_populates='{back}' but {target} has no attribute '{back}'")
                continue
            # ensure symmetric
            t_target, t_back = target_attrs[back]
            if t_target != cls or t_back != attr:
                problems.append(f"Mismatch: {cls}.{attr} -> {target}.{back} points to ({t_target},{t_back})")
    return problems

if __name__ == '__main__':
    models = load_models()
    print(f"Found models: {list(models.keys())}\n")
    for cls, attrs in models.items():
        print(f"{cls}:")
        for a,(t,b) in attrs.items():
            print(f"  {a} -> {t} (back_populates={b})")
    print('\nChecking relationships...')
    problems = check(models)
    if not problems:
        print('No relationship/back_populates mismatches found')
    else:
        print('Problems found:')
        for p in problems:
            print(' -', p)
