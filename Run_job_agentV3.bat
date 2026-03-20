@echo off
color 0B
echo ===========================================
echo        STARTING JOB SEARCH AGENT
echo ===========================================
echo.
cd /d "%USERPROFILE%\Desktop\Job Search Automation"
python job_hunter_v3.py
echo.
echo ===========================================
echo Process Complete! Check the "Job Search Automation" folder for the new Excel file.
echo You can safely close this window.
pause