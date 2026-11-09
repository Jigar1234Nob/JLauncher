# JLauncher for Linux

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">A Linux desktop launcher for Horizon and Minecraft: Java Edition.</p>

This branch contains the Linux application source and packaging workflow. Windows and macOS builds are maintained separately.

## Build targets

The workflow `.github/workflows/build-linux.yml` builds native packages for:

- x86_64 / amd64
- ARM64 / aarch64

For each architecture it produces a Debian `.deb` package and a portable `.tar.gz` archive. Builds are uploaded as GitHub Actions artifacts. The workflow currently does not publish Linux packages to GitHub Releases automatically.

## Requirements

- A graphical Linux desktop with X11 or XWayland.
- A Microsoft account that owns Minecraft: Java Edition is required to play.
- Horizon-compatible Linux binaries for the target architecture.

## Important ARM64 limitation

Horizon currently publishes its official Linux launcher for x86_64 only. The JLauncher ARM64 application and packages can run natively, but Horizon installation and gameplay remain unavailable on Linux ARM64 until Horizon publishes an ARM64 Linux build. JLauncher should report this limitation rather than trying to execute an incompatible x86_64 binary.

## Features

- Guided setup and Microsoft sign-in.
- Horizon installation and update checks, subject to upstream platform support.
- Minecraft instance management.
- Horizon-compatible mod browsing and supported modpack importing.
- System-tray integration on supported graphical desktops.
- Launcher update checks against published JLauncher releases.

## Build locally

Use Python 3.12 and install the system and Python dependencies listed in `.github/workflows/build-linux.yml`. GitHub Actions provides the reproducible x86_64 and ARM64 build environments.

The Windows source is on the [`build` branch](https://github.com/Jigar1234Nob/JLauncher/tree/build), and macOS source is on the [`macos-build` branch](https://github.com/Jigar1234Nob/JLauncher/tree/macos-build).

JLauncher is independent and is not affiliated with Mojang Studios or Microsoft.
