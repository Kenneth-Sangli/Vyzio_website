@echo off
REM Setup script for vyzio_ads on Windows

echo Launching vyzio_ads setup...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo WARNING: Please edit .env with your environment variables
)

REM Create directories
if not exist logs mkdir logs
if not exist media mkdir media
if not exist staticfiles mkdir staticfiles

REM Run migrations
echo Running migrations...
python manage.py migrate

REM Create superuser
echo Creating superuser...
python manage.py createsuperuser

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Setup completed!
echo.
echo To start the server:
echo   python manage.py runserver
echo.
echo Admin panel:
echo   http://localhost:8000/admin/
