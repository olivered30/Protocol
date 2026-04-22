# ─────────────────────────────────────────────────────────────────────────────
# netMHCpan 4.2c — Interactive Script
# https://github.com/olivered30/Protocol/tree/main/NetMHC
# ─────────────────────────────────────────────────────────────────────────────

import matplotlib.pyplot as plt
from netmhcpan import (
    run_netmhcpan, generate_subpeptides,
    parse_xls, filter_binders, summary_table,
    launch_input_dialog, ask_save_path,
)

INSTALL_DIR = "/Users/linz3/tools/netMHCpan-4.2c"   # ← edit this
STRONG_RANK = 0.5
WEAK_RANK   = 2.0

inputs = launch_input_dialog(
    default_alleles=["HLA-A11:01", "HLA-A11:02", "HLA-A03:01"],
    default_lengths=[9, 10],
)

if inputs is None:
    print("Cancelled.")
else:
    alleles  = inputs["alleles"]
    lengths  = inputs["lengths"]
    mode     = inputs["mode"]
    sequence = inputs["sequence"]

    print(f"Alleles : {alleles}")
    print(f"Lengths : {lengths}")
    print(f"Mode    : {mode}")

    if mode == "peptide":
        source   = [p.strip() for p in sequence.splitlines() if p.strip()]
        expanded = generate_subpeptides(source, lengths)
        print(f"Source peptides : {len(source)}  ->  expanded: {len(expanded)}")
        run_input, is_pep = "\n".join(expanded), True
    else:
        run_input, is_pep = sequence, False

    print("\nRunning netMHCpan...")
    raw = run_netmhcpan(run_input, alleles, lengths, INSTALL_DIR,
                        is_peptide_list=is_pep)
    df  = parse_xls(raw, strong_rank=STRONG_RANK, weak_rank=WEAK_RANK)
    print(f"Parsed {len(df)} predictions across {df['HLA'].nunique()} alleles.")

    print("\nAll predictions:")
    print(df.to_string())

    df_binders = filter_binders(df)
    print(f"\nBinders: {len(df_binders)}  "
          f"(Strong: {(df_binders['Binder']=='Strong').sum()}, "
          f"Weak: {(df_binders['Binder']=='Weak').sum()})")
    print(df_binders[["Peptide","HLA","EL_rank","Binder"]].to_string())

    summ = summary_table(df)
    print("\nBinders per allele:")
    print(summ.to_string())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    if not summ.empty:
        cols = [c for c in ["Strong","Weak"] if c in summ.columns]
        summ.set_index("HLA")[cols].plot(kind="bar", ax=axes[0],
                                          color=["#e24b4a","#378add"][:len(cols)])
    axes[0].set_title("Binders per HLA allele")
    axes[0].set_ylabel("Count")
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].legend(title="Binder class")

    colors = {"Strong":"#e24b4a","Weak":"#378add","Non-binder":"#cccccc"}
    for allele in alleles:
        sub = df[df["HLA"]==allele]
        axes[1].scatter(sub["EL_rank"], [alleles.index(allele)]*len(sub),
                        c=[colors[b] for b in sub["Binder"]], alpha=0.8, s=80)
    axes[1].set_yticks(range(len(alleles)))
    axes[1].set_yticklabels(alleles)
    axes[1].axvline(STRONG_RANK, color="red",    linestyle="--", lw=1, label=f"Strong <={STRONG_RANK}%")
    axes[1].axvline(WEAK_RANK,   color="orange", linestyle="--", lw=1, label=f"Weak <={WEAK_RANK}%")
    axes[1].set_title("EL_rank per peptide")
    axes[1].set_xlabel("EL_rank (%)")
    axes[1].legend(fontsize=8)
    plt.tight_layout()
    plt.show()

    print("\nChoose where to save results...")
    path_all = ask_save_path("netmhcpan_all.csv")
    if path_all:
        df.to_csv(path_all, index=False)
        print(f"Saved all predictions -> {path_all}")

    path_binders = ask_save_path("netmhcpan_binders.csv")
    if path_binders:
        df_binders.to_csv(path_binders, index=False)
        print(f"Saved binders        -> {path_binders}")
