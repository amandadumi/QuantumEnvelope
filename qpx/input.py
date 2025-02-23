from .types import *

def load_integrals(fcidump_path) -> Tuple[int, float, One_electron_integral, Two_electron_integral]:
    """Read all the Hamiltonian integrals from the data file.
    Returns: (E0, d_one_e_integral, d_two_e_integral).
    E0 : a float containing the nuclear repulsion energy (V_nn),
    d_one_e_integral : a dictionary of one-electron integrals,
    d_two_e_integral : a dictionary of two-electron integrals.
    """
    import glob

    if len(glob.glob(fcidump_path)) == 1:
        fcidump_path = glob.glob(fcidump_path)[0]
    elif len(glob.glob(fcidump_path)) == 0:
        print("no matching fcidump file")
    else:
        print(f"multiple matches for {fcidump_path}")
        for i in glob.glob(fcidump_path):
            print(i)

    # Use an iterator to avoid storing everything in memory twice.
    if fcidump_path.split(".")[-1] == "gz":
        import gzip

        f = gzip.open(fcidump_path)
    elif fcidump_path.split(".")[-1] == "bz2":
        import bz2

        f = bz2.open(fcidump_path)
    else:
        f = open(fcidump_path)

    # Only non-zero integrals are stored in the fci_dump.
    # Hence we use a defaultdict to handle the sparsity
    n_orb = int(next(f).split()[2])

    for _ in range(3):
        next(f)

    from collections import defaultdict

    d_one_e_integral = defaultdict(int)
    d_two_e_integral = defaultdict(int)

    for line in f:
        v, *l = line.split()
        v = float(v)
        # Transform from Mulliken (ik|jl) to Dirac's <ij|kl> notation
        # (swap indices)
        i, k, j, l = list(map(int, l))

        if i == 0:
            E0 = v
        elif j == 0:
            # One-electron integrals are symmetric (when real, not complex)
            d_one_e_integral[(i, k)] = v
            d_one_e_integral[(k, i)] = v
        else:
            # Two-electron integrals have many permutation symmetries:
            # Exchange r1 and r2 (indices i,k and j,l)
            # Exchange i,k
            # Exchange j,l
            d_two_e_integral[(i, j, k, l)] = v
            d_two_e_integral[(i, l, k, j)] = v
            d_two_e_integral[(j, i, l, k)] = v
            d_two_e_integral[(j, k, l, i)] = v
            d_two_e_integral[(k, j, i, l)] = v
            d_two_e_integral[(k, l, i, j)] = v
            d_two_e_integral[(l, i, j, k)] = v
            d_two_e_integral[(l, k, j, i)] = v

    f.close()

    return n_orb, E0, d_one_e_integral, d_two_e_integral


def load_wf(path_wf) -> Tuple[List[float], List[Determinant]]:
    """Read the input file :
    Representation of the Slater determinants (basis) and
    vector of coefficients in this basis (wave function)."""

    import glob

    if len(glob.glob(path_wf)) == 1:
        path_wf = glob.glob(path_wf)[0]
    elif len(glob.glob(path_wf)) == 0:
        print(f"no matching wf file: {path_wf}")
    else:
        print(f"multiple matches for {path_wf}")
        for i in glob.glob(path_wf):
            print(i)

    if path_wf.split(".")[-1] == "gz":
        import gzip

        with gzip.open(path_wf) as f:
            data = f.read().decode().split()
    elif path_wf.split(".")[-1] == "bz2":
        import bz2

        with bz2.open(path_wf) as f:
            data = f.read().decode().split()
    else:
        with open(path_wf) as f:
            data = f.read().split()

    def decode_det(str_):
        for i, v in enumerate(str_, start=1):
            if v == "+":
                yield i

    def grouper(iterable, n):
        "Collect data into fixed-length chunks or blocks"
        args = [iter(iterable)] * n
        return zip(*args)

    det = []
    psi_coef = []
    for (coef, det_i, det_j) in grouper(data, 3):
        psi_coef.append(float(coef))
        det.append(Determinant(tuple(decode_det(det_i)), tuple(decode_det(det_j))))

    # Normalize psi_coef
    from math import sqrt

    norm = sqrt(sum(c * c for c in psi_coef))
    psi_coef = [c / norm for c in psi_coef]

    return psi_coef, det


def load_eref(path_ref) -> float:
    """Read the input file :
    Representation of the Slater determinants (basis) and
    vector of coefficients in this basis (wave function)."""

    import glob

    if len(glob.glob(path_ref)) == 1:
        path_ref = glob.glob(path_ref)[0]
    elif len(glob.glob(path_ref)) == 0:
        print(f"no matching ref file: {path_ref}")
    else:
        print(f"multiple matches for {path_ref}")
        for i in glob.glob(path_ref):
            print(i)

    if path_ref.split(".")[-1] == "gz":
        import gzip

        with gzip.open(path_ref) as f:
            data = f.read().decode()
    elif path_ref.split(".")[-1] == "bz2":
        import bz2

        with bz2.open(path_ref) as f:
            data = f.read().decode()
    else:
        with open(path_ref) as f:
            data = f.read()

    import re

    return float(re.search(r"E +=.+", data).group(0).strip().split()[-1])

def save_wf(psi_coef: List[float], psi_det: List[Determinant], wfpath: str, n_orb: int):
    """
    write wf to file with dets in +/- format
    """

    assert (len(psi_coef) == len(psi_det))

    def encode_det(det: Determinant):
        """
        input: Determinant
        output: tuple of +/- strings (one for each spindet)
        """
        return tuple(map(encode_spindet,det))

    def encode_spindet(spindet: Spin_determinant):
        """
        translate a Spin_determinant to a +/- string representation
        """
        return ''.join( ('+' if i in spindet else '-') for i in range(1,max(spindet)+1))

    with open(wfpath,'w') as outfile:
        for ci,di in zip(psi_coef, psi_det):
            outfile.write(f'{ci}\n')
            for spindet in encode_det(di):
                outfile.write(spindet.ljust(n_orb,'-')+'\n')
    return
