param(
    [Parameter(Mandatory=$true)]
    [string]$PythonExe,

    [string]$TorchIndexUrl = "https://download.pytorch.org/whl/cu128"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VendorDir = Join-Path $RepoRoot "vendor\py310"
$Requirements = Join-Path $RepoRoot "requirements-nuke15.txt"
$UserNukeDir = Join-Path $HOME ".nuke"
$UserInitPy = Join-Path $UserNukeDir "init.py"

New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null

Write-Host "Installing MatAnyone2 Nuke dependencies into:"
Write-Host "  $VendorDir"

$PythonParts = $PythonExe -split " "
$PythonCommand = $PythonParts[0]
$PythonArgs = @()
if ($PythonParts.Count -gt 1) {
    $PythonArgs = $PythonParts[1..($PythonParts.Count - 1)]
}

& $PythonCommand @PythonArgs -m pip install --upgrade pip
& $PythonCommand @PythonArgs -m pip install --target $VendorDir --upgrade torch torchvision --index-url $TorchIndexUrl
& $PythonCommand @PythonArgs -m pip install --target $VendorDir --upgrade -r $Requirements
& $PythonCommand @PythonArgs -m pip install --target $VendorDir --upgrade --no-deps "matanyone2@git+https://github.com/pq-yang/MatAnyone2.git"

New-Item -ItemType Directory -Force -Path $UserNukeDir | Out-Null
$PluginAddPath = "nuke.pluginAddPath(r'$RepoRoot')"
if (Test-Path $UserInitPy) {
    $ExistingInit = Get-Content $UserInitPy -Raw
    if ($ExistingInit -notmatch [regex]::Escape($PluginAddPath)) {
        Add-Content -Path $UserInitPy -Value "`n# MatAnyone2 for Nuke`nimport nuke`n$PluginAddPath`n"
    }
} else {
    Set-Content -Path $UserInitPy -Value "# MatAnyone2 for Nuke`nimport nuke`n$PluginAddPath`n"
}

Write-Host ""
Write-Host "Done. Restart Nuke and create the node from:"
Write-Host "  Nodes > Keyer > MatAnyone2 Soft Matte"
