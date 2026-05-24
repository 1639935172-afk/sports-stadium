param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,

    [string]$EnvFile = (Join-Path $PSScriptRoot '..\.env'),
    [switch]$Force
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

$resolvedBackupFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BackupFile)
if (-not (Test-Path -LiteralPath $resolvedBackupFile)) {
    throw "Backup file not found: $resolvedBackupFile"
}

$envValues = Read-DotEnv -Path $EnvFile

$dbEngine = $envValues['DB_ENGINE']
if ($dbEngine -and $dbEngine.ToLowerInvariant() -ne 'mysql') {
    throw "Current DB_ENGINE is '$dbEngine'. This script only restores MySQL databases."
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

$mysql = Get-Command mysql -ErrorAction SilentlyContinue
if (-not $mysql) {
    throw "mysql was not found in PATH. Install MySQL client tools or add them to PATH."
}

if (-not $Force) {
    Write-Host "This will restore '$resolvedBackupFile' into database '$dbName'."
    Write-Host "Existing rows may be overwritten or deleted depending on the backup contents."
    $answer = Read-Host "Type RESTORE to continue"
    if ($answer -ne 'RESTORE') {
        throw 'Restore cancelled.'
    }
}

$mysqlSourcePath = $resolvedBackupFile.Replace('\', '/')
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
        $dbName,
        "--execute=SOURCE $mysqlSourcePath"
    )

    & $mysql.Source @args
    if ($LASTEXITCODE -ne 0) {
        throw "mysql restore failed with exit code $LASTEXITCODE"
    }
}
finally {
    $env:MYSQL_PWD = $previousMySqlPwd
}

Write-Host "Restore completed from: $resolvedBackupFile"
