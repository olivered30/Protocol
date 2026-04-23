# NetMHC — netMHCpan 4.2c Python Wrapper

Interactive Python wrapper for **netMHCpan 4.2c** with GUI dialogs.
Designed for Spyder on macOS (Apple Silicon & Intel) and Linux.

> **netMHCpan license**: Free for academic use only —
> do not redistribute the binaries.
> Download from: https://services.healthtech.dtu.dk/services/NetMHCpan-4.1/

---

## Requirements

- Python ≥ 3.8
- pandas, matplotlib (installed via `requirements.txt`)
- netMHCpan 4.2c binary (downloaded separately from DTU — see Step 3)
- macOS: tcsh (`brew install tcsh` if missing)

---

## Installation & Setup

### Step 1 — Clone this repo

```bash
git clone https://github.com/olivered30/Protocol.git
cd Protocol/NetMHC
```

### Step 2 — Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3 — Download netMHCpan 4.2c from DTU

Go to: https://services.healthtech.dtu.dk/services/NetMHCpan-4.1/

Download the correct build for your computer:

| Computer | Download |
|---|---|
| Mac Apple Silicon (M1/M2/M3) | Version 4.2c → Darwin_arm64 |
| Mac Intel | Version 4.2c → Darwin_x86_64 |
| Linux | Version 4.2c → Linux |

Extract it:

```bash
tar -xvf netMHCpan-4.2c.Darwin_arm64.tar.gz -C ~/tools/

# Rename if the folder has a space (common issue)
mv ~/tools/"netMHCpan-4.2 2" ~/tools/netMHCpan-4.2c
```

### Step 4 — Set up netMHCpan (run once in Python)

```python
import os, shutil

install_dir = "/Users/yourname/tools/netMHCpan-4.2c"  # ← change to your path
bin_path    = os.path.join(install_dir, "netMHCpan")

# Patch internal NMHOME path
with open(bin_path) as f:
    lines = f.readlines()
lines[13] = f"setenv\tNMHOME\t{install_dir}\n"
with open(bin_path, "w") as f:
    f.writelines(lines)

# Fix tcsh glob issue
with open(bin_path) as f:
    content = f.read()
content = content.replace(
    '$NETMHCpan/bin/netMHCpan-4.2',
    '"$NETMHCpan/bin/netMHCpan-4.2"'
)
with open(bin_path, "w") as f:
    f.write(content)

# Copy platform binaries into bin/
# Change 'Darwin_arm64' to 'Darwin_x86_64' or 'Linux_x86_64' if needed
src = os.path.join(install_dir, "Darwin_arm64", "bin")
dst = os.path.join(install_dir, "bin")
os.makedirs(dst, exist_ok=True)
for fname in os.listdir(src):
    shutil.copy2(os.path.join(src, fname), os.path.join(dst, fname))
    os.chmod(os.path.join(dst, fname), 0o755)

print("Setup complete.")
```

### Step 5 — Edit the two paths in run_netmhcpan.py

Open `run_netmhcpan.py` and update these two lines to match your username
and install location:

```python
# Line ~6 — path to the NetMHC folder
sys.path.insert(0, "/Users/yourname/Protocol/NetMHC")   # ← change this

# Line ~14 — path to netMHCpan install
INSTALL_DIR = "/Users/yourname/tools/netMHCpan-4.2c"    # ← change this
```

### Step 6 — Run

Open `run_netmhcpan.py` in Spyder and press **F5**, or in Terminal:

```bash
python3 /Users/yourname/Protocol/NetMHC/run_netmhcpan.py
```

A dialog box will appear asking for:
- HLA alleles (e.g. `HLA-A11:01, HLA-A03:01`) — **no asterisk**
- Peptide lengths (e.g. `9, 10`)
- Input mode: peptide list or full protein FASTA
- Sequence input

Results are printed in the console, plotted in the Plots pane, and two
save dialogs let you export CSVs anywhere you like.

---

## Allele name format

Use `HLA-A02:01` format — **no asterisk**.
To see all supported alleles for your installation:

```python
from netmhcpan import list_alleles
alleles = list_alleles("/Users/yourname/tools/netMHCpan-4.2c")
print(alleles[:20])
```

---

## Use in your own script

```python
from netmhcpan import run_netmhcpan, parse_xls, filter_binders, summary_table

INSTALL_DIR = "/Users/yourname/tools/netMHCpan-4.2c"

# Peptide list
peptides = "GILGFVFTL\nNLVPMVATV\nYVLDHLIVV"
raw = run_netmhcpan(peptides, ["HLA-A02:01", "HLA-B07:02"],
                    lengths=[9], install_dir=INSTALL_DIR,
                    is_peptide_list=True)
df = parse_xls(raw)
print(filter_binders(df))
print(summary_table(df))

# Full protein FASTA
fasta = ">MyProtein\nMKTAYIAKQRQISFVK..."
raw = run_netmhcpan(fasta, ["HLA-A02:01"], lengths=[9, 10],
                    install_dir=INSTALL_DIR)
df = parse_xls(raw)
```

---

## Output columns

| Column | Description |
|---|---|
| `Pos` | Position in protein sequence |
| `Peptide` | Peptide sequence |
| `ID` | Protein / sequence ID |
| `HLA` | HLA allele |
| `core` | MHC-binding core |
| `icore` | Interaction core |
| `EL_score` | Eluted ligand score (higher = stronger) |
| `EL_rank` | %Rank EL — lower = stronger binder |
| `Binder` | `Strong` (≤0.5%), `Weak` (≤2.0%), or `Non-binder` |

---

## File structure

```
Protocol/NetMHC/
├── README.md
├── requirements.txt
├── .gitignore
├── run_netmhcpan.py        ← main interactive script
└── netmhcpan/
    ├── __init__.py
    ├── runner.py           ← binary caller + subpeptide expansion
    ├── parser.py           ← XLS parser, filter, summary
    └── dialog.py           ← GUI input dialog + save dialog
```

---

## License

Wrapper code: MIT
netMHCpan: Academic use only — do not redistribute the DTU binaries.
