"""
macOS-safe dialogs using subprocess + osascript (AppleScript).
No tkinter threading — avoids NSWindow main-thread crash in Spyder.
"""
import subprocess, json, sys, textwrap

def launch_input_dialog(default_alleles=None, default_lengths=None):
    """
    Show the netMHCpan input dialog in a separate Python process.
    Returns dict with keys: alleles, lengths, mode, sequence
    Returns None if cancelled.
    """
    default_alleles = default_alleles or ["HLA-A11:01", "HLA-A11:02", "HLA-A03:01"]
    default_lengths = default_lengths or [9, 10]
    allele_default  = ",".join(default_alleles)
    length_default  = ",".join(str(l) for l in default_lengths)

    code = textwrap.dedent(f"""
import tkinter as tk
from tkinter import messagebox
import json

result = {{}}
root = tk.Tk()
root.title("netMHCpan Input")
root.resizable(False, False)
root.lift()
root.attributes("-topmost", True)
root.focus_force()
pad = dict(padx=10, pady=5)

tk.Label(root, text="HLA Alleles", font=("Helvetica",11,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",**pad)
tk.Label(root, text="Comma-separated, no asterisk — e.g. HLA-A11:01,HLA-A03:01", fg="gray").grid(row=1,column=0,columnspan=2,sticky="w",padx=10)
allele_var = tk.StringVar(value="{allele_default}")
tk.Entry(root, textvariable=allele_var, width=52).grid(row=2,column=0,columnspan=2,**pad)

tk.Label(root, text="Peptide Lengths", font=("Helvetica",11,"bold")).grid(row=3,column=0,columnspan=2,sticky="w",**pad)
tk.Label(root, text="Comma-separated, e.g. 9,10", fg="gray").grid(row=4,column=0,columnspan=2,sticky="w",padx=10)
length_var = tk.StringVar(value="{length_default}")
tk.Entry(root, textvariable=length_var, width=20).grid(row=5,column=0,columnspan=2,sticky="w",**pad)

tk.Label(root, text="Input Mode", font=("Helvetica",11,"bold")).grid(row=6,column=0,columnspan=2,sticky="w",**pad)
mode_var = tk.StringVar(value="peptide")
tk.Radiobutton(root, text="Peptide list  (one per line — auto-expands to chosen lengths)", variable=mode_var, value="peptide").grid(row=7,column=0,columnspan=2,sticky="w",padx=10)
tk.Radiobutton(root, text="Full protein  (FASTA format — netMHCpan does sliding window)", variable=mode_var, value="fasta").grid(row=8,column=0,columnspan=2,sticky="w",padx=10)

tk.Label(root, text="Sequence Input", font=("Helvetica",11,"bold")).grid(row=9,column=0,columnspan=2,sticky="w",**pad)
tk.Label(root, text="Peptides: one per line  |  FASTA: include >header line", fg="gray").grid(row=10,column=0,columnspan=2,sticky="w",padx=10)
seq_box = tk.Text(root, width=60, height=10, font=("Courier",10))
seq_box.grid(row=11,column=0,columnspan=2,**pad)
sb = tk.Scrollbar(root, command=seq_box.yview)
sb.grid(row=11,column=2,sticky="ns",pady=5)
seq_box.config(yscrollcommand=sb.set)

def on_run():
    a = [x.strip() for x in allele_var.get().split(",") if x.strip()]
    l = [int(x.strip()) for x in length_var.get().split(",") if x.strip().isdigit()]
    s = seq_box.get("1.0", tk.END).strip()
    if not a: messagebox.showerror("Error","Please enter at least one HLA allele."); return
    if not l: messagebox.showerror("Error","Please enter at least one peptide length."); return
    if not s: messagebox.showerror("Error","Please enter a sequence."); return
    if mode_var.get()=="fasta" and not s.startswith(">"): messagebox.showerror("Error","FASTA must start with >header."); return
    result.update({{"alleles":a,"lengths":l,"mode":mode_var.get(),"sequence":s}})
    root.destroy()

def on_cancel():
    root.destroy()

bf = tk.Frame(root)
bf.grid(row=12,column=0,columnspan=2,pady=10)
tk.Button(bf,text="Run netMHCpan",command=on_run,bg="#378add",fg="white",font=("Helvetica",11,"bold"),padx=10).pack(side="left",padx=5)
tk.Button(bf,text="Cancel",command=on_cancel,padx=10).pack(side="left",padx=5)
root.mainloop()
print(json.dumps(result))
""")

    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    out  = proc.stdout.strip()
    if not out:
        return None
    data = json.loads(out)
    return data if data else None


def ask_save_path(default_name):
    """
    Native macOS save dialog via osascript — no tkinter, no threading.
    Returns chosen path string, or None if cancelled.
    """
    script = (
        f'set f to choose file name with prompt "Save {default_name}" '
        f'default name "{default_name}"\nreturn POSIX path of f'
    )
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    path = r.stdout.strip()
    return path if path else None
