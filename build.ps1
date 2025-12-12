$ErrorActionPreference = "Stop"

# neuestes Signtool (x64) finden
$signtool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter signtool.exe |
  Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
  Sort-Object FullName -Descending |
  Select-Object -First 1 -ExpandProperty FullName

$pfx = "C:\Users\Nico\code-signing.pfx"
$exe = ".\dist\main.exe"

$pwd = $env:CODESIGN_PFX_PASSWORD
if (-not $pwd) { throw "Env-Var CODESIGN_PFX_PASSWORD fehlt" }

& $signtool sign /f $pfx /p $pwd /fd SHA256 /tr http://timestamp.sectigo.com /td SHA256 $exe
& $signtool verify /pa $exe
