@echo off
REM --- UpdateGitRepo.bat ---
REM Push local commits to GitHub

cd /d "C:\Users\moe\Documents\Self Coding Bot"
echo.
echo 🔄 Pulling latest changes...
git pull origin main

echo.
echo 🚀 Pushing local commits to GitHub...
git push origin main

echo.
echo ✅ Repo updated successfully: https://github.com/aaronwins356/Self-Coding-Bot
pause
