@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --upgrade pip pyinstaller customtkinter pypresence pillow pystray
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name JLauncher --collect-all customtkinter --collect-all pypresence --collect-all pystray jigarzon_launcher.py
echo.
echo Build output: dist\JLauncher.exe
pause
