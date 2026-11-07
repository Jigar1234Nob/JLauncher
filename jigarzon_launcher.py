import hashlib, json, os, platform, queue, re, subprocess, sys, threading, urllib.request, zipfile
from pathlib import Path
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

APP = "Jigarzon Launcher"
APP_VERSION = "1.0.0"
APP_RELEASES = "https://api.github.com/repos/Jigar1234Nob/jigarzon-launcher/releases/latest"
HORIZON_README = "https://raw.githubusercontent.com/horizon-rust/horizon/main/README.md"
DISCORD_APP_ID = os.getenv("JIGARZON_DISCORD_APP_ID", "").strip()
BG, SIDE, PANEL, ALT, BORDER = "#17191F", "#111319", "#20242D", "#292F3A", "#343C49"
TEXT, MUTED, PURPLE, CYAN, GREEN = "#F4F6FB", "#A1AABC", "#8B6CF6", "#63D4E6", "#63D6A0"
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
    filename = "horizon-launcher-windows-x64.zip"
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
        self.root.configure(bg=BG)
        self.set_window_icon(self.root)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)
        saved = settings()
        self.exe = tk.StringVar(value=saved.get("horizon_path", ""))
        self.version = tk.StringVar(value=saved.get("version", "latest"))
        self.signin_pending = False
        self.installed, self.available, self.instances = [], [], []
        self.selected_instance = saved.get("selected_instance", "Horizon")
        self.setup_complete = bool(saved.get("setup_complete", False))
        self.setup_step = int(saved.get("setup_step", 0))
        self.rpc, self.game_active = None, False
        self.minecraft_version = "26.3"
        self.nav = {}
        self.build()
        self.root.after(100, self.poll)
        self.root.after(250, self.connect_startup)
        self.root.after(800, self.check_launcher_update)
        self.root.after(1000, self.check_horizon_game_version)

    def save(self):
        save_settings({"horizon_path": self.exe.get(), "version": self.version.get(), "selected_instance": self.selected_instance, "setup_complete": self.setup_complete, "setup_step": self.setup_step})

    def label(self, p, text, size=11, color=TEXT, bold=False, **kw):
        return ctk.CTkLabel(p, text=text, text_color=color, font=("Segoe UI", size, "bold" if bold else "normal"),
                            anchor=kw.pop("anchor", "w"), justify=kw.pop("justify", "left"),
                            wraplength=kw.pop("wraplength", 0), **kw)

    def button(self, p, text, command, primary=False, **kw):
        return ctk.CTkButton(p, text=text, command=command, height=kw.pop("height", 40),
            corner_radius=9, font=("Segoe UI", 10, "bold"), fg_color=PURPLE if primary else ALT,
            hover_color="#AD91FF" if primary else "#29364D", text_color="white", **kw)

    def card(self, p):
        return ctk.CTkFrame(p, fg_color=PANEL, corner_radius=12, border_width=1, border_color=BORDER)

    def logo_mark(self, parent, size=44, background=SIDE):
        canvas=tk.Canvas(parent,width=size,height=size,bg=background,highlightthickness=0,bd=0)
        k=size/100
        def poly(points,fill):
            canvas.create_polygon(*[v*k for v in points],fill=fill,outline=fill)
        poly([10,34,52,7,52,76,30,94,7,94,30,75,30,35], "#A33BFF")
        poly([58,17,82,34,82,75,100,75,83,94,58,94], "#16BFEA")
        poly([52,7,58,17,58,94,52,88], "#5638E8")
        return canvas

    def build(self):
        shell=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0);shell.pack(fill="both",expand=True)
        side=ctk.CTkFrame(shell,width=215,fg_color=SIDE,corner_radius=0);side.pack(side="left",fill="y");side.pack_propagate(False)
        brand=ctk.CTkFrame(side,fg_color="transparent");brand.pack(fill="x",padx=19,pady=(25,32))
        logo=ctk.CTkFrame(brand,width=44,height=44,corner_radius=10,fg_color=SIDE);logo.pack(side="left",padx=(0,10));logo.pack_propagate(False)
        self.logo_mark(logo,44,SIDE).pack()
        b=ctk.CTkFrame(brand,fg_color="transparent");b.pack(side="left")
        self.label(b,"JIGARZON",16,TEXT,True).pack(anchor="w");self.label(b,"MINECRAFT LAUNCHER",8,MUTED,True).pack(anchor="w")
        self.label(side,"LIBRARY",9,MUTED,True).pack(anchor="w",padx=19,pady=(0,8))
        for name,glyph in [("Home","⌂"),("Instances","▦"),("Mods","✣"),("Settings","⚙")]:
            btn=ctk.CTkButton(side,text="   "+glyph+"    "+name,anchor="w",height=42,corner_radius=9,fg_color="transparent",hover_color=ALT,text_color=TEXT,font=("Segoe UI",11,"bold"),command=lambda n=name:self.page(n))
            btn.pack(fill="x",padx=10,pady=3);self.nav[name]=btn
        ctk.CTkFrame(side,fg_color="transparent").pack(fill="both",expand=True)
        stat=ctk.CTkFrame(side,fg_color=PANEL,corner_radius=11,border_width=1,border_color=BORDER);stat.pack(fill="x",padx=12,pady=12)
        self.label(stat,"HORIZON STATUS",8,MUTED,True).pack(anchor="w",padx=11,pady=(9,3))
        self.status=self.label(stat,"● Checking installation",9,CYAN);self.status.pack(anchor="w",padx=11,pady=(0,9))
        main=ctk.CTkFrame(shell,fg_color=BG,corner_radius=0);main.pack(side="left",fill="both",expand=True)
        header=ctk.CTkFrame(main,fg_color="transparent",height=72);header.pack(fill="x",padx=27,pady=(15,7));header.pack_propagate(False)
        left=ctk.CTkFrame(header,fg_color="transparent");left.pack(side="left",fill="y")
        self.title=self.label(left,"Home",23,TEXT,True);self.title.pack(anchor="w",pady=(4,0))
        self.subtitle=self.label(left,"Your Minecraft library.",10,MUTED);self.subtitle.pack(anchor="w")
        self.button(header,"↻ Refresh",self.refresh).pack(side="right",pady=9)
        self.body=ctk.CTkFrame(main,fg_color="transparent");self.body.pack(fill="both",expand=True,padx=27,pady=(0,18))
        self.page("Home")

    def section(self, p, title, sub=""):
        self.label(p, title, 13, TEXT, True).pack(anchor="w")
        if sub: self.label(p, sub, 10, MUTED, wraplength=650).pack(anchor="w", pady=(4, 0))

    def page(self,name):
        if not self.setup_complete and name!="Tutorial":name="Tutorial"
        for w in self.body.winfo_children():w.destroy()
        for n,b in self.nav.items():b.configure(fg_color=ALT if n==name else "transparent",text_color=CYAN if n==name else TEXT)
        self.title.configure(text=name)
        self.subtitle.configure(text={"Home":"Your Minecraft library.","Instances":"Manage separate game folders.","Mods":"Browse content for your selected instance.","Settings":"Game files and launcher preferences.","Tutorial":"Complete setup to unlock Jigarzon."}[name])
        {"Home":self.home,"Instances":self.instances_page,"Mods":self.mods_page,"Settings":self.settings,"Tutorial":self.tutorial}[name]()

    def home(self):
        hero=self.card(self.body);hero.pack(fill="x",pady=(0,13))
        self.label(hero,"JIGARZON  /  MINECRAFT JAVA",9,CYAN,True).pack(anchor="w",padx=21,pady=(17,4))
        self.label(hero,"Ready for your next world?",22,TEXT,True).pack(anchor="w",padx=21)
        self.label(hero,"Choose an instance and start playing.",10,MUTED).pack(anchor="w",padx=21,pady=(3,13))
        row=ctk.CTkFrame(hero,fg_color="transparent");row.pack(fill="x",padx=20,pady=(0,17))
        self.label(row,"INSTANCE",9,MUTED,True).pack(side="left",padx=(0,9))
        names=[(x.get("name") or x.get("id") or "Horizon") if isinstance(x,dict) else str(x) for x in self.instances] or ["Horizon"]
        if self.selected_instance not in names:self.selected_instance=names[0]
        self.instance_menu=ctk.CTkOptionMenu(row,values=names,variable=tk.StringVar(value=self.selected_instance),command=self.select_instance,fg_color=ALT,button_color=PURPLE,button_hover_color="#7357D5",dropdown_fg_color=PANEL,text_color=TEXT,corner_radius=8,width=220,height=34);self.instance_menu.pack(side="left")
        self.button(row,"Manage instances",lambda:self.page("Instances")).pack(side="right")
        play=self.card(self.body);play.pack(fill="x",pady=(0,13))
        self.label(play,"MINECRAFT JAVA EDITION",9,MUTED,True).pack(anchor="w",padx=21,pady=(16,3))
        self.horizon_build_label=self.label(play,"Horizon Nightly Latest Build ("+self.minecraft_version+")",15,TEXT,True)
        self.horizon_build_label.pack(anchor="w",padx=21,pady=(0,12))
        self.button(play,"▶   PLAY MINECRAFT",self.play,True,height=47).pack(fill="x",padx=21,pady=(0,17))
        news=self.card(self.body);news.pack(fill="both",expand=True)
        self.label(news,"JIGARZON RELEASE",10,CYAN,True).pack(anchor="w",padx=19,pady=(20,7))
        self.label(news,"Jigarzon Launcher v1.00 has released!",21,TEXT,True).pack(anchor="w",padx=19)
        self.label(news,"Your Minecraft worlds, instances and mods. One launcher, with a cleaner way to play.",10,MUTED,wraplength=760).pack(anchor="w",padx=19,pady=(7,20))

    def instances_page(self):
        head=ctk.CTkFrame(self.body,fg_color="transparent");head.pack(fill="x",pady=(0,10))
        self.section(head,"Instances","Each instance keeps its own worlds, settings and mods.")
        self.button(head,"↻ Refresh",self.load_instances).pack(side="right")
        self.instance_list=ctk.CTkScrollableFrame(self.body,fg_color=PANEL,corner_radius=11,border_width=1,border_color=BORDER);self.instance_list.pack(fill="both",expand=True)
        self.button(self.body,"＋ Create instance",self.create_instance,True).pack(anchor="w",pady=11)
        self.load_instances()

    def render_instances(self):
        if not hasattr(self,"instance_list") or not self.instance_list.winfo_exists():return
        for w in self.instance_list.winfo_children():w.destroy()
        if not self.instances:self.label(self.instance_list,"No instances returned by Horizon.",10,MUTED).pack(anchor="w",padx=14,pady=16)
        for item in self.instances:
            name=(item.get("name") or item.get("id") or "Instance") if isinstance(item,dict) else str(item)
            folder=(item.get("home") or item.get("game_dir") or item.get("path") or "") if isinstance(item,dict) else ""
            row=ctk.CTkFrame(self.instance_list,fg_color=ALT,corner_radius=9,border_width=1,border_color=BORDER);row.pack(fill="x",padx=7,pady=4)
            self.label(row,name,11,TEXT,True).pack(anchor="w",padx=12,pady=(9,1))
            if folder:self.label(row,folder,8,MUTED).pack(anchor="w",padx=12,pady=(0,5))
            actions=ctk.CTkFrame(row,fg_color="transparent");actions.pack(fill="x",padx=8,pady=(2,8))
            self.button(actions,"Select",lambda n=name:self.select_instance(n),True,height=29,width=72).pack(side="left",padx=3)
            self.button(actions,"Rename",lambda n=name:self.rename_instance(n),height=29,width=72).pack(side="left",padx=3)
            self.button(actions,"Reinstall",lambda n=name:self.reinstall_instance(n),height=29,width=80).pack(side="left",padx=3)
            self.button(actions,"Delete",lambda n=name:self.delete_instance(n),height=29,width=72).pack(side="right",padx=3)

    def load_instances(self):self.command(["instance","list"],"Loading instances",self.instances_done,True)
    def instances_done(self,out):
        try:
            d=json.loads(out);self.instances=d if isinstance(d,list) else d.get("instances",d.get("items",[]));self.render_instances()
            names=[(x.get("name") or x.get("id") or "Horizon") if isinstance(x,dict) else str(x) for x in self.instances]
            if names and self.selected_instance not in names:
                self.selected_instance=names[0]
                self.save()
                self.command(["instance","select",self.selected_instance],"Selecting "+self.selected_instance)
            if hasattr(self,"instance_menu") and self.instance_menu.winfo_exists():
                self.instance_menu.configure(values=names or ["Horizon"])
                self.instance_menu.set(self.selected_instance)
        except Exception:self.log("Could not read instances returned by Horizon.")
    def select_instance(self,name):
        self.selected_instance=name;self.save()
        if hasattr(self,"instance_menu") and self.instance_menu.winfo_exists():self.instance_menu.set(name)
        self.command(["instance","select",name],"Selecting "+name)
    def create_instance(self):
        name=ctk.CTkInputDialog(text="Choose an instance name:",title="Create instance").get_input()
        if name and name.strip():self.command(["instance","create",name.strip()],"Creating instance",lambda _:self.load_instances())
    def rename_instance(self,old):
        new=ctk.CTkInputDialog(text="New instance name:",title="Rename instance").get_input()
        if new and new.strip() and new.strip()!=old:
            def renamed(_):
                if self.selected_instance==old:self.selected_instance=new.strip();self.save()
                self.load_instances()
            self.command(["instance","rename",old,new.strip()],"Renaming instance",renamed)
    def delete_instance(self,name):
        if name.lower()=="horizon":messagebox.showwarning(APP,"The built-in Horizon instance cannot be deleted.");return
        if messagebox.askyesno(APP,"Delete "+name+"? Its game folder, worlds and packs are moved to the system Trash."):
            self.command(["instance","delete",name],"Deleting "+name,lambda _:self.load_instances())
    def reinstall_instance(self,name):
        if name.lower()=="horizon":messagebox.showwarning(APP,"The built-in Horizon instance cannot be reinstalled this way.");return
        if not messagebox.askyesno(APP,"Reinstall "+name+"? Its worlds, settings and packs will be moved to the system Trash, then a fresh empty instance will be created."):return
        def recreate(_):
            self.command(["instance","create",name],"Recreating "+name,
                lambda __:self.command(["instance","select",name],"Selecting "+name,lambda ___:self.load_instances()))
        self.command(["instance","delete",name],"Removing "+name,recreate)

    def tutorial(self):
        c=self.card(self.body);c.pack(fill="x",pady=(0,10))
        self.label(c,"FIRST-TIME SETUP",9,CYAN,True).pack(anchor="w",padx=21,pady=(20,5))
        self.label(c,"Let's get Minecraft ready.",22,TEXT,True).pack(anchor="w",padx=21)
        self.label(c,"Complete these steps in order. Jigarzon stays locked until all three are finished.",10,MUTED,wraplength=720).pack(anchor="w",padx=21,pady=(5,16))
        for n,title,desc,done in [("1","Sign in with Microsoft","Use an account that owns Minecraft: Java Edition.",self.setup_step>=1),("2","Install latest Horizon","Download the newest nightly build.",self.setup_step>=2),("3","Download game files","Fetch and verify required files from Mojang.",self.setup_step>=3)]:
            r=ctk.CTkFrame(c,fg_color=ALT,corner_radius=9,border_width=1,border_color=BORDER);r.pack(fill="x",padx=17,pady=5)
            self.label(r,("✓  " if done else n+"  ")+title,11,GREEN if done else TEXT,True).pack(anchor="w",padx=12,pady=(9,2))
            self.label(r,desc,9,MUTED).pack(anchor="w",padx=12,pady=(0,9))
        self.setup_action=self.button(c,"SIGN IN WITH MICROSOFT",self.setup_signin,True,height=43);self.setup_action.pack(fill="x",padx=17,pady=(14,8))
        if self.setup_step==1:self.setup_action.configure(text="INSTALL LATEST HORIZON",command=self.setup_install)
        elif self.setup_step==2:self.setup_action.configure(text="DOWNLOAD GAME FILES",command=self.setup_prepare)
        elif self.setup_step>=3:self.setup_action.configure(text="OPEN JIGARZON",command=self.finish_setup)
        self.label(c,"Your Microsoft password is entered only on Microsoft's own sign-in page.",9,MUTED).pack(anchor="w",padx=19,pady=(2,17))
        logs=self.card(self.body);logs.pack(fill="both",expand=True)
        self.section(logs,"Activity log","Live setup output and troubleshooting details.")
        self.console=ctk.CTkTextbox(logs,height=170,fg_color=ALT,text_color=TEXT,
                                   border_width=0,corner_radius=8,font=("Consolas",9),wrap="word")
        self.console.pack(fill="both",expand=True,padx=12,pady=(10,12))
        self.console.insert("end","Jigarzon Launcher activity log ready.\\n")
        self.console.configure(state="disabled")
    def setup_signin(self):
        self.signin_window = None
        self.command(["account","sign-in"],"Opening Microsoft sign-in",lambda _:self.command(["account"],"Checking Microsoft account",self.account_checked,True))

    def show_signin_code(self, code):
        if getattr(self, "signin_window", None) is not None:
            try:
                if self.signin_window.winfo_exists():
                    self.signin_code_label.configure(text=code)
                    self.signin_window.lift()
                    return
            except Exception: pass
        win=ctk.CTkToplevel(self.root); self.signin_window=win
        win.title("Microsoft sign-in"); win.geometry("430x270"); win.resizable(False,False)
        win.transient(self.root); win.grab_set()
        c=ctk.CTkFrame(win,fg_color=PANEL,corner_radius=14); c.pack(fill="both",expand=True,padx=14,pady=14)
        self.label(c,"MICROSOFT ACCOUNT",10,CYAN,True).pack(anchor="w",padx=18,pady=(18,5))
        self.label(c,"Enter this code",20,TEXT,True).pack(anchor="w",padx=18)
        self.signin_code_label=self.label(c,code,30,TEXT,True)
        self.signin_code_label.pack(anchor="w",padx=18,pady=(8,5))
        self.label(c,"Open microsoft.com/link and enter the code above.",10,MUTED).pack(anchor="w",padx=18,pady=(0,14))
        row=ctk.CTkFrame(c,fg_color="transparent"); row.pack(fill="x",padx=18,pady=(0,16))
        self.button(row,"COPY CODE",lambda: (self.root.clipboard_clear(),self.root.clipboard_append(self.signin_code_label.cget("text"))),True).pack(side="left")
        self.button(row,"OPEN MICROSOFT",lambda:webbrowser.open("https://www.microsoft.com/link")).pack(side="left",padx=8)
        win.protocol("WM_DELETE_WINDOW",win.destroy)

    def account_checked(self,out):
        try:
            d=json.loads(out);accounts=d if isinstance(d,list) else d.get("accounts",d.get("items",[]))
            if not accounts:raise ValueError()
            self.setup_step=1;self.save();self.page("Tutorial")
        except Exception:messagebox.showwarning(APP,"No signed-in Microsoft account was confirmed. Finish the browser sign-in, then try again.")
    def setup_install(self):self.command(["install","latest"],"Installing latest Horizon",lambda _:self.setup_installed())
    def setup_installed(self):self.setup_step=2;self.save();self.page("Tutorial")
    def setup_prepare(self):self.command(["prepare","--download"],"Downloading and checking Minecraft files",lambda _:self.setup_prepared())
    def setup_prepared(self):self.setup_step=3;self.save();self.page("Tutorial")
    def finish_setup(self):self.setup_complete=True;self.save();self.page("Home")

    def mods_page(self):
        card=self.card(self.body);card.pack(fill="x",pady=(0,10))
        self.label(card,"MOD BROWSER",9,CYAN,True).pack(anchor="w",padx=15,pady=(12,4))
        self.label(card,"Search mods for instance: "+self.selected_instance,9,MUTED).pack(anchor="w",padx=15)
        row=ctk.CTkFrame(card,fg_color="transparent");row.pack(fill="x",padx=13,pady=11)
        self.mod_query=ctk.CTkEntry(row,placeholder_text="Search mods…",height=36,fg_color=ALT,border_color=BORDER,corner_radius=8);self.mod_query.pack(side="left",fill="x",expand=True,padx=(0,7))
        self.button(row,"Search",self.search_mods,True,height=36).pack(side="left")
        self.button(row,"Installed",self.list_mods,height=36).pack(side="left",padx=(7,0))
        self.button(row,"OPEN MODS FOLDER",self.open_selected_mod_folder,height=36).pack(side="right",padx=(7,0))
        self.drop_hint=self.label(card,"Or drag a Horizon .mrpack / supported modpack ZIP onto this window to import it.",9,MUTED)
        self.drop_hint.pack(anchor="w",padx=15,pady=(0,10))
        self.mod_list=ctk.CTkScrollableFrame(self.body,fg_color=PANEL,corner_radius=11,border_width=1,border_color=BORDER);self.mod_list.pack(fill="both",expand=True)
        self.label(self.mod_list,"Search for mods or view installed content.",10,MUTED).pack(anchor="w",padx=13,pady=15)
    def selected_instance_game_dir(self):
        for item in self.instances:
            if isinstance(item,dict) and (item.get("name") or item.get("id")) == self.selected_instance:
                for key in ("game_dir","game_directory","home","path","directory"):
                    value=item.get(key)
                    if value:
                        p=Path(value).expanduser()
                        if p.exists():return p
        exe=Path(self.exe.get()).resolve() if self.exe.get() else None
        candidates=[]
        if exe:
            candidates += [exe.parent/"game",exe.parent/"data",exe.parent]
        candidates += [data_dir()/"Horizon"/"game",data_dir()/"Horizon"]
        for p in candidates:
            if p.exists() and (p/"options.txt").exists():return p
        return None

    def open_selected_mod_folder(self):
        game_dir=self.selected_instance_game_dir()
        if not game_dir:
            messagebox.showwarning(APP,"Could not determine the selected instance's game folder. Refresh the Instances list and try again.")
            return
        folder=game_dir/"horizon-mods"
        folder.mkdir(parents=True,exist_ok=True)
        os.startfile(str(folder))

    def on_drop(self,event):
        try:paths=[Path(p.strip("{}")) for p in self.root.tk.splitlist(event.data)]
        except Exception:
            messagebox.showwarning(APP,"Windows did not provide a readable dropped file path.")
            return
        if not paths:return
        accepted=[p for p in paths if p.is_file() and p.suffix.lower() in (".mrpack",".zip")]
        unsupported=[p.name for p in paths if p.is_file() and p.suffix.lower()==".jar"]
        if unsupported:
            messagebox.showinfo(APP,"Raw Java .jar mods cannot simply be dropped into Horizon. Horizon needs to check and port supported mod content first. Use the in-app mod browser for compatible mods.")
        if accepted:
            for pack in accepted:
                if messagebox.askyesno(APP,"Import "+pack.name+" with Horizon? Modpacks are imported as their own instance."):
                    self.command(["modpack","import",str(pack)],"Importing "+pack.name,lambda _:self.load_instances())
        elif not unsupported:
            messagebox.showinfo(APP,"Drop a Horizon .mrpack or supported modpack .zip file here.")

    def show_mod_output(self,out,installed=False):
        if not hasattr(self,"mod_list") or not self.mod_list.winfo_exists():return
        for w in self.mod_list.winfo_children():w.destroy()
        try:
            d=json.loads(out);items=d if isinstance(d,list) else d.get("results",d.get("mods",d.get("items",[])))
            if not isinstance(items,list):items=[]
        except Exception:items=[]
        if not items:self.label(self.mod_list,"No results returned. Check Horizon's response in the activity log.",10,MUTED).pack(anchor="w",padx=13,pady=15);return
        for item in items:
            if isinstance(item,dict):
                name=item.get("name") or item.get("title") or item.get("id") or item.get("slug") or "Mod";slug=item.get("slug") or item.get("id") or item.get("project_id") or name
                desc=item.get("summary") or item.get("description") or item.get("author") or ""
            else:name=str(item);slug=name;desc=""
            r=ctk.CTkFrame(self.mod_list,fg_color=ALT,corner_radius=8,border_width=1,border_color=BORDER);r.pack(fill="x",padx=6,pady=4)
            self.label(r,name,11,TEXT,True).pack(anchor="w",padx=11,pady=(8,1));self.label(r,str(desc)[:200],9,MUTED,wraplength=730).pack(anchor="w",padx=11,pady=(0,6))
            if not installed:
                self.button(r,"Install",lambda ident=str(slug):self.install_mod(ident),True,height=29,width=78).pack(anchor="e",padx=9,pady=(0,7))
            else:
                self.button(r,"Remove",lambda ident=str(slug):self.remove_mod(ident),height=29,width=78).pack(anchor="e",padx=9,pady=(0,7))
    def search_mods(self):
        q=self.mod_query.get().strip()
        if q:self.command(["mods","search",q],"Searching mods",lambda out:self.show_mod_output(out),True)
        else:messagebox.showinfo(APP,"Enter a mod name to search.")
    def list_mods(self):self.command(["mods","list","--instance",self.selected_instance],"Loading installed mods",lambda out:self.show_mod_output(out,True),True)
    def install_mod(self,slug):
        if messagebox.askyesno(APP,"Install "+slug+" into "+self.selected_instance+"?"):
            self.command(["mods","install",slug,"--instance",self.selected_instance],"Installing "+slug,lambda _:self.list_mods())
    def remove_mod(self,slug):
        if messagebox.askyesno(APP,"Remove "+slug+" from "+self.selected_instance+"?"):
            self.command(["mods","remove",slug,"--instance",self.selected_instance],"Removing "+slug,lambda _:self.list_mods())
    def settings(self):
        c=self.card(self.body);c.pack(fill="x",pady=(0,11))
        self.section(c,"Minecraft game files","Check, download and repair the files required to play.")
        self.label(c,"Horizon verifies existing downloads and fetches missing or damaged files from Mojang.",9,MUTED).pack(anchor="w",padx=17,pady=(9,11))
        self.button(c,"CHECK / UPDATE GAME FILES",self.check_gamefiles,True,height=40).pack(anchor="w",padx=17,pady=(0,9))
        self.button(c,"UPDATE HORIZON TO LATEST",self.update_horizon,height=36).pack(anchor="w",padx=17,pady=(0,15))
        h=self.card(self.body);h.pack(fill="x",pady=(0,11));self.section(h,"Horizon installation","Manage the official Horizon launcher package.")
        self.path_label=self.label(h,self.exe.get() or "Horizon is not installed yet.",9,MUTED,wraplength=740);self.path_label.pack(anchor="w",padx=17,pady=(9,9))
        buttons=ctk.CTkFrame(h,fg_color="transparent");buttons.pack(anchor="w",padx=17,pady=(0,13))
        self.button(buttons,"Download / repair Horizon",self.download_horizon,True).pack(side="left");self.button(buttons,"Choose existing EXE",self.browse).pack(side="left",padx=7)
        a=self.card(self.body);a.pack(fill="x");self.section(a,"About Jigarzon","Independent launcher for Horizon and Minecraft Java Edition.")
        self.label(a,"Not affiliated with Mojang Studios or Microsoft.",9,MUTED).pack(anchor="w",padx=17,pady=12)
    def check_gamefiles(self):self.command(["prepare","--download"],"Checking and updating Minecraft game files")
    def update_horizon(self):self.command(["install","latest"],"Updating Horizon to latest")

    def connect_startup(self):
        found = locate_horizon()
        if found:
            self.exe.set(str(found)); self.save(); self.log("Horizon launcher found.")
            if not self.setup_complete:self.page("Tutorial")
            self.command(["install","latest"],"Checking for Horizon updates",lambda _:self.refresh())
        else:
            self.log("Horizon is missing. Downloading the official package…"); self.download_horizon()

    def check_horizon_game_version(self):
        def work():
            try:
                req=urllib.request.Request(HORIZON_README,headers={"User-Agent":"Jigarzon-Launcher"})
                with urllib.request.urlopen(req,timeout=12) as response: body=response.read().decode("utf-8","replace")
                match=re.search(r"Minecraft: Java Edition\\s+(\\d+\\.\\d+)",body)
                if match:self.jobs.put(("game_version",match.group(1)))
            except Exception as e:self.jobs.put(("log","Could not check the current Minecraft version: "+str(e)))
        threading.Thread(target=work,daemon=True).start()

    def check_launcher_update(self):
        def work():
            try:
                req=urllib.request.Request(APP_RELEASES,headers={"User-Agent":"Jigarzon-Launcher","Accept":"application/vnd.github+json"})
                with urllib.request.urlopen(req,timeout=15) as response: release=json.loads(response.read().decode("utf-8"))
                tag=str(release.get("tag_name","")).lstrip("v")
                def version_tuple(v):
                    found=re.findall(r"\\d+",v)
                    return tuple(int(x) for x in found[:3]) if found else (0,)
                if version_tuple(tag)<=version_tuple(APP_VERSION):return
                asset=next((a for a in release.get("assets",[]) if a.get("name")=="Jigarzon-Setup.exe"),None)
                if not asset: self.jobs.put(("log","Jigarzon update "+tag+" is published, but its installer asset is missing."));return
                self.jobs.put(("log","Jigarzon Launcher update "+tag+" found. Downloading installer…"))
                req=urllib.request.Request(asset["browser_download_url"],headers={"User-Agent":"Jigarzon-Launcher"})
                installer=data_dir()/"Jigarzon-Setup-update.exe"
                digest=hashlib.sha256()
                with urllib.request.urlopen(req,timeout=60) as response,installer.open("wb") as out:
                    while True:
                        block=response.read(1024*1024)
                        if not block:break
                        out.write(block);digest.update(block)
                expected=asset.get("digest") or ""
                if expected.startswith("sha256:") and digest.hexdigest().lower()!=expected.split(":",1)[1].lower():
                    installer.unlink(missing_ok=True);raise RuntimeError("Installer SHA-256 verification failed.")
                self.jobs.put(("launcher_update_ready",str(installer)))
            except Exception as e:
                # No published release yet is normal for a source checkout.
                if "HTTP Error 404" not in str(e):self.jobs.put(("log","Jigarzon update check: "+str(e)))
        threading.Thread(target=work,daemon=True).start()

    def install_launcher_update(self,installer):
        try:
            subprocess.Popen([installer,"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/CLOSEAPPLICATIONS","/RESTARTAPPLICATIONS"])
            self.root.after(300,self.root.destroy)
        except Exception as e:messagebox.showerror(APP,"Could not start the Jigarzon update installer:\\n\\n"+str(e))

    def set_window_icon(self,window):
        try:
            base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))
            icon=base/"assets"/"jigarzon.ico"
            if icon.is_file():window.iconbitmap(str(icon))
        except Exception:pass

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
                if label == "Opening Microsoft sign-in":
                    webbrowser.open("https://www.microsoft.com/link")
                if label.startswith("Playing Minecraft "):
                    version = label[len("Playing Minecraft "):].removesuffix(" using Jigarzon Launcher")
                    self.game_active = True; self.jobs.put(("discord", version))
                lines = []
                for line in proc.stdout:
                    clean=line.rstrip()
                    lines.append(clean)
                    if clean: self.jobs.put(("log", clean))
                    if label == "Opening Microsoft sign-in":
                        match=re.search(r"(?i)\\b(?:user\\s*)?code\\b\\s*[:=]?\\s*([A-Z0-9-]{6,})", clean)
                        if match:self.jobs.put(("signin_code", match.group(1).strip("-")))
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
        self.load_instances()

    def update_versions(self):
        choices = list(dict.fromkeys(self.installed + self.available))
        if hasattr(self, "combo") and self.combo.winfo_exists(): self.combo.configure(values=choices or ["No versions found"])
        if choices:
            self.version.set(choices[0])
        self.save()

    def install(self):
        self.command(["install", "latest"], "Installing latest Horizon", lambda _: self.load_installed())

    def prepare(self):
        tag = self.version.get().strip()
        if not tag: messagebox.showinfo(APP, "Choose a Horizon version first."); return
        if messagebox.askyesno(APP, "Horizon will download and verify Minecraft files from Mojang. You must own Minecraft: Java Edition. Continue?"):
            self.command(["prepare", "--download", "--version", tag], "Preparing Minecraft " + tag)

    def signin(self): self.command(["account", "sign-in"], "Opening Microsoft sign-in")

    def play(self):
        if not self.setup_complete:
            self.page("Tutorial")
            return
        self.command(["play", "--instance", self.selected_instance],
                     "Playing Minecraft latest using Jigarzon Launcher")

    def discord_start(self, version):
        appid = DISCORD_APP_ID
        if not appid: self.log("Discord Rich Presence is waiting for the Jigarzon Discord Application ID to be configured in the build."); return
        def connect():
            rpc = None
            try:
                from pypresence import Presence
                rpc = Presence(appid); rpc.connect()
                if not self.game_active: rpc.close(); return
                rpc.update(details="Playing Minecraft " + version + " using Jigarzon Launcher",
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
                    self.console.configure(state="normal")
                    self.console.insert("end", val + "\n"); self.console.see("end")
                    self.console.configure(state="disabled")
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
                elif kind == "signin_code": self.show_signin_code(val)
                elif kind == "game_version":
                    self.minecraft_version=val
                    if hasattr(self,"horizon_build_label") and self.horizon_build_label.winfo_exists():
                        self.horizon_build_label.configure(text="Horizon Nightly Latest Build ("+val+")")
                elif kind == "launcher_update_ready":
                    self.log("A newer Jigarzon version is ready. Starting the installer.")
                    self.install_launcher_update(val)
                elif kind == "result":
                    code, out, label, callback, isjson = val; self.busy = False
                    if label.startswith("Playing Minecraft "):
                        self.stop_discord()
                        if "Sign in with a Microsoft account that owns Minecraft: Java Edition to play" in out and not self.signin_pending:
                            self.signin_pending = True
                            self.log("No Minecraft account is signed in. Opening Microsoft sign-in in your browser…")
                            self.command(["account", "sign-in"], "Opening Microsoft sign-in", lambda _: setattr(self, "signin_pending", False))
                    if isjson and out: self.log(out)
                    if code == 0:
                        if label == "Opening Microsoft sign-in": self.signin_pending = False
                        self.set_status(label + " complete")
                        if callback: callback(out)
                    else:
                        if label == "Opening Microsoft sign-in":
                            self.signin_pending = False
                            details=out.strip() or "Horizon did not return a Microsoft device code."
                            messagebox.showerror(APP,"Microsoft sign-in could not start.\n\n"+details+"\n\nIf the message says the sign-in app is not configured, the Horizon build needs its Microsoft client ID.")
                        self.set_status(label + " failed")
        except queue.Empty: pass
        self.root.after(120, self.poll)

def main():
    root = TkinterDnD.Tk(); root.withdraw()
    splash = ctk.CTkToplevel(root); splash.geometry("520x330"); splash.resizable(False, False)
    splash.overrideredirect(True); splash.configure(fg_color=BG); splash.update_idletasks()
    x=(splash.winfo_screenwidth()-520)//2; y=(splash.winfo_screenheight()-330)//2; splash.geometry(f"520x330+{x}+{y}")
    frame=ctk.CTkFrame(splash, fg_color=PANEL, corner_radius=16, border_width=1, border_color=BORDER); frame.pack(fill="both", expand=True, padx=2, pady=2)
    logo=ctk.CTkFrame(frame, width=64, height=64, corner_radius=14, fg_color=BG); logo.pack(pady=(31, 12)); logo.pack_propagate(False)
    app_logo=tk.Canvas(logo,width=64,height=64,bg=BG,highlightthickness=0,bd=0); app_logo.pack()
    app_logo.create_polygon(6,22,33,4,33,49,19,61,4,61,19,48,19,23,fill="#A33BFF",outline="#A33BFF")
    app_logo.create_polygon(37,11,53,22,53,48,64,48,53,61,37,61,fill="#16BFEA",outline="#16BFEA")
    app_logo.create_polygon(33,4,37,11,37,61,33,57,fill="#5638E8",outline="#5638E8")
    ctk.CTkLabel(frame, text="JIGARZON", font=("Segoe UI", 24, "bold"), text_color=TEXT).pack()
    ctk.CTkLabel(frame, text="A better way into your next world.", font=("Segoe UI", 11), text_color=MUTED).pack(pady=(3, 24))
    bar=ctk.CTkProgressBar(frame, width=390, height=8, corner_radius=8, progress_color=PURPLE, fg_color=ALT); bar.pack(pady=(0, 13)); bar.set(.04)
    label=ctk.CTkLabel(frame, text="Starting Jigarzon…", font=("Segoe UI", 10), text_color=MUTED); label.pack()
    app=Jigarzon(root)
    app.set_window_icon(splash)
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
