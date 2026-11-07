# Jigarzon Launcher

A Windows desktop launcher for Horizon, the Rust implementation of Minecraft: Java Edition.

## Features
- View installed Horizon builds.
- Install the latest Horizon build.
- Prepare Minecraft resources.
- Start Microsoft account sign-in through Horizon.
- Launch a selected Horizon build.
- Display the current session as: Playing Minecraft (version) using Jigarzon Launcher.

## Requirements
- Windows 10 or Windows 11, 64-bit.
- Horizon installed separately.
- A Microsoft account that owns Minecraft: Java Edition.
- Your own legitimate Minecraft game files.

## Build on Windows
1. Install Python 3.12.
2. Download this repository.
3. Run build.bat.
4. Find the executable at dist/JigarzonLauncher.exe.

## Use
1. Install Horizon from its official distribution.
2. Open Jigarzon Launcher and browse to horizon-launcher.exe.
3. Refresh installed builds or install the latest build.
4. Sign in with your Microsoft account.
5. Select an installed build and press Play Minecraft.

Jigarzon Launcher uses Horizon's documented command-line interface for version management, preparation, sign-in and game launch.

## GitHub Actions
Every push to main builds a Windows executable. Open the repository's Actions tab and download the Jigarzon-Launcher-Windows artifact. Pushing a tag beginning with v also attaches the executable to a GitHub Release.

## Disclaimer
Jigarzon Launcher is an independent project and is not affiliated with Mojang Studios or Microsoft. Minecraft is a trademark of Mojang and Microsoft. Horizon is a separate open-source project.
