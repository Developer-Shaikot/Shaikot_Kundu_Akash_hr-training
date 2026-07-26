$confPath = "C:\Program Files\Odoo 17.0.20260717\server\odoo.conf"
$content = Get-Content $confPath -Raw

# Only patch if not already patched
if ($content -notmatch 'xampp\\webdav\\hsg\\hr') {
    $content = $content -replace 'addons_path = c:\\program files\\odoo 17.0.20260717\\server\\odoo\\addons', 'addons_path = c:\program files\odoo 17.0.20260717\server\odoo\addons,c:\program files\odoo 17.0.20260717\server\addons,c:\xampp\webdav\hsg\hr'
    Set-Content -Path $confPath -Value $content
    Write-Host "Config updated."
} else {
    Write-Host "Config already contains custom path."
}

# Restart the Odoo service
Restart-Service -Name "odoo-server-17.0" -Force
Write-Host "Odoo service restarted."
