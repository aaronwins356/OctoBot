@echo off
REM === Update local files from GitHub repo ===
cd /d "C:\Users\moe\Documents\Self Coding Bot"

echo.
echo ==============================
echo   Updating Local Repository
echo ==============================

REM Check if folder is a git repo
if not exist ".git" (
    echo Not a git repository. Cloning repository...
    git clone https://github.com/aaronwins356/Self-Coding-Bot.git .
) else (
    echo Pulling latest changes from GitHub...
    git pull origin main
)

echo.
echo Local repository is up to date!
pause
