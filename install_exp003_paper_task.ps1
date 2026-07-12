[CmdletBinding()]
param(
    [string]$TaskName = "MCPT EXP-003 Paper Update",
    [ValidateRange(0, 59)]
    [int]$MinuteAfterHour = 7
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunnerPath = Join-Path $ProjectRoot "run_exp003_paper_task.ps1"
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$UpdateScript = Join-Path $ProjectRoot "run_exp003_paper_update.py"

if (-not (Test-Path $RunnerPath)) {
    throw "Scheduled runner not found: $RunnerPath"
}

if (-not (Test-Path $PythonPath)) {
    throw "Virtual-environment Python not found: $PythonPath"
}

if (-not (Test-Path $UpdateScript)) {
    throw "Paper update script not found: $UpdateScript"
}

$currentUser = (
    [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
)

$currentShell = (
    Get-Process -Id $PID
).Path

$now = Get-Date
$firstRun = (
    $now.Date
    .AddHours($now.Hour)
    .AddMinutes($MinuteAfterHour)
)

if ($firstRun -le $now) {
    $firstRun = $firstRun.AddHours(1)
}

$actionArguments = (
    "-NoProfile -NonInteractive " +
    "-ExecutionPolicy Bypass " +
    "-File `"$RunnerPath`""
)

$action = New-ScheduledTaskAction `
    -Execute $currentShell `
    -Argument $actionArguments `
    -WorkingDirectory $ProjectRoot

$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $firstRun `
    -RepetitionInterval (
        New-TimeSpan -Hours 1
    ) `
    -RepetitionDuration (
        New-TimeSpan -Days 3650
    )

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (
        New-TimeSpan -Minutes 20
    ) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Limited

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description (
        "Runs the EXP-003 paper-only simulator once per hour " +
        "after the hourly candle has closed. No live orders."
    )

Register-ScheduledTask `
    -TaskName $TaskName `
    -InputObject $task `
    -Force | Out-Null

$registeredTask = Get-ScheduledTask `
    -TaskName $TaskName

$taskInfo = Get-ScheduledTaskInfo `
    -TaskName $TaskName

Write-Host ""
Write-Host "EXP-003 PAPER TASK INSTALLED"
Write-Host "============================"
Write-Host "Task:       $TaskName"
Write-Host "User:       $currentUser"
Write-Host "State:      $($registeredTask.State)"
Write-Host "Next run:   $($taskInfo.NextRunTime)"
Write-Host "Frequency:  Once per hour"
Write-Host "Run minute: $MinuteAfterHour minutes after the hour"
Write-Host "Mode:       PAPER ONLY"
Write-Host "Live orders: DISABLED"
Write-Host ""
Write-Host (
    "The task runs only while this Windows user is signed in. " +
    "The computer must be awake or able to wake."
)
Write-Host ""
Write-Host (
    "Check status with:`r`n" +
    ".\show_exp003_paper_task.ps1"
)
