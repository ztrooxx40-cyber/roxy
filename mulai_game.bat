@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python tidak ditemukan. Mode satu komputer tetap bisa dimainkan dengan membuka ular_2_pemain.html di Chrome.
    echo Untuk mode kode ruang, instal Python terlebih dahulu.
    pause
    exit /b 1
)

py -c "import aiohttp" >nul 2>nul
if errorlevel 1 (
    echo Menyiapkan kebutuhan game online...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Gagal menyiapkan game online. Periksa koneksi internet, lalu coba lagi.
        pause
        exit /b 1
    )
)

set "GAME_PORT=8080"
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:%GAME_PORT%/health' -TimeoutSec 2; if ($health.service -eq 'snake-two-player' -and $health.websocket -eq '/ws') { exit 0 } } catch {}; exit 1"
if errorlevel 1 (
    set "GAME_PORT="
    for /f "delims=" %%P in ('powershell -NoProfile -Command "$used = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalPort -Unique); $port = 8080; while ($port -le 8090 -and $used -contains $port) { $port++ }; if ($port -le 8090) { Write-Output $port }"') do set "GAME_PORT=%%P"
    if not defined GAME_PORT (
        echo Tidak ada port game yang tersedia dari 8080 sampai 8090.
        echo Tutup aplikasi server lain, lalu jalankan file ini lagi.
        pause
        exit /b 1
    )

    echo Menyalakan server game...
    start "Server Game Ular" /min cmd /k "cd /d ""%~dp0"" && set PORT=!GAME_PORT! && py server.py"

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddSeconds(20); do { try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:!GAME_PORT!/health' -TimeoutSec 2; if ($health.service -eq 'snake-two-player' -and $health.websocket -eq '/ws') { exit 0 } } catch {}; Start-Sleep -Milliseconds 500 } while ((Get-Date) -lt $deadline); exit 1"
    if errorlevel 1 (
        echo Server belum siap. Periksa jendela "Server Game Ular".
        echo Pastikan Python dan aiohttp tersedia, lalu coba lagi.
        pause
        exit /b 1
    )
) else (
    echo Server game sudah berjalan.
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0izinkan_akses_hp.ps1" -Port !GAME_PORT!
if errorlevel 1 (
    echo.
    echo Akses HP belum diizinkan oleh Windows Firewall.
    echo Jalankan ulang file ini dan setujui permintaan administrator agar HP dapat tersambung.
)

set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME (
    start "" "%CHROME%" "http://127.0.0.1:%GAME_PORT%/"
) else (
    start "" "http://127.0.0.1:%GAME_PORT%/"
)

echo Game siap. Pilih "Main di komputer ini" atau "Main online".
echo Jangan tutup jendela "Server Game Ular" selama bermain online.
for /f "delims=" %%I in ('powershell -NoProfile -Command "[System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) | Where-Object AddressFamily -eq InterNetwork | Select-Object -First 1 -ExpandProperty IPAddressToString"') do set "LAN_IP=%%I"
if defined LAN_IP (
    echo.
    echo Untuk bermain di HP pada Wi-Fi yang sama, buka: http://%LAN_IP%:%GAME_PORT%
    echo Pastikan komputer dan HP tersambung ke Wi-Fi yang sama.
)
