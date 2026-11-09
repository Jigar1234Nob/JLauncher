# JLauncher

<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="JLauncher logo" width="160">
</p>

<p align="center">
  A desktop launcher for Horizon and Minecraft: Java Edition.
</p>

JLauncher is an independent desktop launcher project for managing Horizon installations, Minecraft Java Edition instances, compatible mods, and launcher updates.

## Platform builds

The project keeps each operating-system build on its own branch:

| Platform | Source branch | Build workflow |
|---|---|---|
| Windows | [`build`](https://github.com/Jigar1234Nob/JLauncher/tree/build) | [Windows workflow](https://github.com/Jigar1234Nob/JLauncher/actions/workflows/build-windows.yml) |
| macOS | [`macos-build`](https://github.com/Jigar1234Nob/JLauncher/tree/macos-build) | [macOS workflow](https://github.com/Jigar1234Nob/JLauncher/actions/workflows/build-macos.yml) |
| Linux | [`linux-build`](https://github.com/Jigar1234Nob/JLauncher/tree/linux-build) | [Linux workflow](https://github.com/Jigar1234Nob/JLauncher/actions/workflows/build-linux.yml) |

Download published installers and packages from [GitHub Releases](https://github.com/Jigar1234Nob/JLauncher/releases).

## Features

- Guided first-run setup and Microsoft account sign-in.
- Horizon installation and update checks.
- Separate Minecraft instances and instance management.
- Browser for Horizon-compatible mods and modpack importing.
- Launcher update checks.
- Platform-specific packaging and application branding.

## Important compatibility notes

- A Microsoft account that owns Minecraft: Java Edition is required to play.
- Horizon does not load arbitrary Java mod JAR files as-is. Use its compatible mod browser and supported modpack import.
- Horizon's official Linux launcher is currently x86_64 only. The JLauncher Linux ARM64 package can run, but Horizon installation and gameplay on ARM64 remain unavailable until Horizon publishes an ARM64 Linux build.
- The macOS application is currently unsigned and not notarized. macOS may require approval in Privacy & Security. Horizon must also provide a compatible macOS CLI package.

## Repository layout

- `main`: project overview and logo.
- `build`: Windows source and installer workflow.
- `macos-build`: macOS source and packaging workflow.
- `linux-build`: Linux source and packaging workflow.

JLauncher is an independent project and is not affiliated with Mojang Studios or Microsoft.
