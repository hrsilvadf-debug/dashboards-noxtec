@echo off
title PRINTS NoxTec - Painel Validação Documentos
echo ============================================
echo  PRINTS NoxTec - Painel Validação Documentos
echo ============================================
echo.
cd /d "%~dp0validacao-documentos\backend"

if not exist venv\Scripts\python.exe (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Python nao encontrado.
        pause
        exit /b 1
    )
)

echo Ativando venv...
call venv\Scripts\activate

echo Instalando dependencias...
pip install --quiet --upgrade pip
pip install --only-binary=:all: --quiet fastapi pydantic uvicorn

echo.
echo ============================================
echo  Painel disponivel em:
echo  http://localhost:8001/static/index.html
echo.
echo  Login padrao:
echo    Email: admin@noxtec.com.br
echo    Senha: admin123
echo.
echo  Para popular dados de exemplo, rode em outro terminal:
echo    python seed_data.py
echo.
echo  Pressione Ctrl+C para parar o servidor.
echo ============================================
echo.

python main.py
pause
