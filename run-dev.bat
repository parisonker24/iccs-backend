@echo off
REM Activate the project's virtual environment and run Uvicorn
IF EXIST ".venv\Scripts\activate" (
  call .venv\Scripts\activate
) ELSE (
  echo Could not find .venv virtualenv. Please create/activate the correct venv.
  pause
  exit /b 1
)
echo Starting Uvicorn using .venv Python...
python -m uvicorn app.main:app --reload
