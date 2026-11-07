import json
import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP = "Jigarzon Launcher"
BG = "#0b0d14"
SIDEBAR = "#10131d"
PANEL = "#151a27"
PANEL2 = "#1b2232"
BORDER = "#283248"
TEXT = "#f1f5ff"
MUTED = "#8e9bb3"
ACCENT = "#9b6bff"
ACCENT_HOVER = "#b18cff"
CYAN = "#5ce1e6"
GREEN = "#65e6a6"
RED = "#ff7188"

def settings_file():
    folder = Path(os.getenv("APPDATA", str(Path.home()))) / "JigarzonLauncher"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"

def load_settings():
    try:
        return json.loads(settings_file().read_text(encoding="utf-8"))
    except Exception:
        return {}

def extract_tags(data):
    found = []
    def walk(value):
        if isinstance(value, str):
            if value:
                found.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if item.get("available_here", True) is not False:
                        tag = item.get("tag") or item.get("version")
                        if isinstance(tag, str) and tag:
                            found.append(tag)
                elif isinstance(item, str) and item:
                    found.append(item)
        elif isinstance(value, dict):
            for key in ("installed", "versions", "releases", "items", "data"):
                if key in value:
                    walk(value[key])
            selected = value.get("selected")
            if isinstance(selected, str) and selected:
                found.append(selected)
    walk(data)
    result = []
    for item in found:
        if item not in result and len(item) < 100:
            result.append(item)
    return result

class Jigarzon:
    def __init__(self, root):
        self.root = root
        self.root.title(APP)
        self.root.geometry("1160x760")
        self.root.minsize(980, 660)
        self.root.configure(bg=BG)
        self.queue = queue.Queue()
        self.busy = False
        self.installed = []
        self.available = []
        self.instances = []
        saved = load_settings()
        self.exe = tk.StringVar(value=saved.get("horizon_path", ""))
        self.selected_version = tk.StringVar(value=saved.get("version", ""))
        self.status = tk.StringVar(value="Horizon not connected")
        self.current_page = "Home"
        self.build_ui()
        self.find_horizon()
        self.root.after(100, self.poll)
        if self.exe.get():
            self.refresh_all()

    def save(self):
        settings_file().write_text(json.dumps({
            "horizon_path": self.exe.get(),
            "version": self.selected_version.get()
        }, indent=2), encoding="utf-8")

    def style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("J.TCombobox", fieldbackground=PANEL2, background=PANEL2,
                        foreground=TEXT, arrowcolor=CYAN, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, padding=9)
        style.map("J.TCombobox", fieldbackground=[("readonly", PANEL2)],
                  foreground=[("readonly", TEXT)], selectbackground=[("readonly", PANEL2)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("J.Horizontal.TProgressbar", troughcolor=PANEL2,
                        background=ACCENT, bordercolor=PANEL2, lightcolor=ACCENT,
                        darkcolor=ACCENT)

    def label(self, parent, text, size=10, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")),
                        fg=color, font=("Segoe UI", size, "bold" if bold else "normal"),
                        **kwargs)

    def button(self, parent, text, command, primary=False, compact=False):
        return tk.Button(parent, text=text, command=command, cursor="hand2",
                         bg=ACCENT if primary else PANEL2, fg=TEXT,
                         activebackground=ACCENT_HOVER if primary else BORDER,
                         activeforeground=TEXT, relief="flat", bd=0,
                         padx=14 if compact else 18, pady=8 if compact else 11,
                         font=("Segoe UI", 9, "bold"),
                         disabledforeground="#667085")

    def card(self, parent, padx=16, pady=16):
        frame = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        frame.pack_propagate(False)
        return frame

    def build_ui(self):
        self.style()
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg=SIDEBAR, width=218)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(24, 30))
        tk.Label(brand, text="J", bg=ACCENT, fg="white",
                 font=("Segoe UI", 20, "bold"), width=2, height=1).pack(side="left", padx=(0, 10))
        titlebox = tk.Frame(brand, bg=SIDEBAR)
        titlebox.pack(side="left")
        self.label(titlebox, "JIGARZON", 15, TEXT, True).pack(anchor="w")
        self.label(titlebox, "GAME MANAGEMENT", 7, MUTED, True).pack(anchor="w")

        self.label(self.sidebar, "LIBRARY", 8, MUTED, True).pack(anchor="w", padx=20, pady=(0, 9))
        self.nav_buttons = {}
        for name, glyph in [("Home", "⌂"), ("Instances", "▦"), ("Tutorial", "◉"), ("Settings", "⚙")]:
            b = tk.Button(self.sidebar, text=f"   {glyph}     {name}", anchor="w",
                          command=lambda n=name: self.show_page(n), cursor="hand2",
                          bg=SIDEBAR, fg=TEXT, activebackground=PANEL2,
                          activeforeground=TEXT, relief="flat", bd=0,
                          padx=10, pady=12, font=("Segoe UI", 10, "bold"))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = b

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=18, pady=18)
        self.label(self.sidebar, "HORIZON STATUS", 8, MUTED, True).pack(anchor="w", padx=20)
        self.status_dot = tk.Label(self.sidebar, text="●", bg=SIDEBAR, fg=RED,
                                   font=("Segoe UI", 10))
        self.status_dot.pack(anchor="w", padx=20, pady=(10, 2))
        self.status_label = self.label(self.sidebar, "Not connected", 8, MUTED)
        self.status_label.pack(anchor="w", padx=37)
        self.label(self.sidebar, "JIGARZON  /  1.0", 7, "#56627a", True).pack(side="bottom", anchor="w", padx=20, pady=18)

        content = tk.Frame(shell, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        top = tk.Frame(content, bg=BG, height=70)
        top.pack(fill="x", padx=28, pady=(16, 8))
        top.pack_propagate(False)
        lefttop = tk.Frame(top, bg=BG)
        lefttop.pack(side="left", fill="y")
        self.page_title = self.label(lefttop, "Home", 20, TEXT, True)
        self.page_title.pack(anchor="w", pady=(7, 0))
        self.page_subtitle = self.label(lefttop, "Your Minecraft library, ready when you are.", 8, MUTED)
        self.page_subtitle.pack(anchor="w")
        self.button(top, "↻  Refresh", self.refresh_all, compact=True).pack(side="right", pady=10)

        self.page_host = tk.Frame(content, bg=BG)
        self.page_host.pack(fill="both", expand=True, padx=28, pady=(4, 22))
        self.show_page("Home")

    def find_horizon(self):
        candidates = [
            shutil.which("horizon-launcher.exe"),
            str(Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Horizon/horizon-launcher.exe"),
            str(Path(os.getenv("LOCALAPPDATA", "")) / "Horizon/horizon-launcher.exe")
        ]
        for item in candidates:
            if item and Path(item).is_file():
                self.exe.set(item)
                self.save()
                break

    def show_page(self, name):
        self.current_page = name
        for key, button in self.nav_buttons.items():
            button.configure(bg=PANEL2 if key == name else SIDEBAR,
                             fg=CYAN if key == name else TEXT)
        for child in self.page_host.winfo_children():
            child.destroy()
        self.page_title.configure(text=name)
        subtitles = {
            "Home": "Your Minecraft library, ready when you are.",
            "Instances": "Separate game folders, worlds and configurations.",
            "Tutorial": "A quick setup guide, from first launch to first world.",
            "Settings": "Connect Horizon and manage your launcher preferences."
        }
        self.page_subtitle.configure(text=subtitles.get(name, ""))
        if name == "Home":
            self.home_page()
        elif name == "Instances":
            self.instances_page()
        elif name == "Tutorial":
            self.tutorial_page()
        else:
            self.settings_page()

    def section(self, parent, title, subtitle=None):
        self.label(parent, title.upper(), 9, CYAN, True).pack(anchor="w")
        if subtitle:
            self.label(parent, subtitle, 8, MUTED).pack(anchor="w", pady=(4, 0))

    def home_page(self):
        hero = tk.Frame(self.page_host, bg="#171b2b", highlightthickness=1, highlightbackground="#34304f")
        hero.pack(fill="x", pady=(0, 16))
        hero_left = tk.Frame(hero, bg="#171b2b")
        hero_left.pack(side="left", fill="both", expand=True, padx=24, pady=22)
        self.label(hero_left, "HORIZON  /  MINECRAFT JAVA", 8, CYAN, True).pack(anchor="w")
        self.label(hero_left, "A cleaner way to play.", 25, TEXT, True).pack(anchor="w", pady=(7, 4))
        self.label(hero_left, "Choose a build. Install the client. Prepare your game files. Play.", 9, MUTED).pack(anchor="w")
        hero_right = tk.Frame(hero, bg="#171b2b")
        hero_right.pack(side="right", padx=24, pady=24)
        self.button(hero_right, "OPEN SETUP GUIDE  →", lambda: self.show_page("Tutorial"), True).pack()

        row = tk.Frame(self.page_host, bg=BG)
        row.pack(fill="x", pady=(0, 15))
        version_card = tk.Frame(row, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        version_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        install_card = tk.Frame(row, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        install_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.section(version_card, "Version selection", "Select a published Horizon release or nightly build.")
        version_card.pack_configure(padx=18, pady=16)
        self.version_combo = ttk.Combobox(version_card, textvariable=self.selected_version,
                                          state="readonly", style="J.TCombobox")
        self.version_combo.pack(fill="x", pady=(12, 10))
        actions = tk.Frame(version_card, bg=PANEL)
        actions.pack(fill="x")
        self.button(actions, "Browse releases", self.load_releases, compact=True).pack(side="left")
        self.button(actions, "Install selected", self.install_selected, True, True).pack(side="right")

        self.section(install_card, "Game files", "Download and prepare the Minecraft resources your account owns.")
        install_card.pack_configure(padx=18, pady=16)
        self.label(install_card, "Mojang assets  •  libraries  •  game resources", 9, TEXT).pack(anchor="w", pady=(15, 9))
        self.button(install_card, "DOWNLOAD & PREPARE GAME FILES", self.prepare_download, True).pack(fill="x")
        self.label(install_card, "Requires Microsoft sign-in and Minecraft: Java Edition ownership.", 8, MUTED).pack(anchor="w", pady=(8, 0))

        bottom = tk.Frame(self.page_host, bg=BG)
        bottom.pack(fill="both", expand=True)
        play = tk.Frame(bottom, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        play.pack(side="left", fill="both", expand=True, padx=(0, 8))
        activity = tk.Frame(bottom, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        activity.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.section(play, "Launch", "Start your selected Horizon instance.")
        play.pack_configure(padx=18, pady=16)
        self.label(play, "READY WHEN YOU ARE", 17, TEXT, True).pack(anchor="w", pady=(14, 4))
        self.label(play, "The launcher will remember your selected release.", 8, MUTED).pack(anchor="w")
        self.button(play, "▶   PLAY MINECRAFT", self.play, True).pack(fill="x", pady=(18, 0))
        self.button(play, "Microsoft account sign-in", self.signin, compact=True).pack(fill="x", pady=(8, 0))
        self.section(activity, "Activity console", "Live output from Horizon commands.")
        activity.pack_configure(padx=18, pady=16)
        self.console = tk.Text(activity, height=9, bg="#0d111b", fg="#b9c7dc",
                               insertbackground=TEXT, relief="flat", bd=0,
                               font=("Cascadia Mono", 8), wrap="word")
        self.console.pack(fill="both", expand=True, pady=(10, 0))
        self.console.insert("end", "Jigarzon Launcher online. Connect Horizon in Settings to begin.\\n")

    def instances_page(self):
        head = tk.Frame(self.page_host, bg=BG)
        head.pack(fill="x", pady=(0, 14))
        self.section(head, "Your instances", "Horizon keeps each instance's worlds, options and packs in its own folder.")
        self.button(head, "↻  Load instances", self.load_instances, compact=True).pack(side="right")
        self.instance_list = tk.Listbox(self.page_host, bg=PANEL, fg=TEXT,
                                        selectbackground=ACCENT, selectforeground="white",
                                        relief="flat", bd=0, font=("Segoe UI", 10),
                                        highlightthickness=1, highlightbackground=BORDER)
        self.instance_list.pack(fill="both", expand=True, pady=(0, 12))
        controls = tk.Frame(self.page_host, bg=BG)
        controls.pack(fill="x")
        self.button(controls, "+  Create instance", self.create_instance, True).pack(side="left")
        self.button(controls, "Set selected as active", self.select_instance).pack(side="left", padx=8)
        self.label(self.page_host, "Tip: instances are isolated. Test mods or separate worlds without touching your main setup.", 8, MUTED).pack(anchor="w", pady=(12, 0))
        self.render_instances()

    def render_instances(self):
        if not hasattr(self, "instance_list") or not self.instance_list.winfo_exists():
            return
        self.instance_list.delete(0, "end")
        if not self.instances:
            self.instance_list.insert("end", "No instance data loaded yet. Connect Horizon and choose Load instances.")
        for item in self.instances:
            if isinstance(item, dict):
                name = item.get("name") or item.get("id") or str(item)
                folder = item.get("game_dir") or item.get("directory") or ""
                active = "  ★ ACTIVE" if item.get("selected") or item.get("active") else ""
                self.instance_list.insert("end", f"  {name}{active}    {folder}")
            else:
                self.instance_list.insert("end", f"  {item}")

    def tutorial_page(self):
        intro = tk.Frame(self.page_host, bg="#171b2b", highlightthickness=1, highlightbackground="#34304f")
        intro.pack(fill="x", pady=(0, 15))
        self.label(intro, "FIRST-TIME SETUP", 8, CYAN, True).pack(anchor="w", padx=20, pady=(17, 4))
        self.label(intro, "From zero to your first world.", 21, TEXT, True).pack(anchor="w", padx=20)
        self.label(intro, "Follow these steps in order. The launcher handles the downloads and setup.", 9, MUTED).pack(anchor="w", padx=20, pady=(5, 17))
        steps = [
            ("01", "Connect Horizon", "Open Settings, then browse to horizon-launcher.exe from your Horizon installation. This connects Jigarzon to the official Horizon command-line launcher."),
            ("02", "Choose a Horizon build", "Return to Home, open Browse releases, choose a release or Nightly build, then press Install selected. Jigarzon downloads and installs that client build."),
            ("03", "Sign in to Microsoft", "Press Microsoft account sign-in. Complete the sign-in in the browser using an account that owns Minecraft: Java Edition."),
            ("04", "Download Minecraft files", "Press Download & Prepare Game Files. Horizon prepares the resources from your Minecraft installation or downloads the required Mojang files for your signed-in account."),
            ("05", "Play", "Choose the installed build and press Play Minecraft. Horizon starts the selected instance with that version."),
            ("06", "Keep worlds organised", "Use Instances to create separate game folders. Each instance keeps its own worlds, options and packs.")
        ]
        for number, title, detail in steps:
            card = tk.Frame(self.page_host, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=number, bg=PANEL2, fg=CYAN, font=("Segoe UI", 12, "bold"),
                     width=4, height=2).pack(side="left", padx=14, pady=12)
            body = tk.Frame(card, bg=PANEL)
            body.pack(side="left", fill="x", expand=True, padx=(0, 14), pady=11)
            self.label(body, title, 10, TEXT, True).pack(anchor="w")
            self.label(body, detail, 8, MUTED, wraplength=760, justify="left").pack(anchor="w", pady=(3, 0))
        self.button(self.page_host, "GO TO HOME  →", lambda: self.show_page("Home"), True).pack(anchor="e", pady=(12, 0))

    def settings_page(self):
        card = tk.Frame(self.page_host, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=(0, 12))
        self.section(card, "Horizon executable", "Select the real horizon-launcher.exe file. Jigarzon does not bundle or replace Horizon.")
        card.pack_configure(padx=20, pady=18)
        row = tk.Frame(card, bg=PANEL)
        row.pack(fill="x", pady=(14, 0))
        tk.Entry(row, textvariable=self.exe, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 9))
        self.button(row, "Browse…", self.browse_horizon).pack(side="right")
        self.button(card, "Connect and refresh", self.refresh_all, True, True).pack(anchor="w", pady=(12, 0))
        info = tk.Frame(self.page_host, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill="x")
        self.section(info, "About Jigarzon", "A Prism-inspired interface for managing Horizon builds and Minecraft instances.")
        info.pack_configure(padx=20, pady=18)
        self.label(info, "Jigarzon Launcher is an independent project. Horizon is downloaded from its own release service.", 9, TEXT).pack(anchor="w", pady=(12, 4))
        self.label(info, "Minecraft is a trademark of Mojang Studios and Microsoft. This project is not affiliated with them.", 8, MUTED).pack(anchor="w")

    def browse_horizon(self):
        path = filedialog.askopenfilename(filetypes=[("Horizon launcher", "horizon-launcher.exe"), ("Applications", "*.exe")])
        if path:
            self.exe.set(path)
            self.save()
            self.refresh_all()

    def require_exe(self):
        path = Path(self.exe.get().strip().strip('"'))
        if not path.is_file():
            messagebox.showerror(APP, "Select the Horizon horizon-launcher.exe file in Settings first.")
            return None
        return path

    def run_command(self, args, label, callback=None, json_output=False):
        exe = self.require_exe()
        if not exe or self.busy:
            return
        self.busy = True
        self.save()
        self.set_status(label, True)
        self.write_log(f"\\n[{label}]")
        command = [str(exe), "--json"] + args if json_output else [str(exe)] + args

        def worker():
            try:
                proc = subprocess.Popen(command, cwd=str(exe.parent), stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                        errors="replace", bufsize=1)
                lines = []
                for line in proc.stdout:
                    line = line.rstrip()
                    lines.append(line)
                    if not json_output and line:
                        self.queue.put(("log", line))
                code = proc.wait()
                output = "\\n".join(lines)
                self.queue.put(("result", (code, output, label, callback, json_output)))
            except Exception as error:
                self.queue.put(("log", str(error)))
                self.queue.put(("result", (1, "", label, None, False)))
        threading.Thread(target=worker, daemon=True).start()

    def write_log(self, line):
        self.queue.put(("log", line))

    def set_status(self, message, active=False):
        self.queue.put(("status", (message, active)))

    def refresh_all(self):
        if not self.exe.get().strip():
            if self.current_page == "Settings":
                return
            self.set_status("Select Horizon in Settings", False)
            return
        self.load_installed()

    def load_releases(self):
        self.run_command(["versions"], "Loading available Horizon releases", self.on_releases, True)

    def load_installed(self):
        self.run_command(["versions", "--installed"], "Checking installed Horizon builds", self.on_installed, True)

    def on_releases(self, output):
        try:
            data = json.loads(output)
            self.available = extract_tags(data)
            if not self.available:
                self.write_log("No release tags were found in Horizon's response.")
            self.update_version_choices()
        except Exception:
            self.write_log("Could not read the release list. Check the Horizon output above.")

    def on_installed(self, output):
        try:
            data = json.loads(output)
            self.installed = extract_tags(data)
            self.write_log(f"Detected {len(self.installed)} installed Horizon build(s).")
            self.update_version_choices()
            self.load_releases()
        except Exception:
            self.write_log("Could not read installed builds. Try Browse releases.")

    def update_version_choices(self):
        choices = []
        for tag in self.installed + self.available:
            if tag not in choices:
                choices.append(tag)
        if hasattr(self, "version_combo") and self.version_combo.winfo_exists():
            self.version_combo["values"] = choices
        if self.selected_version.get() not in choices and choices:
            self.selected_version.set(choices[0])
        self.save()

    def install_selected(self):
        tag = self.selected_version.get().strip()
        if not tag:
            messagebox.showinfo(APP, "Load releases and choose a version first.")
            return
        if tag in self.installed:
            messagebox.showinfo(APP, f"{tag} is already installed.")
            return
        if not messagebox.askyesno(APP, f"Download and install Horizon {tag}?"):
            return
        self.run_command(["install", tag], f"Installing Horizon {tag}", self.after_install)

    def after_install(self, output):
        self.load_installed()

    def prepare_download(self):
        if not messagebox.askyesno(APP, "Horizon will prepare Minecraft files from your installation or download the required Mojang files. You must be signed in with an account that owns Minecraft: Java Edition. Continue?"):
            return
        tag = self.selected_version.get().strip()
        args = ["prepare", "--download"]
        if tag:
            args += ["--version", tag]
        self.run_command(args, f"Downloading and preparing Minecraft files for {tag or 'the selected build'}")

    def signin(self):
        self.run_command(["account", "sign-in"], "Opening Microsoft sign-in")

    def play(self):
        tag = self.selected_version.get().strip()
        if not tag:
            messagebox.showinfo(APP, "Choose a Horizon build first.")
            return
        if tag not in self.installed:
            if messagebox.askyesno(APP, f"Horizon {tag} is not installed. Install it now?"):
                self.run_command(["install", tag], f"Installing Horizon {tag}", lambda out: self.select_version_then_play(tag))
            return
        self.select_version_then_play(tag)

    def select_version_then_play(self, tag):
        self.run_command(["settings", "selected-version", tag],
                         f"Selecting Horizon {tag}",
                         lambda output: self.run_command(["play"], f"Playing Minecraft {tag} using Jigarzon Launcher"))

    def load_instances(self):
        self.run_command(["instance", "list"], "Loading instances", self.on_instances, True)

    def on_instances(self, output):
        try:
            data = json.loads(output)
            self.instances = data if isinstance(data, list) else data.get("instances", data.get("items", []))
            self.render_instances()
        except Exception:
            self.write_log("Could not parse the instance list.")

    def create_instance(self):
        from tkinter import simpledialog
        name = simpledialog.askstring(APP, "Name your new instance:")
        if name and name.strip():
            self.run_command(["instance", "create", name.strip()], f"Creating instance {name.strip()}", lambda out: self.load_instances())

    def select_instance(self):
        if not hasattr(self, "instance_list"):
            return
        selection = self.instance_list.curselection()
        if not selection or not self.instances:
            return
        item = self.instances[selection[0]]
        name = item.get("name") or item.get("id") if isinstance(item, dict) else str(item)
        if name:
            self.run_command(["instance", "select", name], f"Selecting instance {name}")

    def poll(self):
        try:
            while True:
                kind, value = self.queue.get_nowait()
                if kind == "log":
                    if hasattr(self, "console") and self.console.winfo_exists():
                        self.console.insert("end", value + "\\n")
                        self.console.see("end")
                elif kind == "status":
                    message, active = value
                    self.status.set(message)
                    self.status_dot.configure(fg=CYAN if active else GREEN)
                    self.status_label.configure(text=message[:30])
                elif kind == "result":
                    code, output, label, callback, is_json = value
                    self.busy = False
                    if is_json and output:
                        self.write_log(output)
                    if code == 0:
                        self.set_status(f"{label} complete", False)
                        if callback:
                            callback(output)
                    else:
                        self.set_status(f"{label} failed. Check activity output.", False)
                        if output:
                            self.write_log(output)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

if __name__ == "__main__":
    root = tk.Tk()
    app = Jigarzon(root)
    root.mainloop()
