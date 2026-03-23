# Setup on FEYNMACHINE (Windows)

## Prerequisites
- Python 3.11+ — https://python.org/downloads (check "Add to PATH")
- Git — https://git-scm.com
- Ollama for Windows — https://ollama.com/download/windows
- Node.js — https://nodejs.org (for NemoClaw)

## 1. Clone the repo
```powershell
git clone https://github.com/YOUR_USERNAME/alfonso-assistant.git
cd alfonso-assistant
```

## 2. Set up secrets
```powershell
copy .env.example .env
notepad .env
```
Fill in TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, NVIDIA_API_KEY.

For LACIE paths, use Windows-style:
```
LACIE_PHOTOS=D:\photos icloud
LACIE_ROOT=D:\
OLLAMA_MODELS_PATH=D:\ollama-models
```
(replace D:\ with the actual LaCie drive letter)

## 3. Python environment
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Point Ollama at the LaCie models
Set a persistent system environment variable so Ollama finds the models you already downloaded:
```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama-models", "Machine")
```
Then verify:
```powershell
ollama list
# should show llama3.1:8b
```

## 5. Run the bot
```powershell
.venv\Scripts\python telegram_bot.py
```

## 6. Auto-start on Windows login (Task Scheduler)
Run in PowerShell as Admin:
```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-WindowStyle Hidden -Command `"cd '$PWD'; .venv\Scripts\python telegram_bot.py`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartOnFailure -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "AlfonsoTelegramBot" -Action $action -Trigger $trigger -Settings $settings
```

## NemoClaw on Windows
```powershell
npm install -g nemoclaw
nemoclaw onboard
# choose Local Ollama when prompted
nemoclaw my-assistant connect
```
