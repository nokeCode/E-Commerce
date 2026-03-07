@echo off
REM start-dev.bat - Windows cmd wrapper
REM Usage: start-dev.bat [host:port]
cd /d "%~dp0"
if exist myenv\Scripts\activate.bat (
    call myenv\Scripts\activate.bat
) else (
    echo Virtual environment not found at myenv\Scripts\activate.bat
    pause
    exit /b 1
)
cd HStore
if "%1"=="" (
    python manage.py runserver
) else (
    python manage.py runserver %1
)
