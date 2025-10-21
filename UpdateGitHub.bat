@echo off
REM === Update GitHub repo from local folder ===
cd /d "C:\Users\moe\Documents\Self Coding Bot"

echo.
echo ==============================
echo   Updating GitHub Repository
echo ==============================

REM Check if this folder is a git repo
if not exist ".git" (
    echo Not a git repository. Initializing...
    git init
    git remote add origin https://github.com/aaronwins356/Self-Coding-Bot.git
)

echo Adding changes...
git add .

echo Committing changes...
git commit -m "Automated update from local folder" || echo No new changes to commit.

echo Pushing to GitHub...
git push origin main

echo.
echo Repository updated successfully!
pause
