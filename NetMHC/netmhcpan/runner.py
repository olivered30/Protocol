import subprocess, tempfile, os, platform

def _get_binary(install_dir):
    system = platform.system()
    arch   = platform.machine()
    path   = os.path.join(install_dir, f"{system}_{arch}", "bin", "netMHCpan-4.2")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Binary not found: {path}\n"
            f"Make sure you downloaded the {system}_{arch} build from DTU."
        )
    os.chmod(path, 0o755)
    return path

def _make_env(install_dir):
    env = os.environ.copy()
    env["NETMHCpan"] = install_dir
    env["TMPDIR"]    = "/tmp"
    return env

def run_netmhcpan(input_str, alleles, lengths, install_dir,
                  is_peptide_list=False, binding_affinity=False):
    """
    Run netMHCpan 4.2c and return raw XLS output as a string.

    Parameters
    ----------
    input_str        : str   FASTA string or newline-separated peptide list
    alleles          : list  HLA alleles e.g. ['HLA-A11:01'] — no asterisk
    lengths          : list  Peptide lengths e.g. [9, 10]
    install_dir      : str   Path to netMHCpan install dir
    is_peptide_list  : bool  True → peptide input; False → FASTA input
    binding_affinity : bool  True → also predict IC50 affinity (-BA flag)
    """
    real_bin   = _get_binary(install_dir)
    env        = _make_env(install_dir)
    allele_str = ",".join(alleles)
    length_str = ",".join(str(l) for l in lengths)

    suffix  = ".pep" if is_peptide_list else ".fasta"
    inp_tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    inp_tmp.write(input_str)
    inp_tmp.close()

    xls_tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
    xls_tmp.close()

    cmd = [real_bin, "-a", allele_str, "-l", length_str,
           "-xls", "-xlsfile", xls_tmp.name]
    cmd += ["-p", inp_tmp.name] if is_peptide_list else ["-f", inp_tmp.name]
    if binding_affinity:
        cmd += ["-BA"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    os.unlink(inp_tmp.name)

    if result.returncode != 0:
        os.unlink(xls_tmp.name)
        raise RuntimeError(
            f"netMHCpan failed (exit {result.returncode})\n"
            f"STDOUT: {result.stdout[-2000:]}\nSTDERR: {result.stderr}"
        )
    with open(xls_tmp.name) as f:
        content = f.read()
    os.unlink(xls_tmp.name)
    return content

def generate_subpeptides(peptides, lengths):
    """Expand peptides into all overlapping sub-sequences of given lengths."""
    seen, result = set(), []
    min_len = min(lengths)
    for pep in peptides:
        if len(pep) < min_len:
            print(f"  Skipping '{pep}' — shorter than min length {min_len}")
            continue
        for L in lengths:
            for i in range(len(pep) - L + 1):
                sub = pep[i:i+L]
                if sub not in seen:
                    seen.add(sub)
                    result.append(sub)
    return result

def list_alleles(install_dir):
    """Return all HLA alleles supported by this netMHCpan installation."""
    real_bin = _get_binary(install_dir)
    env      = _make_env(install_dir)
    r = subprocess.run([real_bin, "-listMHC"], capture_output=True, text=True, env=env)
    return [l.strip() for l in r.stdout.splitlines()
            if l.strip().startswith(("HLA", "H-2"))]
