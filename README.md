# JLauncher

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">
  <strong>A cleaner way to manage Horizon and Minecraft: Java Edition on Windows.</strong>
</p>

JLauncher is a Windows desktop companion for Horizon, the Rust-based Minecraft: Java Edition client. It combines account sign-in, Horizon installation, game instances, version selection, and compatible mod management in one application.

## Features

- **Guided first-run tutorial:** Walks you through the initial setup and account connection.
- **Microsoft account sign-in:** Connect the account that owns Minecraft: Java Edition.
- **Horizon installation:** Downloads and installs the official compatible Horizon launcher package.
- **Automatic update checks:** Checks for JLauncher updates when the app opens and checks for newer Horizon releases.
- **Instance management:** Create and manage separate Minecraft setups, then select which instance to launch.
- **Game version selection:** Browse available game versions and manage the version used by an instance.
- **Compatible mod browser:** Find and install mods supported by Horizon.
- **Modpack importing:** Import supported modpack archives, including compatible `.mrpack` files.
- **Folder access:** Open the selected instance's folders to manage its files.
- **System tray:** Closing the window hides JLauncher in the notification area. The tray menu can reopen the app, launch the selected instance, or fully exit.
- **Diagnostics:** View launcher activity and logs to help troubleshoot issues.
- **Appearance settings:** Use the launcher's dark interface and available application settings.

## Installation and upgrades

The Windows installer installs JLauncher for the current Windows user. When upgrading from the older Jigarzon Launcher installation, the installer replaces the old program folder with the JLauncher folder while retaining the legacy application-data directory so existing settings and Horizon/Minecraft files are not needlessly deleted.

## Requirements

- Windows 10 or later.
- A Microsoft account that owns Minecraft: Java Edition to play.
- An internet connection for sign-in, release checks, and downloads.

## Mod compatibility

Horizon does not automatically support every Minecraft Java mod. Use the compatible mod browser and supported modpack import features. Installing arbitrary Java mod JAR files may not work.

## Troubleshooting

If Horizon does not start, check that it is installed and that the selected instance is configured correctly. When asking for help, include your JLauncher version and relevant logs.

JLauncher is an independent community project and is not affiliated with Mojang Studios or Microsoft.
