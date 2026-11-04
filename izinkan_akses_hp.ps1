param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 65535)]
    [int]$Port
)

$ErrorActionPreference = 'Stop'
$ruleName = "Game Ular 2 Pemain TCP $Port"
$rule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($rule) {
    $portFilter = $rule | Get-NetFirewallPortFilter
    $addressFilter = $rule | Get-NetFirewallAddressFilter
    if (
        $rule.Enabled -eq 'True' -and
        $rule.Direction -eq 'Inbound' -and
        $rule.Action -eq 'Allow' -and
        $portFilter.Protocol -eq 'TCP' -and
        $portFilter.LocalPort -contains "$Port" -and
        $addressFilter.RemoteAddress -contains 'LocalSubnet'
    ) {
        exit 0
    }
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdministrator) {
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Port ' + $Port
    try {
        $process = Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    }
    catch {
        Write-Error 'Permintaan administrator dibatalkan atau gagal. Akses dari HP belum dibuka.'
        exit 1
    }

    exit $process.ExitCode
}

if ($rule) {
    $rule | Remove-NetFirewallRule
}

New-NetFirewallRule `
    -DisplayName $ruleName `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort $Port `
    -RemoteAddress LocalSubnet `
    -Profile Any `
    -Description 'Game Ular 2 Pemain: hanya perangkat pada jaringan lokal.' | Out-Null
