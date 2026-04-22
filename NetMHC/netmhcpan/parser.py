import pandas as pd

def parse_xls(raw, strong_rank=0.5, weak_rank=2.0):
    """
    Parse raw XLS output from netMHCpan 4.2c into a tidy DataFrame.
    Adds a 'Binder' column: Strong / Weak / Non-binder.
    """
    lines = [l for l in raw.splitlines() if l.strip() and not l.startswith("#")]
    if len(lines) < 3:
        raise ValueError("XLS output too short — check netMHCpan ran correctly.")

    allele_row    = lines[0].split("\t")
    alleles_found = [(i, v.strip()) for i, v in enumerate(allele_row)
                     if v.strip().startswith(("HLA", "H-2"))]
    if not alleles_found:
        raise ValueError("No allele names found in XLS header.")

    col_row = lines[1].split("\t")
    has_ba  = any("BA" in c for c in col_row)

    records = []
    for line in lines[2:]:
        vals = line.split("\t")
        if not vals or not vals[0].strip().lstrip("-").isdigit():
            continue
        for allele_idx, allele_name in alleles_found:
            try:
                el_score = float(vals[allele_idx + 2].strip())
                el_rank  = float(vals[allele_idx + 3].strip())
            except (IndexError, ValueError):
                continue
            rec = {
                "Pos":      vals[0].strip(),
                "Peptide":  vals[1].strip(),
                "ID":       vals[2].strip(),
                "HLA":      allele_name,
                "core":     vals[allele_idx].strip(),
                "icore":    vals[allele_idx + 1].strip(),
                "EL_score": el_score,
                "EL_rank":  el_rank,
            }
            if has_ba:
                try:
                    rec["BA_score"] = float(vals[allele_idx + 4].strip())
                    rec["BA_rank"]  = float(vals[allele_idx + 5].strip())
                except (IndexError, ValueError):
                    rec["BA_score"] = rec["BA_rank"] = None
            records.append(rec)

    if not records:
        raise ValueError("No data rows parsed.")

    df = pd.DataFrame(records)
    df["EL_rank"] = pd.to_numeric(df["EL_rank"], errors="coerce")
    df["Binder"]  = "Non-binder"
    df.loc[df["EL_rank"] <= weak_rank,   "Binder"] = "Weak"
    df.loc[df["EL_rank"] <= strong_rank, "Binder"] = "Strong"
    return df

def filter_binders(df, include_weak=True):
    """Return strong (and optionally weak) binders sorted by EL_rank."""
    levels = ["Strong", "Weak"] if include_weak else ["Strong"]
    return df[df["Binder"].isin(levels)].sort_values("EL_rank").reset_index(drop=True)

def summary_table(df):
    """Return binder counts grouped by HLA allele and binder class."""
    return (
        df[df["Binder"] != "Non-binder"]
        .groupby(["HLA", "Binder"]).size()
        .unstack(fill_value=0)
        .reset_index()
    )
