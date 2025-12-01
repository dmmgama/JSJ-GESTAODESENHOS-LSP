@echo off
title JSJ Gestao Desenhos - App
echo.
echo ========================================
echo   JSJ Gestao Desenhos - Iniciando...
echo ========================================
echo.

cd /d "%~dp0"

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo Iniciando Streamlit...
echo (A app vai abrir no browser)
echo.
echo Para fechar: Ctrl+C ou fechar esta janela
echo.

streamlit run app.py

pause
