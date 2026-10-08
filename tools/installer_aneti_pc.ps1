# Installe sur le PC d'Ahmed la tâche planifiée « Concours-ANETI » : chaque jour à 12h30, tools\aneti_pc.py télécharge
# les pages de l'ANETI (qui refuse les connexions venant de l'étranger, donc de GitHub) et les envoie sur GitHub.
#
# Prérequis (déjà présents pour le relevé Otrity) : Python, Git, connexion GitHub (gh auth login).
# Puis, dans le dossier du site des concours (gh repo clone Ah6259/alerte-concours-tunisie si besoin) :
#   powershell -ExecutionPolicy Bypass -File tools\installer_aneti_pc.ps1
#
# Sans ce PC, le site continue : seules les annonces de l'ANETI manquent.

$ErrorActionPreference = "Stop"
$racine = Split-Path -Parent $PSScriptRoot
$script = Join-Path $racine "tools\aneti_pc.py"

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "Python introuvable : installez-le d'abord (python.org ou Microsoft Store)." }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git introuvable : installez-le d'abord (git-scm.com)." }

$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$script`"" -WorkingDirectory $racine
$trigger  = New-ScheduledTaskTrigger -Daily -At 12:30
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
              -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "Concours-ANETI" -Force `
  -Description "Releve quotidien des pages de l'ANETI pour les sites Alerte Concours et Documents (tools\aneti_pc.py)" `
  -Action $action -Trigger $trigger -Settings $settings | Out-Null

Write-Host "Tâche « Concours-ANETI » installée (chaque jour à 12h30). Premier relevé maintenant…"
& $py $script
