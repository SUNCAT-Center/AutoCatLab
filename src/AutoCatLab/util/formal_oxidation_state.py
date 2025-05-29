import numpy as np
from ase.data import covalent_radii as cradii
from ase.geometry import get_distances
from catkit.gen.utils.connectivity import get_cutoff_neighbors


def get_interatomic_distances(atoms):
    D, distances = get_distances(atoms.positions,
                                 cell=atoms.cell,
                                 pbc=True)
    min_cell_width = np.min(np.linalg.norm(atoms.cell, axis=1))
    min_cell_width *= np.ones(len(atoms))
    np.fill_diagonal(distances, min_cell_width)
    return D, distances


def get_connectivity(atoms, bond_scale=False):
    matrix = get_cutoff_neighbors(atoms, scale_cov_radii=1.3)

    if bond_scale:
        covalent_radii = np.array([cradii[n] for n in atoms.numbers])
        M = covalent_radii * np.ones([len(atoms), len(atoms)])
        cov_distances = (M + M.T)
        Dm, distances = get_interatomic_distances(atoms)
        distances_scaled = distances / cov_distances
        matrix = np.array(matrix, dtype=float)
        matrix *= distances_scaled
    return matrix


def get_formal_oxidation_state(atoms, charge_O=-2,
                               charge_H=1, bond_scale=False):
    O_indices = np.array([i for i, a in enumerate(atoms)
                          if a.symbol == 'O'])

    H_indices = []

    M_indices = np.array([i for i, a in enumerate(atoms)
                          if not a.symbol in ['O', 'H', 'N']])

    con_matrix = get_connectivity(atoms, bond_scale=bond_scale)
    oxi_states = np.ones([len(atoms)])
    oxi_states[O_indices] = charge_O
    if H_indices:  # First correct O charge due to H
        oxi_states[H_indices] = charge_H
        for H_i in H_indices:
            H_O_connectivity = con_matrix[H_i][O_indices]
            norm = np.sum(H_O_connectivity)
            O_indices_H = O_indices[np.where(H_O_connectivity)[0]]
            oxi_states[O_indices_H] += charge_H / norm
    for metal_i in M_indices:  # Substract O connectivity
        M_O_connectivity = con_matrix[metal_i][O_indices]
        norm = np.sum(con_matrix[O_indices][:, M_indices], axis=-1)
        oxi_states[metal_i] = sum(
            M_O_connectivity * -oxi_states[O_indices] / norm)
    # atoms.set_initial_charges(np.round(oxi_states, 4))
    return np.round(oxi_states, 4)
