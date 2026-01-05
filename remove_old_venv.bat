@echo off
REM Safe removal helper for legacy 'venv' folder. This will prompt before deleting.
echo This script will permanently delete the 'venv' folder in the repository root.
echo Make sure you REALLY want to remove it before proceeding.
set /p CONFIRM=Type DELETE to remove the folder, or anything else to cancel: 
if /I "%CONFIRM%"=="DELETE" (
  echo Deleting venv folder...
  rmdir /s /q venv
  echo Done.
) else (
  echo Cancelled. No changes made.
)
pause
