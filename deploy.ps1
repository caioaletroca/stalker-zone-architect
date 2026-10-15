param(
    [string]$GammaPath = "C:\GAMMA",
    [string]$ModName = "STALKER Zone Architect - Base Building"
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$sourceGamedata = Join-Path $repoRoot "gamedata"

if (-not (Test-Path -LiteralPath $sourceGamedata)) {
    throw "Source gamedata folder not found at $sourceGamedata"
}

$targetModDir = Join-Path $GammaPath "mods\$ModName"
$targetGamedata = Join-Path $targetModDir "gamedata"

Write-Host "Deploying Base Building mod to MO2..." -ForegroundColor Cyan
Write-Host "Source: $sourceGamedata"
Write-Host "Target: $targetGamedata"

if (-not (Test-Path -LiteralPath $targetModDir)) {
    New-Item -ItemType Directory -Path $targetModDir | Out-Null
    Write-Host "Created mod directory: $targetModDir" -ForegroundColor Green
}

if (Test-Path -LiteralPath $targetGamedata) {
    $item = Get-Item -LiteralPath $targetGamedata
    if ($item.Attributes -match "ReparsePoint") {
        Write-Host "Removing existing symlink..."
        Remove-Item -LiteralPath $targetGamedata -Force
    } else {
        Write-Host "Backing up existing non-symlink gamedata directory..."
        Rename-Item -LiteralPath $targetGamedata -NewName "gamedata_backup_$((Get-Date).ToString('yyyyMMddHHmmss'))"
    }
}

New-Item -ItemType SymbolicLink -Path $targetGamedata -Target $sourceGamedata | Out-Null
Write-Host "Successfully created symbolic link from repo gamedata to MO2 mod folder." -ForegroundColor Green
Write-Host "Next step: Enable '$ModName' in MO2 (place below 'Hideout Furniture' and 'Even More Hideout Furnitures')." -ForegroundColor Yellow
