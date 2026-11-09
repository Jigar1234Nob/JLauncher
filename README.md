# JLauncher for macOS

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">A desktop launcher for Horizon and Minecraft: Java Edition.</p>

This branch contains the macOS application source and packaging workflow. Windows and Linux builds remain on their own branches.

## Build targets

The workflow `.github/workflows/build-macos.yml` builds on separate Apple Silicon and Intel runners. It packages the application as:

- A macOS `.dmg` installer.
- A portable `.zip` archive.

Builds are uploaded as GitHub Actions artifacts. The workflow currently does not publish macOS assets to GitHub Releases automatically.

## Features

- Guided first-run setup and Microsoft sign-in.
- Horizon installation and update checks, subject to upstream macOS package availability.
- Minecraft instance management.
- Horizon-compatible mod browsing and supported modpack importing.
- System-tray/menu-bar integration where supported.
- Launcher update checks against published JLauncher releases.

## Important macOS notes

- The application is currently unsigned and not notarized. macOS may require approval in Privacy & Security before opening it.
- Horizon must publish a compatible macOS CLI archive for Horizon installation and gameplay to work on the Mac.
- A Microsoft account that owns Minecraft: Java Edition is required to play.

## Build locally

Use Python 3.12 and install the dependencies listed in the workflow. The GitHub Actions workflow is the supported reproducible build path.

The Windows source is on the [`build` branch](https://github.com/Jigar1234Nob/JLauncher/tree/build), and Linux source is on the [`linux-build` branch](https://github.com/Jigar1234Nob/JLauncher/tree/linux-build).

JLauncher is independent and is not affiliated with Mojang Studios or Microsoft.
