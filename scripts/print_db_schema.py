import asyncio
from app.core.config import settings
from app.db.session import engine
from sqlalchemy import inspect


def masked_url(url: str) -> str:
    # Mask password in URL for safe printing
    try:
        if '@' in url and '://' in url:
            scheme, rest = url.split('://', 1)
            if ':' in rest and '@' in rest:
                creds, host = rest.split('@', 1)
                if ':' in creds:
                    user, pwd = creds.split(':', 1)
                    return f"{scheme}://{user}:***@{host}"
        return url
    except Exception:
        return url


def list_columns():
    sync_engine = getattr(engine, 'sync_engine', None)
    if sync_engine is None:
        print('Could not access sync_engine from async engine.')
        return 2

    inspector = inspect(sync_engine)
    print('App DATABASE_URL (masked):', masked_url(settings.DATABASE_URL))
    print('\nTables in DB schema:')
    tables = inspector.get_table_names()
    for t in tables:
        print(' -', t)

    if 'products' in tables:
        print('\nColumns in `products` table:')
        cols = inspector.get_columns('products')
        for c in cols:
            print(' -', c['name'], c.get('type'))
    else:
        print('\n`products` table not found in this database.')
    return 0


if __name__ == '__main__':
    raise SystemExit(list_columns())
