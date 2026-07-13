$ErrorActionPreference = "Stop"

$paths = @(
    ".\setup_databento_credentials.ps1",
    ".\exp005_databento_cost.py",
    ".\estimate_exp005_databento_cost.py",
    ".\tests\test_exp005_databento_cost.py"
)

$removed = 0

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "Removed obsolete paid-source file: $path"
        $removed += 1
    }
}

if ($removed -eq 0) {
    Write-Host "No obsolete Databento estimator files were present."
}

Write-Host "EXP-005 remains on the zero-cost Lucid/Rithmic path."
