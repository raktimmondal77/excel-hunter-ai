@echo off
title Excel Hunter AI Dashboard
cd /d "%~dp0"

echo ========================================================
echo         EXCEL HUNTER AI - FREELANCE ASSISTANT
echo ========================================================
echo.
echo Starting dashboard server...
echo Your dashboard URL: http://localhost:8501
echo.
echo (A browser window will open automatically in 2 seconds)
echo (If it does not open, simply paste http://localhost:8501 into your browser)
echo.

:: Automatically pop open default browser (Chrome, Edge, Firefox, Brave)
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8501"

:: Start Streamlit server
python -m streamlit run app.py --server.port 8501 --server.headless false --browser.serverAddress localhost

pause
