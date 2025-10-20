@echo off
REM --- UpdateLocalFile.bat ---
REM Commit local changes in your Self-Coding-Bot project

cd /d "C:\Users\moe\Documents\Self Coding Bot"
git add .
set /p commitmsg="Enter commit message: "
git commit -m "%commitmsg%"
echo.
echo ✅ Local changes committed.
pause
