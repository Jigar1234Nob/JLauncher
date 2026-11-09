<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<h1 align="center">JLauncher</h1>

<p align="center">
  A Windows desktop launcher for Horizon, the Rust-based Minecraft: Java Edition client.
</p>

JLauncher is a Windows desktop launcher for Horizon, the Rust-based Minecraft: Java Edition client.

## Features

- Guided Microsoft sign-in and first-run setup.
- Automatically checks for JLauncher updates at startup and installs newer published releases.
- Checks Horizon's latest Nightly build on every startup and installs it when needed.
- Reads the current Minecraft Java Edition version from Horizon's official project information (currently 26.3).
- Home dashboard with the JLauncher v2.00 release announcement and the current Horizon build label.
- Prism-inspired dark interface with the JL purple/cyan identity.
- Windows application icon, taskbar icon and Inno Setup installer branding.
- System-tray support: closing the window keeps JLauncher running in the notification area; the tray menu can reopen the launcher, launch the selected instance, or fully exit.
- Per-user Windows installer with Start Menu and optional desktop shortcuts.
- Instance manager to create, select, rename, reinstall and delete instances.
- Mod browser for Horizon-compatible content.
- Open the selected instance's Horizon mods folder.
- Optional Stats for Nerds developer gallery with live application logs and Horizon CLI access.
- In-app reinstall and uninstall controls, including a choice to preserve Horizon and Minecraft files.
- Drag and drop Horizon `.mrpack` or supported modpack `.zip` files to import them.

## Mods and compatibility

Horizon does not run arbitrary Java mod JARs as-is. Its mod browser checks and ports supported mod content. Dropping a raw `.jar` into JLauncher will therefore not activate it; use Horizon's mod browser for compatible mods. Modpack files are imported as their own instance.

A Microsoft account that owns Minecraft: Java Edition is required. Minecraft assets are downloaded from Mojang through Horizon and are not bundled with JLauncher.

## Building on Windows

The GitHub Actions workflow runs from `build` and builds both `JLauncherLauncher.exe` and `JLauncher-Setup-Windows.exe`. It uses PyInstaller and Inno Setup. Push a version tag such as `v2.0.0` to publish the installer as a GitHub Release. Future releases are checked automatically when JLauncher starts.

JLauncher is an independent project and is not affiliated with Mojang Studios or Microsoft.
