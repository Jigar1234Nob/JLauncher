# Jigarzon Launcher

A Prism-inspired Windows desktop interface for Horizon, the Rust implementation of Minecraft: Java Edition.

## What it does

- Browse Horizon's published releases and Nightly builds.
- Install the selected Horizon client build directly from the launcher.
- Download and prepare Minecraft resources through Horizon for a signed-in account that owns Java Edition.
- Sign in with Microsoft using Horizon's browser-based account flow.
- Choose which installed Horizon version to launch.
- View and create separate Horizon instances.
- Follow a first-run tutorial inside the launcher.
- Show Horizon command output and setup status.

## Quick start

1. Install Horizon using its official instructions: https://github.com/horizon-rust/horizon
2. Open Jigarzon Launcher.
3. Go to **Settings** and select the `horizon-launcher.exe` from your Horizon installation.
4. Return to **Home**, choose **Browse releases**, select a build, and press **Install selected**.
5. Press **Microsoft account sign-in** and finish the sign-in in your browser. The account must own Minecraft: Java Edition.
6. Choose the build you installed and press **Download & Prepare Game Files**. This asks Horizon to prepare the selected version's game resources from your existing Minecraft installation or download the required Mojang files.
7. Press **Play Minecraft**.

The built-in **Tutorial** page walks through the same process.

## Important download details

Jigarzon downloads Horizon builds by calling Horizon's documented `horizon-launcher install <TAG>` command. Minecraft game resources are prepared with `horizon-launcher prepare --download --version <TAG>`. Horizon handles the actual downloads, checks and account ownership requirements.

Jigarzon does not bundle Minecraft's copyrighted game files, Microsoft account tokens, or a copy of Horizon. You need a Microsoft account that owns Minecraft: Java Edition. Sign-in is handled by Horizon.

## Build on Windows

1. Install Python 3.12.
2. Download this repository.
3. Run `build.bat`.
4. Find the executable at `dist/JigarzonLauncher.exe`.

GitHub Actions also builds the Windows executable on every push to `main`. Open the repository's Actions tab and download the `Jigarzon-Launcher-Windows` artifact. Pushing a tag beginning with `v` attaches the executable to a GitHub Release.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- Horizon installed separately.
- A Microsoft account that owns Minecraft: Java Edition for online play and Mojang downloads.

## Disclaimer

Jigarzon Launcher is an independent project and is not affiliated with Mojang Studios or Microsoft. Minecraft is a trademark of Mojang Studios and Microsoft. Horizon is a separate open-source project.
