# Job Hunter Agent: one-time setup on Windows 10 or 11.
#
#   Right-click this file → Run with PowerShell
#   (or in PowerShell:  powershell -ExecutionPolicy Bypass -File .\install.ps1)
#
# It installs the Python packages and the browser the agent fills forms in, creates your private folders (profile\
# and .env, never published), puts Job Hunter Agent in the Start menu and on the desktop with its icon, lets a
# jobhunter:// link open it, and opens it. The app then walks you through the rest on its Setup page.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$Root = $PSScriptRoot
function Say($t) { Write-Host "  $t" }

Write-Host "`nJob Hunter Agent · setup`n"

# 1 · Python 3.10 or newer
$py = $null
foreach ($c in @("py -3", "python", "python3")) {
  try {
    $v = & cmd /c "$c -c ""import sys; print(sys.version_info[0]*100+sys.version_info[1])"" 2>nul"
    if ($LASTEXITCODE -eq 0 -and [int]$v -ge 310) { $py = $c; break }
  } catch {}
}
if (-not $py) {
  Say "Python 3.10 or newer is needed. Install it, then run this again:"
  Say "  winget install Python.Python.3.12     (or https://www.python.org/downloads/, tick 'Add python.exe to PATH')"
  Read-Host "`nPress Enter to close"; exit 1
}
Say "Python: $py"

# 2 · a private Python environment for the agent, its packages, and the browser it fills forms in
if (-not (Test-Path ".venv\Scripts\python.exe")) { Say "Creating .venv…"; & cmd /c "$py -m venv .venv" }
$vpy  = Join-Path $Root ".venv\Scripts\python.exe"
$vpyw = Join-Path $Root ".venv\Scripts\pythonw.exe"
Say "Installing packages (a few minutes the first time)…"
& $vpy -m pip install --quiet --upgrade pip
& $vpy -m pip install --quiet -r requirements.txt
Say "Installing the browser the agent fills forms in…"
& $vpy -m playwright install chromium

# 3 · your private folders: profile\ (your storybook, empty) and .env (settings); nothing here is ever published
& $vpy -m agent.run init

# 4 · Start menu and desktop icons, with the app's icon
$icon = Join-Path $Root "docs\brand\app-icon\AppIcon.ico"
$shell = New-Object -ComObject WScript.Shell
foreach ($dir in @([Environment]::GetFolderPath("Programs"), [Environment]::GetFolderPath("Desktop"))) {
  $lnk = $shell.CreateShortcut((Join-Path $dir "Job Hunter Agent.lnk"))
  $lnk.TargetPath = $vpyw
  $lnk.Arguments = "-m dashboard.launcher"
  $lnk.WorkingDirectory = $Root
  $lnk.IconLocation = "$icon,0"
  $lnk.Description = "Job Hunter Agent"
  $lnk.Save()
}
Say "Added Job Hunter Agent to the Start menu and the desktop."

# 5 · jobhunter:// opens the app (the deck's live-demo icon uses it)
$key = "HKCU:\Software\Classes\jobhunter"
New-Item -Path "$key\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path $key -Name "(Default)" -Value "URL:Job Hunter Agent"
Set-ItemProperty -Path $key -Name "URL Protocol" -Value ""
New-Item -Path "$key\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "$key\DefaultIcon" -Name "(Default)" -Value "$icon,0"
Set-ItemProperty -Path "$key\shell\open\command" -Name "(Default)" -Value "`"$vpyw`" `"$Root\dashboard\launcher.py`""

Write-Host "`nDone. Opening Job Hunter Agent: its Setup page shows what's left (a model, your standing answers, your storybook).`n"
Start-Process -FilePath $vpyw -ArgumentList "-m", "dashboard.launcher" -WorkingDirectory $Root
