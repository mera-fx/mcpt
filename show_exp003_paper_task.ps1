[CmdletBinding()]
param(
    [string]$TaskName = "MCPT EXP-003 Paper Update",
    [int]$LogLines = 40
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $ProjectRoot "paper_logs\EXP-003_hourly_update.log"

$task = Get-ScheduledTask `
    -TaskName $TaskName `
    -ErrorAction SilentlyContinue

if ($null -eq $task) {
    Write-Host ""
    Write-Host "EXP-003 paper task is not installed."
    Write-Host (
        "Install it with:`r`n" +
        ".\install_exp003_paper_task.ps1"
    )

    exit 1
}

$taskInfo = Get-ScheduledTaskInfo `
    -TaskName $TaskName

Write-Host ""
Write-Host "EXP-003 PAPER TASK STATUS"
Write-Host "========================="
Write-Host "Task:        $TaskName"
Write-Host "State:       $($task.State)"
Write-Host "Last run:    $($taskInfo.LastRunTime)"
Write-Host "Last result: $($taskInfo.LastTaskResult)"
Write-Host "Next run:    $($taskInfo.NextRunTime)"
Write-Host "Missed runs: $($taskInfo.NumberOfMissedRuns)"
Write-Host "Mode:        PAPER ONLY"
Write-Host ""

if (Test-Path $LogFile) {
    Write-Host "Recent task log"
    Write-Host "---------------"

    Get-Content `
        -Path $LogFile `
        -Tail $LogLines
}
else {
    Write-Host (
        "No task log exists yet. It will be created " +
        "after the first scheduled run."
    )
}
