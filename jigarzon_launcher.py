import json, os, queue, shutil, subprocess, threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP="Jigarzon Launcher"; BG="#101116"; PANEL="#191b24"; ALT="#222532"; FG="#f3f4f8"; MUTED="#a2a7b6"; PURPLE="#a855f7"; GREEN="#4ade80"
def cfg():
 p=Path(os.getenv("APPDATA",Path.home()))/"JigarzonLauncher"; p.mkdir(parents=True,exist_ok=True); return p/"settings.json"
def load():
 try:return json.loads(cfg().read_text(encoding="utf-8"))
 except Exception:return {}

class Launcher:
 def __init__(self,root):
  self.root=root; root.title(APP); root.geometry("900x620"); root.minsize(780,560); root.configure(bg=BG)
  s=load(); self.exe=tk.StringVar(value=s.get("horizon_path","")); self.version=tk.StringVar(value=s.get("version","")); self.status=tk.StringVar(value="Select horizon-launcher.exe to begin.")
  self.q=queue.Queue(); self.busy=False; self.build(); self.find_horizon(); root.after(120,self.poll)
 def label(self,p,t,n=10,c=FG,b=False):return tk.Label(p,text=t,bg=p.cget("bg"),fg=c,font=("Segoe UI",n,"bold" if b else "normal"))
 def button(self,p,t,fn,primary=False):return tk.Button(p,text=t,command=fn,cursor="hand2",bg=PURPLE if primary else ALT,fg="white",activebackground="#9333ea",activeforeground="white",relief="flat",bd=0,padx=14,pady=10,font=("Segoe UI",9,"bold"))
 def build(self):
  h=tk.Frame(self.root,bg=BG); h.pack(fill="x",padx=28,pady=(22,14))
  tk.Label(h,text="J",bg=PURPLE,fg="white",font=("Segoe UI",20,"bold"),width=2).pack(side="left",padx=(0,12))
  t=tk.Frame(h,bg=BG); t.pack(side="left"); self.label(t,"JIGARZON",18,FG,True).pack(anchor="w"); self.label(t,"LAUNCHER",8,MUTED,True).pack(anchor="w")
  self.label(h,"HORIZON MC  /  RUST EDITION",9,MUTED,True).pack(side="right",pady=12)
  hero=tk.Frame(self.root,bg=PANEL,highlightthickness=1,highlightbackground="#2b2e3b"); hero.pack(fill="x",padx=28,pady=8)
  self.label(hero,"MINECRAFT: JAVA EDITION 26.3",9,PURPLE,True).pack(anchor="w",padx=22,pady=(20,4))
  self.label(hero,"Your world. Your way.",24,FG,True).pack(anchor="w",padx=22)
  self.label(hero,"Manage Horizon builds and start the Rust-powered Minecraft client.",10,MUTED).pack(anchor="w",padx=22,pady=(4,20))
  body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True,padx=28,pady=10)
  left=tk.Frame(body,bg=PANEL,highlightthickness=1,highlightbackground="#2b2e3b"); left.pack(side="left",fill="both",expand=True,padx=(0,10))
  right=tk.Frame(body,bg=PANEL,width=260,highlightthickness=1,highlightbackground="#2b2e3b"); right.pack(side="right",fill="y"); right.pack_propagate(False)
  self.label(left,"HORIZON INSTALLATION",9,MUTED,True).pack(anchor="w",padx=18,pady=(18,8))
  row=tk.Frame(left,bg=PANEL); row.pack(fill="x",padx=18)
  tk.Entry(row,textvariable=self.exe,bg=ALT,fg=FG,insertbackground=FG,relief="flat",font=("Segoe UI",9)).pack(side="left",fill="x",expand=True,ipady=9,padx=(0,8))
  self.button(row,"Browse",self.browse).pack(side="right")
  self.label(left,"Choose horizon-launcher.exe from your Horizon installation.",8,MUTED).pack(anchor="w",padx=18,pady=(6,16))
  self.label(left,"AVAILABLE BUILDS",9,MUTED,True).pack(anchor="w",padx=18,pady=(3,8))
  self.versions=ttk.Combobox(left,textvariable=self.version,state="readonly"); self.versions.pack(fill="x",padx=18,ipady=5)
  row2=tk.Frame(left,bg=PANEL); row2.pack(fill="x",padx=18,pady=12)
  self.button(row2,"Refresh builds",self.refresh).pack(side="left"); self.button(row2,"Install latest",self.install).pack(side="left",padx=8); self.button(row2,"Prepare files",self.prepare).pack(side="left")
  self.label(left,"ACTIVITY",9,MUTED,True).pack(anchor="w",padx=18,pady=(12,6))
  self.log=tk.Text(left,height=7,bg="#12141b",fg="#cbd0dc",relief="flat",font=("Consolas",8),wrap="word"); self.log.pack(fill="both",expand=True,padx=18,pady=(0,18)); self.log.insert("end","Jigarzon Launcher ready.\n")
  self.label(right,"PLAY",9,MUTED,True).pack(anchor="w",padx=18,pady=(20,12))
  self.label(right,"Ready to\nstart playing?",20,FG,True).pack(anchor="w",padx=18)
  self.label(right,"Choose an installed Horizon build, then launch Minecraft.",9,MUTED).pack(anchor="w",padx=18,pady=(8,18))
  self.button(right,"▶  PLAY MINECRAFT",self.play,True).pack(fill="x",padx=18)
  self.button(right,"Sign in to Microsoft",self.signin).pack(fill="x",padx=18,pady=(9,0))
  tk.Frame(right,bg="#303442",height=1).pack(fill="x",padx=18,pady=18)
  self.label(right,"STATUS",8,MUTED,True).pack(anchor="w",padx=18)
  tk.Label(right,textvariable=self.status,bg=PANEL,fg=GREEN,justify="left",wraplength=220,font=("Segoe UI",9)).pack(anchor="w",padx=18,pady=(7,0))
  foot=tk.Frame(self.root,bg=BG); foot.pack(fill="x",padx=28,pady=(0,14))
  self.label(foot,"Jigarzon Launcher",8,MUTED).pack(side="left"); self.label(foot,"Independent project • Not affiliated with Mojang or Microsoft",8,MUTED).pack(side="right")
 def find_horizon(self):
  for p in [shutil.which("horizon-launcher.exe"),str(Path(os.getenv("LOCALAPPDATA",""))/"Programs/Horizon/horizon-launcher.exe"),str(Path(os.getenv("LOCALAPPDATA",""))/"Horizon/horizon-launcher.exe")]:
   if p and Path(p).is_file(): self.exe.set(p); break
 def browse(self):
  p=filedialog.askopenfilename(filetypes=[("Horizon launcher","horizon-launcher.exe"),("Programs","*.exe")])
  if p:self.exe.set(p); self.save(); self.refresh()
 def save(self):
  cfg().write_text(json.dumps({"horizon_path":self.exe.get(),"version":self.version.get()},indent=2),encoding="utf-8")
 def run(self,args,label,callback=None):
  if self.busy:return
  p=Path(self.exe.get().strip())
  if not p.is_file():messagebox.showerror(APP,"Select the Horizon horizon-launcher.exe file first.");return
  self.busy=True; self.save(); self.q.put(("status",label)); self.q.put(("log","> "+p.name+" "+" ".join(args)))
  def work():
   try:
    r=subprocess.run([str(p)]+args,cwd=str(p.parent),capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=1800)
    out=(r.stdout or "")+(r.stderr or "")
    if out.strip():self.q.put(("log",out.strip()))
    self.q.put(("status",label+" complete." if r.returncode==0 else "Command failed. Check activity output."))
    if r.returncode==0 and callback:callback(out)
   except Exception as e:self.q.put(("log",str(e)));self.q.put(("status","Could not run Horizon command."))
   finally:self.q.put(("busy",False))
  threading.Thread(target=work,daemon=True).start()
 def refresh(self):
  def done(out):
   try:
    d=json.loads(out); raw=d.get("versions",d.get("installed",[])) if isinstance(d,dict) else []
    vals=[x if isinstance(x,str) else x.get("tag",x.get("version",x.get("name",""))) for x in raw]
    vals=[x for x in vals if x]
    if vals:self.q.put(("versions",vals))
    else:self.q.put(("log","No installed builds were returned."))
   except Exception:self.q.put(("log","Could not parse the installed build list."))
  self.run(["versions","--installed","--json"],"Refreshing installed builds",done)
 def install(self):self.run(["install","latest"],"Installing latest Horizon build",lambda _:self.refresh())
 def prepare(self):self.run(["prepare"],"Preparing Minecraft files")
 def signin(self):self.run(["account","sign-in"],"Starting Microsoft sign-in")
 def play(self):
  v=self.version.get().strip()
  if not v:messagebox.showwarning(APP,"Refresh builds and select an installed build first.");return
  self.run(["play","--version",v],f"Playing Minecraft {v} using Jigarzon Launcher")
 def poll(self):
  try:
   while True:
    k,v=self.q.get_nowait()
    if k=="log":self.log.insert("end",v+"\n");self.log.see("end")
    elif k=="status":self.status.set(v)
    elif k=="busy":self.busy=v
    elif k=="versions":
     self.versions["values"]=v
     if v and self.version.get() not in v:self.version.set(v[0])
     self.save()
  except queue.Empty:pass
  self.root.after(120,self.poll)

if __name__=="__main__":
 root=tk.Tk(); Launcher(root); root.mainloop()
