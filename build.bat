@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --upgrade pip pyinstaller customtkinter pypresence
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name JigarzonLauncher --collect-all customtkinter --collect-all pypresence jigarzon_launcher.py
echo.
echo Build output: dist\JigarzonLauncher.exe
pause
