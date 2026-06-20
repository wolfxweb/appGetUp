@echo off
echo ==========================================
echo   GetUp - Subindo ambiente local Docker
echo ==========================================
echo.

cd /d "%~dp0"

echo Parando container anterior (se existir)...
docker compose down 2>nul

echo.
echo Construindo e subindo container...
docker compose up --build -d

echo.
echo Aguardando container inicializar...
timeout /t 8 /nobreak >nul

echo.
echo Executando migracoes do banco de dados...
docker compose exec app python migrate_db.py

echo.
echo ==========================================
echo   Aplicacao disponivel em:
echo   http://localhost:9090
echo ==========================================
echo.
pause
