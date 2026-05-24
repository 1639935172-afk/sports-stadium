param(
    [string]$EnvFile = (Join-Path $PSScriptRoot '..\.env'),
    [string]$BackupDir = (Join-Path $PSScriptRoot '..\backups')
)

$ErrorActionPreference = 'Stop'

function Read-DotEnv {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Env file not found: $Path"
    }

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith('#')) {
            continue
        }
        $parts = $trimmed.Split('=', 2)
        if ($parts.Count -ne 2) {
            continue
        }
        $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
    return $values
}

$envValues = Read-DotEnv -Path $EnvFile

$dbEngine = $envValues['DB_ENGINE']
if ($dbEngine -and $dbEngine.ToLowerInvariant() -ne 'mysql') {
    throw "Current DB_ENGINE is '$dbEngine'. This script only backs up MySQL databases."
}

$dbName = $envValues['DB_NAME']
if (-not $dbName) { $dbName = 'sports_stadium' }
$dbUser = $envValues['DB_USER']
if (-not $dbUser) { $dbUser = 'root' }
$dbPassword = $envValues['DB_PASSWORD']
$dbHost = $envValues['DB_HOST']
if (-not $dbHost) { $dbHost = '127.0.0.1' }
$dbPort = $envValues['DB_PORT']
if (-not $dbPort) { $dbPort = '3306' }

$mysqldump = Get-Command mysqldump -ErrorAction SilentlyContinue
if (-not $mysqldump) {
    throw "mysqldump was not found in PATH. Install MySQL client tools or add them to PATH."
}

$resolvedBackupDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BackupDir)
New-Item -ItemType Directory -Force -Path $resolvedBackupDir | Out-Null

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupFile = Join-Path $resolvedBackupDir "$dbName`_$timestamp.sql"

$previousMySqlPwd = $env:MYSQL_PWD
try {
    if ($null -ne $dbPassword) {
        $env:MYSQL_PWD = $dbPassword
    }

    $args = @(
        "--host=$dbHost",
        "--port=$dbPort",
        "--user=$dbUser",
        '--default-character-set=utf8mb4',
        '--single-transaction',
        '--no-tablespaces',
        '--routines',
        '--triggers',
        "--result-file=$backupFile",
        $dbName
    )

    & $mysqldump.Source @args
    if ($LASTEXITCODE -ne 0) {
        throw "mysqldump failed with exit code $LASTEXITCODE"
    }
}
finally {
    $env:MYSQL_PWD = $previousMySqlPwd
}

Write-Host "Backup created: $backupFile"
