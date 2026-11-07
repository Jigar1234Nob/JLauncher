import hashlib, json, os, platform, queue, subprocess, threading, urllib.request, zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

APP = "Jigarzon Launcher"
BG, SIDE, PANEL, ALT, BORDER = "#090B12", "#0D111B", "#141A28", "#1B2435", "#27334A"
TEXT, MUTED, PURPLE, CYAN, GREEN = "#F4F6FC", "#91A0B8", "#9875FF", "#62DCE8", "#69D9A4"
RELEASES = "https://api.github.com/repos/horizon-rust/horizon/releases?per_page=100"
ctk.set_appearance_mode("dark")

def data_dir():
    p = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "JigarzonLauncher"
    p.mkdir(parents=True, exist_ok=True)
    return p

def settings():
    try: return json.loads((data_dir() / "settings.json").read_text(encoding="utf-8"))
    except Exception: return {}

def save_settings(value):
    (data_dir() / "settings.json").write_text(json.dumps(value, indent=2), encoding="utf-8")

def locate_horizon():
    saved = settings().get("horizon_path", "")
    candidates = [Path(saved)] if saved else []
    candidates += [data_dir() / "Horizon" / "horizon-launcher.exe",
                   Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Horizon/horizon-launcher.exe"]
    for p in candidates:
        if p.is_file(): return p
    folder = data_dir() / "Horizon"
    if folder.exists():
        return next(iter(folder.rglob("horizon-launcher.exe")), None)
    return None

def install_horizon(progress):
    req = urllib.request.Request(RELEASES, headers={"User-Agent": "Jigarzon-Launcher", "Accept": "application/vnd.github+json"})
    progress("Checking official Horizon releases…", .05)
    with urllib.request.urlopen(req, timeout=30) as r: releases = json.loads(r.read().decode())
    release = next((r for r in releases if str(r.get("tag_name", "")).startswith("launcher@")), None)
    if not release: raise RuntimeError("No official Horizon launcher release was found.")
    arm = (platform.machine().lower() in ("arm64", "aarch64") or os.getenv("PROCESSOR_ARCHITECTURE", "").upper() == "ARM64" or os.getenv("PROCESSOR_ARCHITEW6432", "").upper() == "ARM64")
    filename = "horizon-launcher-windows-arm64.zip" if arm else "horizon-launcher-windows-x64.zip"
    asset = next((a for a in release.get("assets", []) if a.get("name") == filename), None)
    if not asset: raise RuntimeError("The official release is missing " + filename)
    archive = data_dir() / "horizon-package.zip"
    digest, received, total = hashlib.sha256(), 0, int(asset.get("size") or 0)
    progress("Downloading Horizon " + release["tag_name"].replace("launcher@", "") + "…", .1)
    req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "Jigarzon-Launcher"})
    with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as out:
        while True:
            block = response.read(1024 * 1024)
            if not block: break
            out.write(block); digest.update(block); received += len(block)
            progress("Downloading Horizon… " + str(round(received / 1048576, 1)) + " MB",
                     min(.1 + .75 * received / total, .85) if total else .5)
    expected = asset.get("digest") or ""
    if expected.startswith("sha256:") and digest.hexdigest().lower() != expected.split(":", 1)[1].lower():
        archive.unlink(missing_ok=True)
        raise RuntimeError("The downloaded Horizon package failed its SHA-256 check.")
    target = data_dir() / "Horizon"
    target.mkdir(parents=True, exist_ok=True)
    progress("Installing Horizon files…", .9)
    with zipfile.ZipFile(archive) as z:
        root = target.resolve()
        for member in z.infolist():
            dest = (target / member.filename).resolve()
            if dest != root and root not in dest.parents: raise RuntimeError("Unsafe path in Horizon archive.")
        z.extractall(target)
    archive.unlink(missing_ok=True)
    exe = next(iter(target.rglob("horizon-launcher.exe")), None)
    if not exe: raise RuntimeError("The package did not contain horizon-launcher.exe.")
    progress("Horizon is ready.", 1)
    return exe

def tags(data):
    out = []
    def walk(x):
        if isinstance(x, dict):
            for k in ("installed", "versions", "releases", "items", "data"):
                if k in x: walk(x[k])
            s = x.get("selected")
            if isinstance(s, str): out.append(s)
        elif isinstance(x, list):
            for i in x:
                if isinstance(i, dict):
                    if i.get("available_here", True) is not False:
                        t = i.get("tag") or i.get("version")
                        if isinstance(t, str): out.append(t)
                elif isinstance(i, str): out.append(i)
        elif isinstance(x, str): out.append(x)
    walk(data)
    return list(dict.fromkeys(t for t in out if t and len(t) < 100))

class Jigarzon:
    def __init__(self, root):
        self.root, self.jobs, self.busy = root, queue.Queue(), False
        self.root.title(APP); self.root.geometry("1220x790"); self.root.minsize(1020, 680)
        self.root.configure(fg_color=BG)
        saved = settings()
        self.exe = tk.StringVar(value=saved.get("horizon_path", ""))
        self.version = tk.StringVar(value=saved.get("version", ""))
        self.discord_id = tk.StringVar(value=saved.get("discord_app_id", ""))
        self.installed, self.available, self.instances = [], [], []
        self.rpc, self.game_active = None, False
        self.nav = {}
        self.build()
        self.root.after(100, self.poll)
        self.root.after(250, self.connect_startup)

    def save(self):
        save_settings({"horizon_path": self.exe.get(), "version": self.version.get(), "discord_app_id": self.discord_id.get().strip()})

    def label(self, p, text, size=11, color=TEXT, bold=False, **kw):
        return ctk.CTkLabel(p, text=text, text_color=color, font=("Segoe UI", size, "bold" if bold else "normal"),
                            anchor=kw.pop("anchor", "w"), justify=kw.pop("justify", "left"),
                            wraplength=kw.pop("wraplength", 0), **kw)

    def button(self, p, text, command, primary=False, **kw):
        return ctk.CTkButton(p, text=text, command=command, height=kw.pop("height", 40),
            corner_radius=13, font=("Segoe UI", 11, "bold"), fg_color=PURPLE if primary else ALT,
            hover_color="#AD91FF" if primary else "#29364D", text_color="white", **kw)

    def card(self, p):
        return ctk.CTkFrame(p, fg_color=PANEL, corner_radius=20, border_width=1, border_color=BORDER)

    def build(self):
        shell = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0); shell.pack(fill="both", expand=True)
        side = ctk.CTkFrame(shell, width=220, fg_color=SIDE, corner_radius=0); side.pack(side="left", fill="y"); side.pack_propagate(False)
        brand = ctk.CTkFrame(side, fg_color="transparent"); brand.pack(fill="x", padx=20, pady=(27, 34))
        logo = ctk.CTkFrame(brand, width=46, height=46, corner_radius=15, fg_color=PURPLE); logo.pack(side="left", padx=(0, 11)); logo.pack_propagate(False)
        self.label(logo, "J", 25, "white", True, anchor="center").pack(expand=True)
        btxt = ctk.CTkFrame(brand, fg_color="transparent"); btxt.pack(side="left")
        self.label(btxt, "JIGARZON", 17, TEXT, True).pack(anchor="w")
        self.label(btxt, "GAME LIBRARY", 9, MUTED, True).pack(anchor="w")
        self.label(side, "WORKSPACE", 9, MUTED, True).pack(anchor="w", padx=21, pady=(0, 10))
        for name, glyph in [("Home", "⌂"), ("Instances", "▦"), ("Tutorial", "◉"), ("Settings", "⚙")]:
            b = ctk.CTkButton(side, text="   " + glyph + "    " + name, anchor="w", height=46, corner_radius=13,
                fg_color="transparent", hover_color=ALT, text_color=TEXT, font=("Segoe UI", 12, "bold"),
                command=lambda n=name: self.page(n))
            b.pack(fill="x", padx=12, pady=3); self.nav[name] = b
        ctk.CTkFrame(side, fg_color="transparent").pack(fill="both", expand=True)
        stat = ctk.CTkFrame(side, fg_color=PANEL, corner_radius=16); stat.pack(fill="x", padx=14, pady=14)
        self.label(stat, "HORIZON STATUS", 9, MUTED, True).pack(anchor="w", padx=14, pady=(12, 3))
        self.status = self.label(stat, "●  Checking installation", 10, CYAN); self.status.pack(anchor="w", padx=14, pady=(0, 12))
        self.label(side, "JIGARZON  •  2.0", 9, "#65718A", True).pack(side="bottom", anchor="w", padx=20, pady=16)
        main = ctk.CTkFrame(shell, fg_color=BG, corner_radius=0); main.pack(side="left", fill="both", expand=True)
        header = ctk.CTkFrame(main, fg_color="transparent", height=78); header.pack(fill="x", padx=30, pady=(18, 8)); header.pack_propagate(False)
        hleft = ctk.CTkFrame(header, fg_color="transparent"); hleft.pack(side="left", fill="y")
        self.title = self.label(hleft, "Home", 25, TEXT, True); self.title.pack(anchor="w", pady=(7, 0))
        self.subtitle = self.label(hleft, "Your Minecraft library, ready when you are.", 10, MUTED); self.subtitle.pack(anchor="w")
        self.button(header, "↻ Refresh", self.refresh).pack(side="right", pady=12)
        self.body = ctk.CTkFrame(main, fg_color="transparent"); self.body.pack(fill="both", expand=True, padx=30, pady=(0, 22))
        self.page("Home")

    def section(self, p, title, sub=""):
        self.label(p, title, 13, TEXT, True).pack(anchor="w")
        if sub: self.label(p, sub, 10, MUTED, wraplength=650).pack(anchor="w", pady=(4, 0))

    def page(self, name):
        for w in self.body.winfo_children(): w.destroy()
        for n, b in self.nav.items(): b.configure(fg_color=ALT if n == name else "transparent", text_color=CYAN if n == name else TEXT)
        self.title.configure(text=name)
        self.subtitle.configure(text={"Home":"Your Minecraft library, ready when you are.","Instances":"Separate folders for worlds and configurations.","Tutorial":"From first download to first world.","Settings":"Manage Horizon and launcher preferences."}[name])
        {"Home":self.home,"Instances":self.instances_page,"Tutorial":self.tutorial,"Settings":self.settings}[name]()

    def home(self):
        hero = ctk.CTkFrame(self.body, fg_color="#171B2C", corner_radius=24, border_width=1, border_color="#383454")
        hero.pack(fill="x", pady=(0, 16))
        left = ctk.CTkFrame(hero, fg_color="transparent"); left.pack(side="left", fill="both", expand=True, padx=25, pady=24)
        self.label(left, "HORIZON  /  MINECRAFT JAVA", 10, CYAN, True).pack(anchor="w")
        self.label(left, "Your next world starts here.", 26, TEXT, True).pack(anchor="w", pady=(7, 4))
        self.label(left, "Versions, game files and setup. All in one place.", 11, MUTED).pack(anchor="w")
        self.button(hero, "SETUP GUIDE  →", lambda:self.page("Tutorial"), True, width=145).pack(side="right", padx=24, pady=34)
        row = ctk.CTkFrame(self.body, fg_color="transparent"); row.pack(fill="x", pady=(0, 15))
        v, g = self.card(row), self.card(row); v.pack(side="left", fill="both", expand=True, padx=(0, 8)); g.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.section(v, "Choose your version", "Browse official Horizon releases and nightly builds."); v.pack_configure(padx=19, pady=18)
        self.combo = ctk.CTkComboBox(v, variable=self.version, values=["Loading…"], state="readonly", height=42, corner_radius=12, fg_color=ALT, border_color=BORDER, button_color=PURPLE)
        self.combo.pack(fill="x", pady=(14, 10))
        line = ctk.CTkFrame(v, fg_color="transparent"); line.pack(fill="x")
        self.button(line, "Browse releases", self.releases, height=37).pack(side="left")
        self.button(line, "Install selected", self.install, True, height=37).pack(side="right")
        self.section(g, "Minecraft game files", "Horizon downloads verified resources from Mojang."); g.pack_configure(padx=19, pady=18)
        self.label(g, "Assets  •  libraries  •  Java runtime", 11, TEXT).pack(anchor="w", pady=(18, 12))
        self.button(g, "DOWNLOAD & PREPARE", self.prepare, True, height=43).pack(fill="x")
        self.label(g, "Requires a Microsoft account that owns Minecraft: Java Edition.", 9, MUTED, wraplength=420).pack(anchor="w", pady=(8, 0))
        bottom = ctk.CTkFrame(self.body, fg_color="transparent"); bottom.pack(fill="both", expand=True)
        play, log = self.card(bottom), self.card(bottom); play.pack(side="left", fill="both", expand=True, padx=(0, 8)); log.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.section(play, "Ready to play?", "Launch the selected Horizon build."); play.pack_configure(padx=19, pady=18)
        self.label(play, "MAKE IT A GOOD SESSION.", 16, TEXT, True).pack(anchor="w", pady=(18, 4))
        self.label(play, "Your selected release is saved automatically.", 10, MUTED).pack(anchor="w")
        self.button(play, "▶  PLAY MINECRAFT", self.play, True, height=47).pack(fill="x", pady=(18, 8))
        self.button(play, "Microsoft account sign-in", self.signin).pack(fill="x")
        self.section(log, "Activity", "Live download and launch output.")
        log.pack_configure(padx=19, pady=18)
        self.console = ctk.CTkTextbox(log, height=155, corner_radius=13, fg_color="#0C111C", text_color="#C5D0E2", font=("Cascadia Mono", 10), border_width=1, border_color=BORDER)
        self.console.pack(fill="both", expand=True, pady=(10, 0))
        self.console.insert("end", "Jigarzon is ready. Checking Horizon…\n")

    def instances_page(self):
        head = ctk.CTkFrame(self.body, fg_color="transparent"); head.pack(fill="x", pady=(0, 12))
        self.section(head, "Your instances", "Keep different worlds and configurations separate.")
        self.button(head, "↻ Load instances", self.load_instances).pack(side="right")
        self.instance_list = ctk.CTkScrollableFrame(self.body, fg_color=PANEL, corner_radius=18, border_width=1, border_color=BORDER)
        self.instance_list.pack(fill="both", expand=True)
        self.button(self.body, "+ Create instance", self.create_instance, True).pack(anchor="w", pady=12)

    def render_instances(self):
        if not hasattr(self, "instance_list") or not self.instance_list.winfo_exists(): return
        for w in self.instance_list.winfo_children(): w.destroy()
        if not self.instances: self.label(self.instance_list, "No instance data loaded. Press Load instances.", 11, MUTED).pack(anchor="w", padx=15, pady=18)
        for item in self.instances:
            name = item.get("name") or item.get("id") or "Instance" if isinstance(item, dict) else str(item)
            folder = (item.get("home") or item.get("game_dir") or "") if isinstance(item, dict) else ""
            row = ctk.CTkFrame(self.instance_list, fg_color=ALT, corner_radius=13); row.pack(fill="x", padx=9, pady=5)
            self.label(row, name, 12, TEXT, True).pack(anchor="w", padx=14, pady=(10, 2))
            if folder: self.label(row, folder, 9, MUTED).pack(anchor="w", padx=14, pady=(0, 10))

    def tutorial(self):
        intro = self.card(self.body); intro.pack(fill="x", pady=(0, 14))
        self.label(intro, "GETTING STARTED", 10, CYAN, True).pack(anchor="w", padx=20, pady=(18, 4))
        self.label(intro, "From first download to first world.", 22, TEXT, True).pack(anchor="w", padx=20)
        self.label(intro, "Jigarzon fetches the official Horizon package for your Windows architecture.", 10, MUTED).pack(anchor="w", padx=20, pady=(5, 18))
        steps = [("01","Horizon installs automatically","The official Windows ARM64 or x64 package is downloaded and its SHA-256 digest is checked."),
                 ("02","Choose a version","Browse Horizon builds and install the version you want."),
                 ("03","Sign in to Microsoft","Use an account that owns Minecraft: Java Edition."),
                 ("04","Prepare game files","Horizon downloads and verifies Minecraft assets and libraries from Mojang."),
                 ("05","Play","Choose your installed build and press Play Minecraft."),
                 ("06","Organise instances","Create separate game folders for different worlds and setups.")]
        for n, title, detail in steps:
            c = self.card(self.body); c.pack(fill="x", pady=5)
            self.label(c, n, 14, CYAN, True).pack(side="left", padx=17, pady=15)
            box = ctk.CTkFrame(c, fg_color="transparent"); box.pack(side="left", fill="x", expand=True, pady=11)
            self.label(box, title, 12, TEXT, True).pack(anchor="w")
            self.label(box, detail, 10, MUTED, wraplength=800).pack(anchor="w", pady=(3, 0))

    def settings(self):
        c = self.card(self.body); c.pack(fill="x", pady=(0, 13))
        self.section(c, "Horizon installation", "Jigarzon downloads and manages the official Horizon launcher.")
        self.path_label = self.label(c, self.exe.get() or "Horizon is not installed yet.", 10, MUTED, wraplength=800)
        self.path_label.pack(anchor="w", padx=19, pady=(12, 10))
        buttons = ctk.CTkFrame(c, fg_color="transparent"); buttons.pack(anchor="w", padx=19, pady=(0, 17))
        self.button(buttons, "Download / repair Horizon", self.download_horizon, True).pack(side="left")
        self.button(buttons, "Choose existing EXE", self.browse).pack(side="left", padx=8)
        d = self.card(self.body); d.pack(fill="x", pady=(0, 13))
        self.section(d, "Discord Rich Presence", "Show the Minecraft version on your Discord profile.")
        self.label(d, "Discord Application ID", 10, TEXT, True).pack(anchor="w", padx=19, pady=(13, 5))
        ctk.CTkEntry(d, textvariable=self.discord_id, height=42, corner_radius=12, fg_color=ALT, border_color=BORDER).pack(fill="x", padx=19)
        self.label(d, "Create an application at discord.com/developers/applications. Keep Discord desktop running.", 9, MUTED).pack(anchor="w", padx=19, pady=7)
        self.button(d, "Save Discord settings", self.save, True).pack(anchor="w", padx=19, pady=(2, 17))
        about = self.card(self.body); about.pack(fill="x")
        self.section(about, "About Jigarzon", "An independent desktop launcher for Horizon and Minecraft Java Edition.")
        self.label(about, "Not affiliated with Mojang Studios or Microsoft.", 10, MUTED).pack(anchor="w", padx=19, pady=15)

    def connect_startup(self):
        found = locate_horizon()
        if found:
            self.exe.set(str(found)); self.save(); self.log("Horizon launcher found."); self.refresh()
        else:
            self.log("Horizon is missing. Downloading the official package…"); self.download_horizon()

    def download_horizon(self):
        if self.busy: return
        self.busy = True; self.set_status("Downloading Horizon", True)
        def worker():
            try:
                path = install_horizon(lambda msg, pct: self.jobs.put(("progress", msg)))
                self.jobs.put(("horizon", str(path)))
            except Exception as e: self.jobs.put(("download_error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("Horizon launcher", "horizon-launcher.exe"), ("Applications", "*.exe")])
        if path:
            self.exe.set(path); self.save()
            if hasattr(self, "path_label"): self.path_label.configure(text=path)
            self.refresh()

    def require_exe(self):
        p = Path(self.exe.get().strip().strip('"'))
        if not p.is_file():
            messagebox.showerror(APP, "Horizon is not installed. Use Settings → Download / repair Horizon."); return None
        return p

    def command(self, args, label, callback=None, json_output=False):
        exe = self.require_exe()
        if not exe or self.busy: return
        self.busy = True; self.save(); self.set_status(label, True); self.log("\n[" + label + "]")
        cmd = [str(exe), "--json"] + args if json_output else [str(exe)] + args
        def work():
            try:
                proc = subprocess.Popen(cmd, cwd=str(exe.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace", bufsize=1)
                if label.startswith("Playing Minecraft "):
                    version = label[len("Playing Minecraft "):].removesuffix(" using Jigarzon Launcher")
                    self.game_active = True; self.jobs.put(("discord", version))
                lines = []
                for line in proc.stdout:
                    lines.append(line.rstrip())
                    if line.strip(): self.jobs.put(("log", line.rstrip()))
                self.jobs.put(("result", (proc.wait(), "\n".join(lines), label, callback, json_output)))
            except Exception as e: self.jobs.put(("result", (1, str(e), label, None, False)))
        threading.Thread(target=work, daemon=True).start()

    def refresh(self):
        if self.exe.get().strip(): self.load_installed()

    def load_installed(self): self.command(["versions", "--installed"], "Checking installed Horizon builds", self.installed_done, True)
    def releases(self): self.command(["versions"], "Loading Horizon releases", self.releases_done, True)

    def installed_done(self, out):
        try:
            self.installed = tags(json.loads(out)); self.update_versions(); self.releases()
        except Exception: self.log("Could not read installed Horizon builds.")

    def releases_done(self, out):
        try: self.available = tags(json.loads(out)); self.update_versions()
        except Exception: self.log("Could not read Horizon releases.")

    def update_versions(self):
        choices = list(dict.fromkeys(self.installed + self.available))
        if hasattr(self, "combo") and self.combo.winfo_exists(): self.combo.configure(values=choices or ["No versions found"])
        if choices and self.version.get() not in choices: self.version.set(choices[0])
        self.save()

    def install(self):
        tag = self.version.get().strip()
        if not tag: self.releases(); return
        if tag in self.installed: messagebox.showinfo(APP, tag + " is already installed."); return
        if messagebox.askyesno(APP, "Download and install Horizon " + tag + "?"):
            self.command(["install", tag], "Installing Horizon " + tag, lambda _: self.load_installed())

    def prepare(self):
        tag = self.version.get().strip()
        if not tag: messagebox.showinfo(APP, "Choose a Horizon version first."); return
        if messagebox.askyesno(APP, "Horizon will download and verify Minecraft files from Mojang. You must own Minecraft: Java Edition. Continue?"):
            self.command(["prepare", "--download", "--version", tag], "Preparing Minecraft " + tag)

    def signin(self): self.command(["account", "sign-in"], "Opening Microsoft sign-in")

    def play(self):
        tag = self.version.get().strip()
        if not tag: messagebox.showinfo(APP, "Choose a Horizon version first."); return
        if tag not in self.installed:
            if messagebox.askyesno(APP, tag + " is not installed. Install it now?"):
                self.command(["install", tag], "Installing Horizon " + tag, lambda _: self.play_version(tag))
            return
        self.play_version(tag)

    def play_version(self, tag): self.command(["play", "--version", tag], "Playing Minecraft " + tag + " using Jigarzon Launcher")

    def load_instances(self): self.command(["instance", "list"], "Loading instances", self.instances_done, True)
    def instances_done(self, out):
        try:
            d = json.loads(out); self.instances = d if isinstance(d, list) else d.get("instances", d.get("items", [])); self.render_instances()
        except Exception: self.log("Could not read instances.")
    def create_instance(self):
        name = ctk.CTkInputDialog(text="Name your new instance:", title="Create instance").get_input()
        if name and name.strip(): self.command(["instance", "create", name.strip()], "Creating instance", lambda _: self.load_instances())

    def discord_start(self, version):
        appid = self.discord_id.get().strip()
        if not appid: self.log("Add a Discord Application ID in Settings to enable Rich Presence."); return
        def connect():
            rpc = None
            try:
                from pypresence import Presence
                rpc = Presence(appid); rpc.connect()
                if not self.game_active: rpc.close(); return
                rpc.update(details="Playing Minecraft (" + version + ") using Jigarzon Launcher",
                           state="Minecraft Java Edition", large_text="Jigarzon Launcher")
                self.rpc = rpc; self.jobs.put(("log", "Discord Rich Presence connected."))
            except Exception as e:
                if rpc:
                    try: rpc.close()
                    except Exception: pass
                self.jobs.put(("log", "Discord Rich Presence unavailable: " + str(e)))
        threading.Thread(target=connect, daemon=True).start()

    def stop_discord(self):
        self.game_active = False; rpc, self.rpc = self.rpc, None
        if rpc:
            threading.Thread(target=lambda: (rpc.clear(), rpc.close()), daemon=True).start()

    def log(self, msg): self.jobs.put(("log", msg))
    def set_status(self, msg, active=False): self.jobs.put(("status", (msg, active)))

    def poll(self):
        try:
            while True:
                kind, val = self.jobs.get_nowait()
                if kind == "log" and hasattr(self, "console") and self.console.winfo_exists():
                    self.console.insert("end", val + "\n"); self.console.see("end")
                elif kind == "status": self.status.configure(text="●  " + val[0], text_color=CYAN if val[1] else GREEN)
                elif kind == "progress": self.status.configure(text="●  " + val, text_color=CYAN)
                elif kind == "horizon":
                    self.busy = False; self.exe.set(val); self.save(); self.log("Horizon installed: " + val); self.set_status("Horizon connected")
                    if hasattr(self, "path_label") and self.path_label.winfo_exists(): self.path_label.configure(text=val)
                    self.refresh()
                elif kind == "download_error":
                    self.busy = False; self.set_status("Horizon setup failed")
                    messagebox.showerror(APP, "Could not download Horizon:\n\n" + val + "\n\nRetry from Settings.")
                elif kind == "discord": self.discord_start(val)
                elif kind == "result":
                    code, out, label, callback, isjson = val; self.busy = False
                    if label.startswith("Playing Minecraft "): self.stop_discord()
                    if isjson and out: self.log(out)
                    if code == 0:
                        self.set_status(label + " complete")
                        if callback: callback(out)
                    else:
                        self.set_status(label + " failed")
                        if out: self.log(out)
        except queue.Empty: pass
        self.root.after(120, self.poll)

def main():
    root = ctk.CTk(); root.withdraw()
    splash = ctk.CTkToplevel(root); splash.geometry("520x330"); splash.resizable(False, False)
    splash.overrideredirect(True); splash.configure(fg_color=BG); splash.update_idletasks()
    x=(splash.winfo_screenwidth()-520)//2; y=(splash.winfo_screenheight()-330)//2; splash.geometry(f"520x330+{x}+{y}")
    frame=ctk.CTkFrame(splash, fg_color=PANEL, corner_radius=27, border_width=1, border_color=BORDER); frame.pack(fill="both", expand=True, padx=2, pady=2)
    logo=ctk.CTkFrame(frame, width=60, height=60, corner_radius=19, fg_color=PURPLE); logo.pack(pady=(35, 12)); logo.pack_propagate(False)
    ctk.CTkLabel(logo, text="J", font=("Segoe UI", 31, "bold"), text_color="white").pack(expand=True)
    ctk.CTkLabel(frame, text="JIGARZON", font=("Segoe UI", 24, "bold"), text_color=TEXT).pack()
    ctk.CTkLabel(frame, text="A better way into your next world.", font=("Segoe UI", 11), text_color=MUTED).pack(pady=(3, 24))
    bar=ctk.CTkProgressBar(frame, width=390, height=8, corner_radius=8, progress_color=PURPLE, fg_color=ALT); bar.pack(pady=(0, 13)); bar.set(.04)
    label=ctk.CTkLabel(frame, text="Starting Jigarzon…", font=("Segoe UI", 10), text_color=MUTED); label.pack()
    app=Jigarzon(root)
    def watch():
        label.configure(text=app.status.cget("text").replace("●  ", ""))
        if app.exe.get() and Path(app.exe.get()).is_file():
            bar.set(1); label.configure(text="Horizon is ready")
            root.after(650, finish); return
        if not app.busy and app.exe.get(): root.after(500, finish); return
        if not app.busy and "failed" in app.status.cget("text").lower():
            root.after(300, finish); return
        root.after(250, watch)
    def finish():
        try: splash.destroy()
        except Exception: pass
        root.deiconify(); root.lift()
    root.after(250, watch); root.mainloop()

if __name__ == "__main__":
    main()
