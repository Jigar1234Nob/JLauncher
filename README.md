# JLauncher

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">
  <strong>A cleaner way to manage Horizon and Minecraft: Java Edition on Linux.</strong>
</p>

JLauncher is a desktop companion for Horizon, the Rust-based Minecraft: Java Edition client. It provides a graphical place to manage account sign-in, game instances, versions, and supported mods.

## Features

- **Guided first-run setup:** Helps you complete initial configuration and account connection.
- **Microsoft account sign-in:** Connect the account that owns Minecraft: Java Edition.
- **Horizon setup:** Helps install Horizon when an official compatible Linux package is available for your architecture.
- **Update checks:** Checks for newer JLauncher releases when the application starts.
- **Instance management:** Keep separate Minecraft configurations and select the instance you want to launch.
- **Game version selection:** Choose from the versions made available by Horizon.
- **Compatible mod browser:** Browse and install mods supported by Horizon.
- **Modpack importing:** Import supported modpack archives, including compatible `.mrpack` files.
- **Troubleshooting information:** Use available logs and diagnostics to investigate problems.

## System requirements

- A graphical Linux desktop with X11 or XWayland support.
- A Microsoft account that owns Minecraft: Java Edition to play.
- An internet connection for sign-in, release checks, and downloads.
- Compatible Horizon binaries for your Linux architecture.

## Architecture compatibility

JLauncher can be packaged for both x86_64 and ARM64 Linux systems. However, Horizon's official Linux launcher is currently available for x86_64 only. On ARM64, JLauncher itself may run, but Horizon installation and gameplay require an official compatible ARM64 release from Horizon.

## Mod compatibility

Horizon does not guarantee support for arbitrary Java mod JAR files. Use the compatible mod browser and supported modpack import features.

## Getting started

Launch JLauncher from your desktop environment, follow the setup tutorial, connect your Microsoft account, and complete Horizon setup if a compatible package is available for your system.

JLauncher is an independent community project and is not affiliated with Mojang Studios or Microsoft.
