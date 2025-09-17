# PowerShell script to set OpenAI API key
# Run this script once to set your API key permanently

Write-Host "Setting OpenAI API key..." -ForegroundColor Green

# Get API key from user
$apiKey = Read-Host "Enter your OpenAI API key"

if ($apiKey) {
    # Set environment variable for current session
    $env:OPENAI_API_KEY = $apiKey
    
    # Set environment variable permanently for user
    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $apiKey, "User")
    
    Write-Host "✅ API key set successfully!" -ForegroundColor Green
    Write-Host "The API key will be automatically loaded every time you run the app." -ForegroundColor Cyan
} else {
    Write-Host "❌ No API key provided." -ForegroundColor Red
}
