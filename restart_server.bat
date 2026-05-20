bat_content = """@echo off
title Restart Server Streamlit IMHLP
echo ===================================================
echo       RESTARTING STREAMLIT LOCALHOST SERVER        
echo ===================================================
echo.
echo [1/3] Mencari dan menghentikan server di port 8501...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do (
    echo Menghentikan proses PID: %%a...
    taskkill /F /PID %%a >nul 2>&1
)
echo.
echo [2/3] Memastikan tidak ada sisa proses python/streamlit...
taskkill /IM streamlit.exe /F >nul 2>&1
echo.
echo [3/3] Menjalankan kembali server Streamlit...
echo ---------------------------------------------------
python -m streamlit run app.py
pause
"""

with open("restart_server.bat", "w", encoding="utf-8") as f:
    f.write(bat_content)
print("File restart_server.bat berhasil dibuat.")