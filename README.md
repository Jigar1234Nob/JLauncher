<p align="center">
  <img src="assets/jigarzon-logo.svg" alt="Jigarzon Launcher logo" width="160">
</p>

<h1 align="center">Jigarzon Launcher</h1>

<p align="center">
  A desktop launcher for Horizon, the Rust-based Minecraft: Java Edition client.
</p>

Jigarzon Launcher is a desktop launcher for Horizon, the Rust-based Minecraft: Java Edition client.

## Features

- Guided Microsoft sign-in and first-run setup.
- Automatically checks for Jigarzon Launcher updates at startup and installs newer published releases.
- Checks Horizon's latest Nightly build on every startup and installs it when needed.
- Reads the current Minecraft Java Edition version from Horizon's official project information (currently 26.3).
- Home dashboard with the Jigarzon v2.00 release announcement and the current Horizon build label.
- Prism-inspired dark interface with the JL purple/cyan identity.
- Branded Windows and Linux application icons and platform-specific packages.
- System-tray support: closing the window keeps Jigarzon running in the notification area; the tray menu can reopen the launcher, launch the selected instance, or fully exit.
- Platform packages for Windows and Linux, including a Debian package and portable Linux archive.
- Instance manager to create, select, rename, reinstall and delete instances.
- Mod browser for Horizon-compatible content.
- Open the selected instance's Horizon mods folder.
- Optional Stats for Nerds developer gallery with live application logs and Horizon CLI access.
- In-app reinstall and uninstall controls, including a choice to preserve Horizon and Minecraft files.
- Drag and drop Horizon `.mrpack` or supported modpack `.zip` files to import them.

## Mods and compatibility

Horizon does not run arbitrary Java mod JARs as-is. Its mod browser checks and ports supported mod content. Dropping a raw `.jar` into Jigarzon will therefore not activate it; use Horizon's mod browser for compatible mods. Modpack files are imported as their own instance.

A Microsoft account that owns Minecraft: Java Edition is required. Minecraft assets are downloaded from Mojang through Horizon and are not bundled with Jigarzon.

## Platform builds

- **Windows:** built from the `build` branch by `.github/workflows/build-windows.yml`, producing `Jigarzon-Setup-Windows.exe`.
- **macOS:** built separately from the `macos-build` branch by `.github/workflows/build-macos.yml`.
- **Linux:** built separately from the `linux-build` branch by `.github/workflows/build-linux.yml`, producing x86_64 and ARM64 Debian `.deb` packages and portable `.tar.gz` archives.

The Linux workflow builds native x86_64 and ARM64 versions of Jigarzon. A graphical Linux desktop with X11 or XWayland is required for the launcher UI and tray integration. **Important:** Horizon currently publishes its official Linux launcher for x86_64 only. The Jigarzon ARM64 app and installer run natively, but Horizon installation and gameplay remain unavailable on Linux ARM64 until Horizon publishes an ARM64 Linux build. The app reports this limitation rather than attempting to run an incompatible x86_64 binary.

The Debian package installs Jigarzon under `/opt/JigarzonLauncher` and adds an application-menu entry. Install the matching package with `sudo apt install ./Jigarzon-Launcher-Linux-x86_64.deb` or `sudo apt install ./Jigarzon-Launcher-Linux-arm64.deb`. The portable archive can be extracted and started with `./run-jigarzon.sh`.

Linux updates can be installed from a published matching architecture `.deb` release asset. The updater asks the desktop's PolicyKit authentication dialog to install the package. Future releases are checked automatically when Jigarzon starts.

Jigarzon is an independent project and is not affiliated with Mojang Studios or Microsoft.
