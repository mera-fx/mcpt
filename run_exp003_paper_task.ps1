[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$UpdateScript = Join-Path $ProjectRoot "run_exp003_paper_update.py"
$LogDirectory = Join-Path $ProjectRoot "paper_logs"
$LogFile = Join-Path $LogDirectory "EXP-003_hourly_update.log"

New-Item `
    -ItemType Directory `
    -Path $LogDirectory `
    -Force | Out-Null

$mutexName = "Local\MCPT_EXP003_PAPER_UPDATE"
$mutex = [System.Threading.Mutex]::new($false, $mutexName)
$hasLock = $false

try {
    $hasLock = $mutex.WaitOne([TimeSpan]::Zero)

    if (-not $hasLock) {
        Add-Content `
            -Path $LogFile `
            -Value (
                "$(Get-Date -Format o) | SKIP | " +
                "Another paper update is still running."
            )

        exit 0
    }

    Add-Content `
        -Path $LogFile `
        -Value (
            "`r`n========================================`r`n" +
            "$(Get-Date -Format o) | START | " +
            "EXP-003 paper-only update"
        )

    if (-not (Test-Path $PythonPath)) {
        throw "Virtual-environment Python not found: $PythonPath"
    }

    if (-not (Test-Path $UpdateScript)) {
        throw "Paper update script not found: $UpdateScript"
    }

    Set-Location $ProjectRoot

    & $PythonPath $UpdateScript 2>&1 |
        Tee-Object `
            -FilePath $LogFile `
            -Append

    $exitCode = $LASTEXITCODE

    Add-Content `
        -Path $LogFile `
        -Value (
            "$(Get-Date -Format o) | END | " +
            "Exit code $exitCode"
        )

    exit $exitCode
}
catch {
    Add-Content `
        -Path $LogFile `
        -Value (
            "$(Get-Date -Format o) | ERROR | " +
            $_.Exception.Message
        )

    throw
}
finally {
    if ($hasLock) {
        $mutex.ReleaseMutex()
    }

    $mutex.Dispose()
}
