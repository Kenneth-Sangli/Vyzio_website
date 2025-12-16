# Script PowerShell de sauvegarde automatique SQLite
# Placez ce script dans le dossier scripts/ et exécutez-le via le Planificateur de tâches Windows

$backupDir = "../backups"
$dbFile = "../db.sqlite3"
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir/backup_$date.sql"

# Créer le dossier de backup s'il n'existe pas
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Sauvegarde de la base SQLite
if (Test-Path $dbFile) {
    & sqlite3 $dbFile ".dump" | Out-File -Encoding UTF8 $backupFile
    Write-Host "Backup créé : $backupFile"
} else {
    Write-Host "Base de données introuvable : $dbFile"
}

# Rotation : ne garder que les 30 derniers backups
$backups = Get-ChildItem -Path $backupDir -Filter "backup_*.sql" | Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 30) {
    $toDelete = $backups | Select-Object -Skip 30
    foreach ($file in $toDelete) {
        Remove-Item $file.FullName
        Write-Host "Backup supprimé : $($file.FullName)"
    }
}
