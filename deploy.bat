@echo off

cd /d C:\Ballconnecthub

call venv\Scripts\activate

git add .

set /p msg=Enter commit message:

git commit -m "%msg%"

git push

pause