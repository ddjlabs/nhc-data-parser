@echo off
echo Creating Python virtual environment...
python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment
    exit /b %ERRORLEVEL%
)

echo Activating virtual environment...
call venv\Scripts\activate

if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment
    exit /b %ERRORLEVEL%
)

echo Installing dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies
    exit /b %ERRORLEVEL%
)

echo Initializing database...
python -c "from models import init_db; init_db()"

echo.
echo Setup completed successfully!
echo To activate the virtual environment, run: venv\Scripts\activate
echo To run the pipeline: python pipeline.py
echo To start the API server: uvicorn api:app --reload
