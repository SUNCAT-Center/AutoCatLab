import os
import shutil
import subprocess
import pandas as pd
import numpy as np
import spglib
import yaml
from ase.io import read, write
from mendeleev import element
from yaml import Loader
from pathlib import Path

from ase.data import covalent_radii as cradii
import pkgutil
import pkg_resources

from .rapidos import RapiDOS

# Use Path to locate the YAML file within the installed package
yaml_path = Path(__file__).parent / 'valence_orbital_mapping.yaml'
with open(yaml_path, 'r') as f:
    orbital_map = yaml.safe_load(f)


def get_initial_magmoms(atoms):
    # Guess spin on each atom based on number of outer electrons
    # What about AFM combinations? Need to check all symmetries?
    high_spin_elements = ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe',
                          'Y', 'Zr', 'Nb',
                          'Hf', 'Ta']
    low_spin_elements = ['Co', 'Ni',
                         'Mo', 'Tc', 'Ru',
                         'W', 'Re', 'Os', 'Ir']

    # Assumin 2tg-eg splitting (octahedral field)
    low_spin_function = np.array([0, 1, 2, 3, 2, 1, 0, 1, 2, 1, 0])
    high_spin_function = np.array([0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0])

    # Whether Co is high or low spin depends on oxidation state?

    N_oxygen = list(atoms.symbols).count('O')
    # N_H = list(atoms.symbols).count('H') # add more species later
    N_metal = len(atoms) - N_oxygen
    average_ox = N_oxygen / N_metal * 2
    initial_magmoms = []
    for a in atoms:
        if a.symbol == 'O':
            mag = 0
        else:
            ele = element(a.symbol)
            group = int(ele.group_id)
            period = int(ele.period)
            if group > 1:
                N_d = int(group - average_ox)  # Number of d electrons
            else:
                N_d = 0
            if a.symbol in high_spin_elements:
                mag = high_spin_function[N_d]
            elif a.symbol in low_spin_elements:
                mag = low_spin_function[N_d]
            else:
                mag = 0

        mag += 0.01  # break symmetry
        initial_magmoms += [mag]

    return initial_magmoms


# def get_spin_state(symbol):
#    high_spin_elements = {1: ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co'],
#                          2: ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co'],
#                          3: ['Ti', 'V', 'Cr', 'Mn', 'Fe'],
#                          4: ['V', 'Cr', 'Mn', 'Fe']
#                          4: ['V', 'Cr', 'Mn', 'Fe']
#                          }


def get_kpoints(atoms, effective_length=25, bulk=True):
    """Return a tuple of k-points derived from the unit cell.

        Parameters
        ----------
        atoms : object
        effective_length : k-point*unit-cell-parameter
        bulk : Whether it is a bulk system. If not nkz = 1
    """
    l = effective_length
    cell = atoms.get_cell()
    # print(np.linalg.norm(cell, axis=1))
    nkx = int(round(l / np.linalg.norm(cell[0]) / 2 + 0.01, 0) * 2)
    nky = int(round(l / np.linalg.norm(cell[1]) / 2 + 0.01, 0) * 2)
    if bulk == True:
        nkz = int(round(l / np.linalg.norm(cell[2]) / 2 + 0.01) * 2)
    else:
        nkz = 1
    return ((nkx, nky, nkz))


def get_LUJ_values(atoms, user_luj=None):
    selected_luj = {}

    # Static values - can we do better than this?

    ldau_luj = {
        'Sc': {'L': 2, 'U': 3.00, 'J': 0.0},
        'Ti': {'L': 2, 'U': 3.00, 'J': 0.0},
        'V': {'L': 2, 'U': 3.25, 'J': 0.0},  # Materials Project
        'Cr': {'L': 2, 'U': 3.50, 'J': 0.0},  # close to MP
        'Mn': {'L': 2, 'U': 3.75, 'J': 0.0},
        'Fe': {'L': 2, 'U': 4.30, 'J': 0.0},  # carter 4.3 eV Friebel 3.5 eV
        'Co': {'L': 2, 'U': 3.32, 'J': 0.0},
        'Ni': {'L': 2, 'U': 6.45, 'J': 0.0},  # This is simply too high, needs to be checked with HSE06
        # 'Ni':{'L':  2, 'U': 6.45, 'J': 0.0}, # carter 5.5 Friebel 6.6 eV
        'Cu': {'L': 2, 'U': 3.00, 'J': 0.0},  # we should have some U
        'Zn': {'L': 2, 'U': 3.00, 'J': 0.0},  # used default U value
        'Y': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Zr': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Nb': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Mo': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Tc': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ru': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Rh': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Pd': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ag': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Cd': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Hf': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ta': {'L': -1, 'U': 0.00, 'J': 0.0},
        'W': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Re': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Os': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ir': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Pt': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Au': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Hg': {'L': -1, 'U': 0.00, 'J': 0.0},
        'La': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ce': {'L': 3, 'U': 0.00, 'J': 0.0},
        'O': {'L': -1, 'U': 0.00, 'J': 0.0},
        'C': {'L': -1, 'U': 0.00, 'J': 0.0},
        'H': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Al': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Te': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Tl': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Sb': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Pb': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ge': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Si': {'L': -1, 'U': 0.00, 'J': 0.0},
        'As': {'L': -1, 'U': 0.00, 'J': 0.0},
        'In': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Ga': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Sn': {'L': -1, 'U': 0.00, 'J': 0.0},
        'Bi': {'L': -1, 'U': 0.00, 'J': 0.0}}

    # Update with user-provided values if any
    if user_luj:
        for element, values in user_luj.items():
            if element in ldau_luj:
                # Update existing element with any of L, U, J that are provided
                for param in ['L', 'U', 'J']:
                    if param in values:
                        ldau_luj[element][param] = values[param]
            else:
                # Add new element
                ldau_luj[element] = values

    # Select values for atoms in the system
    selected_luj = {}

    for sym in set(list(atoms.symbols)):
        selected_luj[sym] = ldau_luj[sym]

    return selected_luj


def get_afm_comp(atoms):
    """get all magnetic configurations from symmetry (using spglib package)"""
    magmoms = get_initial_magmoms(atoms)

    magmoms = [round(m, 1) for m in magmoms]
    magmoms_list = [[]]
    magmoms_list_ph = []
    for mag in magmoms:
        for m in magmoms_list:
            magmoms_list_ph += [m + [mag]]
            if not mag == 0:
                magmoms_list_ph += [m + [-mag]]

        magmoms_list = magmoms_list_ph
        magmoms_list_ph = []

    magnetic_spacegroup_nos = []
    for magmoms in magmoms_list:
        spglibdata = spglib.get_magnetic_symmetry_dataset((atoms.get_cell(),
                                                           atoms.get_scaled_positions(),
                                                           atoms.get_atomic_numbers(),
                                                           magmoms),
                                                          symprec=1e-3)
        magnetic_spacegroup_nos += [spglibdata['uni_number']]

    unque_sp, indices = np.unique(magnetic_spacegroup_nos, return_index=True)

    return np.array(magmoms_list)[indices]


def get_nbands_cohp(directory):
    # Get number of bands needed for lobster
    atoms = read(directory + 'POSCAR')
    symbols = list(atoms.symbols)
    Nbands = 0
    Nelectrons = 0

    for sym in set(symbols):
        n = symbols.count(sym)
        found = False
        Norb = 0
        for line in open(directory + 'POTCAR', 'r'):
            if found:
                zval = int(float(line.rstrip('\n')))
                found = False
                break
            if 'PBE ' + sym in line:
                psp = [l for l in line.split(' ') if sym in l and not 'PAW' in l][0]
                found = True

        orbitals = orbital_map[psp]
        Norb += orbitals.count('s')
        Norb += orbitals.count('p') * 3
        Norb += orbitals.count('d') * 5
        Norb += orbitals.count('f') * 7
        Nbands += Norb * n
        Nelectrons += zval * n

    # add a few extra bands
    Nbands = max(Nbands, Nelectrons)

    # round up to multiple of 4
    Nbands += 4 - Nbands % 4

    return Nbands


def get_bader_charges(dir='.'):
    if not (os.path.exists(dir + 'CHGCAR')):
        quit('ERROR no CHGCAR present')
    if os.path.exists(dir + 'AECCAR0'):
        subprocess.call('cd ' + dir + '; /global/cfs/cdirs/m2997/bin/chgsum.pl AECCAR0 AECCAR2',
                        shell=True)
        subprocess.call('cd ' + dir + ';bader CHGCAR -ref CHGCAR_sum', shell=True)
    else:
        subprocess.call('cd ' + dir + '; bader CHGCAR', shell=True)

    outfilename = dir + 'bader_charges.txt'

    # Read bader output file
    with open(dir + "ACF.dat", "r") as file:
        lines = file.readlines()

    newlines = []
    for line in lines[2:-4]:
        newline = map(float, line.split())
        newlines.append(list(newline))

    newlines = np.array(newlines)
    charge = newlines[:, 4]

    atoms = read(dir + 'OUTCAR')
    names = list(atoms.symbols)

    # Read PSP dependent number of valence electrons from OUTCAR
    with open(dir + "OUTCAR", "r") as file:
        outcar = file.readlines()

    for line in outcar:
        if 'ZVAL' in line and not 'valenz' in line:
            zvals = [float(z) for z in line.split()[2:]]
            break
        if 'POSCAR:' in line:
            atoms_short = [n for n in line.split()[1:]]
    chargedict = {}
    for i, a in enumerate(atoms_short):
        chargedict[a] = zvals[i]

    write_charge = []
    with open(outfilename, 'w+') as outfile:
        for i in range(len(charge)):
            name_i = names[i]
            index = i
            charge_i = charge[i]
            netcharge = -(charge_i - chargedict[name_i])
            netcharge_round = round(netcharge, 2)

            write_charge.append(netcharge_round)
            print('index: ' + str(index) + ' name: ' + name_i +
                  ' charge: ' + str(netcharge), file=outfile)

    with open(outfilename, 'r') as outfile:
        printout = outfile.readlines()
        for line in printout:
            print(line)
    return write_charge


def get_restart(outcar, dir):
    relax_dir = dir + outcar
    atoms = read(relax_dir)
    moments = atoms.get_magnetic_moments()

    forces = np.linalg.norm(atoms.get_forces(), axis=1)

    atoms.set_initial_magnetic_moments(moments)
    try:
        atoms_charges = get_bader_charges(dir)
        atoms.set_initial_charges(atoms_charges)
    except:
        print('bader charges failed')
        pass
    print('Forces converged to fmax=', np.max(forces))

    write(dir + 'restart.json', atoms)


def get_max_radii(directory):
    atoms = read(directory + 'POSCAR')

    radii = []
    for n in list(set(atoms.numbers)):
        if n == 8:
            continue
        radii += [cradii[n]]

    radii_O = cradii[8]

    min_radii = 0.1  # round((radii_O + min(radii)) * 0.75, 3)
    max_radii = round((radii_O + max(radii)) * 1.15, 3)

    return max_radii


def write_lobsterIn(directory, config_params=None):
    """
    Write lobsterin file with configuration parameters.
    
    Args:
        directory: Directory where lobsterin file will be written
        config_params: Dictionary containing LOBSTER configuration parameters
    """
    # Use default parameters if none provided
    if config_params is None:
        config_params = {
            "basisSet": "pbeVaspFit2015",
            "COHPStartEnergy": "-100",
            "COHPEndEnergy": "100",
            "DensityOfEnergy": ".TRUE.",
            "max_radii": "2.3"
        }

    script = open(directory + 'lobsterin', "w")
    max_radii = get_max_radii(directory)
    lines = [
        f"basisSet {config_params['basisSet']} \n",
        f"COHPStartEnergy {config_params['COHPStartEnergy']} \n",
        f"COHPEndEnergy {config_params['COHPEndEnergy']} \n",
        f"DensityOfEnergy {config_params['DensityOfEnergy']} \n",
        f"cohpGenerator from 0.1 to {max_radii} orbitalWise \n"
    ]
    
    calculation_lines = []
    restart_json = directory + 'restart.json'
    atoms = read(restart_json)

    for symbol in set(atoms.get_chemical_symbols()):
        if symbol + '_pv' in orbital_map:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol + '_pv'] + '\n')
        elif symbol + '_sv' in orbital_map:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol + '_sv'] + '\n')
        elif symbol + '_d' in orbital_map:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol + '_d'] + '\n')
        elif symbol + '_3' in orbital_map:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol + '_3'] + '\n')
        elif symbol + '_2' in orbital_map:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol + '_2'] + '\n')
        else:
            calculation_lines.append("basisfunctions " + symbol + ' ' + orbital_map[symbol] + '\n')

    lines = lines + calculation_lines
    script.writelines(lines)
    script.close()


def get_icohp_matrix(atoms, filename='ICOHPLIST.lobster', orbitals='all'):
    """
    Returns the NxN matrix with individual bonds in offdiagonal term
    Similar to a connectivity matrix but with ICOHP connectivity
    atom: ASE Atoms objext
    filename: input ICOHPLIST.lobster, ICOOPLIST.lobster, or ICOBILIST.lobster
              for energy, charge, and bond-order contribution repsectively
    orbitals: 'all' to inlcude all orbitals in the setup
               dict to include specific orbitals for each element:
               {'Cr': ['s', 'd'],
                'O':  ['2p']}
    """
    I_matrix = np.zeros([len(atoms), len(atoms)])
    icohps = []
    for line in open(filename, 'r'):
        linesplit = line.split()
        if len(linesplit) > 8:
            # i = 0
            continue
        n, atom1, atom2, distance, t1, t2, t3, icohp = linesplit
        orbital1 = None
        orbital2 = None
        if '_' in atom1:
            atom1, orbital1 = atom1.split('_', 1)
        if '_' in atom2:
            atom2, orbital2 = atom2.split('_', 1)
        n = int(n)
        for i, s in enumerate(atom1):
            if s.isdigit():
                symbol1 = atom1[:i]
                idx1 = int(atom1[i:])
                break
        for i, s in enumerate(atom2):
            if s.isdigit():
                symbol2 = atom2[:i]
                idx2 = int(atom2[i:])
                break
        idx1 -= 1
        idx2 -= 1
        if orbitals == 'all':
            # Only take total sum for now
            if not orbital1 == None and not orbital2 == None:
                continue
        else:
            match = False
            if orbital1 is None and orbital2 is None:
                continue
            for orb1 in orbitals[symbol1]:
                for orb2 in orbitals[symbol2]:
                    if orb1 in orbital1 and orb2 in orbital2:
                        match = True
            if not match:
                continue

        I_matrix[idx1, idx2] += float(icohp)
        I_matrix[idx2, idx1] += float(icohp)

    return I_matrix


def get_icohp_vs_d(atoms, filename):
    distances = []
    icohps = []
    pairs = []
    translations = []
    for line in open(filename, 'r'):
        linesplit = line.split()
        if len(linesplit) > 8:
            # i = 0
            continue
        n, atom1, atom2, distance, t1, t2, t3, icohp = linesplit

        if '_' in atom1 or '_' in atom2:
            continue
        for i, s in enumerate(atom1):
            if s.isdigit():
                symbol1 = atom1[:i]
                idx1 = int(atom1[i:])
                break
        for i, s in enumerate(atom2):
            if s.isdigit():
                symbol2 = atom2[:i]
                idx2 = int(atom2[i:])
                break

        distances += [float(distance)]
        icohps += [float(icohp)]
        pair = '{}-{}'.format(symbol1, symbol2)
        pairs += [pair]
        translations += [[t1, t2, t3]]
    new_icohps = []
    n = int(len(distances) / 2)
    for i in range(0, n):
        new_icohps.append(icohps[i] + icohps[i + n])

    return distances[0:n], new_icohps, pairs[0:n]


def get_doe(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read().split("\n")
            data_list = data[6:]
        split_data = [line.split() for line in data_list]
        df = pd.DataFrame(split_data)
        df = df.apply(pd.to_numeric)
        df['total_int_up-down'] = df[3] + df[4]
    except:
        df = pd.DataFrame({'0': [0],
                           '1': [0],
                           '2': [0],
                           '3': [0],
                           '4': [0]})
        print("doe error occured in filename{}".format(filename))
        df['total_int_up-down'] = df['3'] + df['4']
    return df


def get_madelung_energies(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read().split("\n")
            data_list = data[5:]
        split_data = [line.split() for line in data_list]
        madelung_energy_str = split_data[0][1]
        madelung_energy = eval(madelung_energy_str)
    except:
        print("madelung error occured in filename{}".format(filename))
    return madelung_energy


def copy_file(source_path: str, destination_path: str) -> None:
    """
    Copy a file from source path to destination path.
    
    Args:
        source_path: Path to the source file
        destination_path: Path where the file should be copied to
    """
    try:
        shutil.copy2(source_path, destination_path)
    except FileNotFoundError:
        print(f"Source file {source_path} not found")
    except PermissionError:
        print(f"Permission denied when copying {source_path} to {destination_path}")
    except Exception as e:
        print(f"Error copying file: {str(e)}")


def get_pdos_data(execution):
    dos_dir = execution.result_material_dir
    poscar_path = os.path.join(dos_dir, 'POSCAR')
    with open(poscar_path, 'r') as file:
        first_line = file.readline().strip()
    first_line_list = first_line.split()

    R = RapiDOS(file_dir=dos_dir)
    xlim = [-15, 15]

    PTM_oxides = ['Al', 'Si', 'As', 'Bi', 'Ga', 'Ge', 'In', 'Pb', 'Sn', 'Sb', 'Tl', 'Po', 'Te']
    elements_orbital = {}

    for i in range(len(first_line_list)):
        if first_line_list[i] == 'O':
            elements_orbital[first_line_list[i]] = ['p']
        elif first_line_list[i] in PTM_oxides:
            elements_orbital[first_line_list[i]] = ['p']
        else:
            elements_orbital[first_line_list[i]] = ['d']

    pdos_data = R.pdos_data(elements=elements_orbital, xlim=xlim)

    center_tm_d = 0.0
    center_ptm_p = 0.0
    center_o_2p = 0.0

    for key, value in elements_orbital.items():
        if 'd' in value:
            center_tm_d = R.get_pdos_center(elements={key: value})
        elif key != 'O' and 'p' in value:
            center_ptm_p = R.get_pdos_center(elements={key: value})
        else:
            center_o_2p = R.get_pdos_center(elements={key: value})

    return pdos_data, center_tm_d, center_ptm_p, center_o_2p






