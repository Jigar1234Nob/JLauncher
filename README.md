# JLauncher for Windows

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">A Windows desktop launcher for Horizon and Minecraft: Java Edition.</p>

This branch contains the Windows application source and its GitHub Actions build workflow. The default branch contains only the project overview and logo.

## Features

- Guided Microsoft sign-in and first-run setup.
- Checks for JLauncher updates at startup.
- Checks Horizon's latest Nightly build and installs it when needed.
- Manages separate Minecraft instances.
- Browses Horizon-compatible mods and imports supported `.mrpack` or modpack `.zip` files.
- Opens the selected instance's Horizon mods folder.
- Optional developer diagnostics with application logs and Horizon CLI access.
- System-tray support: closing the window hides JLauncher in the notification area. The tray menu can reopen it, launch the selected instance, or fully exit.
- In-app reinstall and uninstall controls, with an option to preserve Horizon and Minecraft files.

## Requirements and compatibility

- Windows 10 or later.
- A Microsoft account that owns Minecraft: Java Edition is required to play.
- Horizon does not run arbitrary Java mod JARs as-is. Use the Horizon-compatible mod browser or supported modpack import.

## Build

The workflow is `.github/workflows/build-windows.yml`. It runs on pushes to this branch and can also be started manually.

The workflow uses Python 3.12, PyInstaller, and Inno Setup. It creates:

- `JLauncher.exe`
- `JLauncher-Setup-Windows.exe`

To publish a GitHub Release, push a version tag such as `v3.0.0`. The workflow attaches the Windows installer to that release.

## Install location and upgrade behaviour

The installer uses the per-user directory:

`%LOCALAPPDATA%\Programs\JLauncher`

It removes the previous `Jigarzon Launcher` program folder and Start Menu group during installation. The legacy application-data directory is intentionally retained so existing settings and Horizon/Minecraft files are not discarded.

## Other platforms

macOS and Linux source and workflows are maintained separately:

- [macOS branch](https://github.com/Jigar1234Nob/JLauncher/tree/macos-build)
- [Linux branch](https://github.com/Jigar1234Nob/JLauncher/tree/linux-build)

JLauncher is independent and is not affiliated with Mojang Studios or Microsoft.
