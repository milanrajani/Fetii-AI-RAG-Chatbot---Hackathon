@echo off
echo Setting up OpenAI API key...
echo.
set /p API_KEY="Enter your OpenAI API key: "

if "%API_KEY%"=="" (
    echo No API key provided. Exiting.
    pause
    exit /b 1
)

echo.
echo Setting environment variable...
setx OPENAI_API_KEY "%API_KEY%"
echo.
echo ✅ API key set successfully!
echo The API key will be automatically loaded every time you run the app.
echo.
pause

