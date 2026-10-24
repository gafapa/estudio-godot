# Report Godot processes that explicitly reference this checkout.
$projectPath = $env:STUDIO_CHECKOUT_PATH.TrimEnd('\').Replace('\', '/')
$pattern = '(?i)' + [regex]::Escape($projectPath) + '([/"\s]|$)'
Get-CimInstance Win32_Process -Filter "Name like 'Godot%'" | Where-Object {
    $_.CommandLine -and $_.CommandLine.Replace('\', '/') -match $pattern
} | ForEach-Object { $_.ProcessId }
