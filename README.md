# Jigarzon Launcher

Jigarzon Launcher is a Windows desktop launcher for Horizon, the Rust-based Minecraft: Java Edition client.

## Features

- Guided Microsoft sign-in and first-run setup.
- Automatically checks for Jigarzon Launcher updates at startup and installs newer published Windows releases. It prefers a matching Windows ARM64 or x64 installer when published, with the existing universal Windows installer as a fallback. It will never download a Windows installer on another operating system.
- Branded startup splash remains visible for at least seven seconds and until the launcher update check finishes.
- Checks Horizon's latest Nightly build on every startup and installs it when needed.
- Reads the current Minecraft Java Edition version from Horizon's official project information (currently 26.3).
- Home dashboard with the Jigarzon v1.00 release announcement and the current Horizon build label.
- Prism-inspired dark interface with the JL purple/cyan identity.
- Windows application icon, taskbar icon and Inno Setup installer branding.
- Per-user Windows installer with Start Menu and optional desktop shortcuts.
- Instance manager to create, select, rename, reinstall and delete instances.
- Custom Horizon Mods browser connected to the official [playhorizon.dev/mods](https://playhorizon.dev/mods) registry, with category search and direct installation into the selected instance.
- Open the selected instance's Horizon mods folder.
- Optional Stats for Nerds developer gallery with live application logs and Horizon CLI access.
- In-app reinstall and uninstall controls, including a choice to preserve Horizon and Minecraft files.
- Drag and drop Horizon `.mrpack` or supported modpack `.zip` files to import them.

## Mods and compatibility

Horizon does not run arbitrary Java mod JARs as-is. Its mod browser checks and ports supported mod content. Dropping a raw `.jar` into Jigarzon will therefore not activate it; use Horizon's mod browser for compatible mods. Modpack files are imported as their own instance.

A Microsoft account that owns Minecraft: Java Edition is required. Minecraft assets are downloaded from Mojang through Horizon and are not bundled with Jigarzon.

## Building on Windows

The GitHub Actions workflow builds both `JigarzonLauncher.exe` and `Jigarzon-Setup.exe`. It uses PyInstaller and Inno Setup. Push a version tag such as `v1.0.0` to publish the installer as a GitHub Release. Future releases are checked automatically when Jigarzon starts.

Jigarzon is an independent project and is not affiliated with Mojang Studios or Microsoft.
