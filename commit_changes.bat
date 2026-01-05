@echo off
REM Commit workspace changes (run this in the repository root where Git is installed and in PATH)
git add -A
git commit -m "pydantic(v2): migrate class Config to model_config; add password test"
echo Commit complete. If this failed, ensure Git is installed and on PATH.
pause
