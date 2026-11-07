@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --upgrade pip pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name JigarzonLauncher jigarzon_launcher.py
echo Build output: dist\JigarzonLauncher.exe
pause
