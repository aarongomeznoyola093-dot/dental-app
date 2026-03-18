@echo off
TITLE Sistema Dental Criss - Launcher
echo --- INICIANDO MOTORES ---


start /min "Prometheus" "C:\Users\aaron\Documents\Prometheus\prometheus-3.7.3.windows-amd64"


start /min "Grafana" "C:\Users\aaron\Downloads\grafana-enterprise_12.3.0_19497075765_windows_amd64\grafana-12.3.0\bin"


timeout /t 3 /nobreak >nul


start http://localhost:8000/app/login.html


echo Iniciando Servidor Web...
python -m uvicorn app.main:app --reload --port 8000