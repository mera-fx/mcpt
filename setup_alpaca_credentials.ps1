[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "ALPACA MARKET-DATA CREDENTIAL SETUP"
Write-Host "==================================="

$keyId = Read-Host "Enter APCA API Key ID"
$secureSecret = Read-Host `
    "Enter APCA API Secret Key" `
    -AsSecureString

if ([string]::IsNullOrWhiteSpace($keyId)) {
    throw "API key ID cannot be empty."
}

$secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
    $secureSecret
)

try {
    $plainSecret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR(
        $secretPointer
    )

    if ([string]::IsNullOrWhiteSpace($plainSecret)) {
        throw "API secret cannot be empty."
    }

    [Environment]::SetEnvironmentVariable(
        "APCA_API_KEY_ID",
        $keyId,
        "User"
    )

    [Environment]::SetEnvironmentVariable(
        "APCA_API_SECRET_KEY",
        $plainSecret,
        "User"
    )

    $env:APCA_API_KEY_ID = $keyId
    $env:APCA_API_SECRET_KEY = $plainSecret
}
finally {
    if ($secretPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR(
            $secretPointer
        )
    }
}

Write-Host ""
Write-Host "Credentials saved to your Windows user environment."
Write-Host "They were not written into the project or Git."
Write-Host ""
Write-Host "The current PowerShell window can use them immediately."
Write-Host "Future terminals will load them after reopening PowerShell."
