"""
IS 456:2000 Constants, Tables, and Standard Empirical Provisions.

Reference: IS 456 : 2000 - Plain and Reinforced Concrete - Code of Practice.
"""

from typing import Dict, List


# Clause 38.1 Note & Annex G-1.1: Limiting depth of neutral axis (xu_max / d)
# Steel Grade -> xu_max / d ratio
LIMITING_NEUTRAL_AXIS_RATIO: Dict[float, float] = {
    250.0: 0.53,
    415.0: 0.48,
    500.0: 0.46,
    550.0: 0.44,  # Per IS 1786 / IS 456 Amendment
}


def get_xu_max_d_ratio(f_y: float, E_s: float = 200000.0) -> float:
    """
    Returns xu_max / d for a given yield strength of steel f_y.
    
    Uses standard table value if exact grade exists (250, 415, 500, 550),
    otherwise calculates using strain compatibility formula from Cl 38.1 Note:
    xu_max / d = 0.0035 / (0.0055 + 0.87 * f_y / E_s)
    
    Clause: IS 456:2000 Clause 38.1 Note & Annex G-1.1
    """
    if f_y in LIMITING_NEUTRAL_AXIS_RATIO:
        return LIMITING_NEUTRAL_AXIS_RATIO[f_y]
    
    # Calculate exact formula ratio
    return 0.0035 / (0.0055 + (0.87 * f_y / E_s))


# Clause 40.2.3 & Table 20: Maximum Shear Stress tau_c_max (N/mm²)
TABLE_20_TAU_C_MAX: Dict[float, float] = {
    15.0: 2.5,
    20.0: 2.8,
    25.0: 3.1,
    30.0: 3.5,
    35.0: 3.7,
    40.0: 4.0,  # 40 and above
}


def get_tau_c_max(f_ck: float) -> float:
    """
    Get maximum permissible shear stress tau_c_max (N/mm²) for given concrete grade.
    
    Clause: IS 456:2000 Table 20 & Clause 40.2.3
    """
    if f_ck < 15.0:
        raise ValueError(f"Concrete grade f_ck ({f_ck} N/mm²) is below IS 456 minimum structural grade M15")
    
    grades = sorted(TABLE_20_TAU_C_MAX.keys())
    if f_ck >= grades[-1]:
        return TABLE_20_TAU_C_MAX[grades[-1]]
    
    for grade in grades:
        if f_ck <= grade:
            return TABLE_20_TAU_C_MAX[grade]
            
    return TABLE_20_TAU_C_MAX[40.0]


# Clause 40.2.1 & Table 19: Design Shear Strength of Concrete tau_c (N/mm²)
TABLE_19_PT_PERCENT: List[float] = [
    0.15, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00
]

TABLE_19_FCK_GRADES: List[float] = [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]

# Mapping: f_ck -> list of tau_c values corresponding to TABLE_19_PT_PERCENT
TABLE_19_VALUES: Dict[float, List[float]] = {
    15.0: [0.28, 0.35, 0.46, 0.54, 0.60, 0.64, 0.68, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71],
    20.0: [0.28, 0.36, 0.48, 0.56, 0.62, 0.67, 0.72, 0.75, 0.79, 0.81, 0.82, 0.82, 0.82],
    25.0: [0.29, 0.36, 0.49, 0.57, 0.64, 0.70, 0.74, 0.78, 0.82, 0.85, 0.88, 0.90, 0.92],
    30.0: [0.29, 0.37, 0.50, 0.59, 0.66, 0.73, 0.78, 0.82, 0.87, 0.90, 0.93, 0.95, 0.98],
    35.0: [0.29, 0.37, 0.50, 0.59, 0.67, 0.74, 0.79, 0.84, 0.89, 0.93, 0.97, 1.00, 1.04],
    40.0: [0.30, 0.38, 0.51, 0.60, 0.68, 0.75, 0.81, 0.86, 0.92, 0.96, 1.01, 1.04, 1.09],
}


# Clause 26.2.1.1: Design bond stress tau_bd (N/mm²) for plain bars in tension
TABLE_TAU_BD_PLAIN: Dict[float, float] = {
    15.0: 1.0,
    20.0: 1.2,
    25.0: 1.4,
    30.0: 1.5,
    35.0: 1.7,
    40.0: 1.9,  # 40 and above
}


def get_bond_stress_breakdown(
    f_ck: float, is_hysd: bool = True, is_compression: bool = False
) -> tuple:
    """
    Returns explicit breakdown of design bond stress components as per IS 456 Cl 26.2.1.1.

    Returns:
        tuple: (tau_bd_plain, hysd_factor, compression_factor, tau_bd_design)
    """
    if f_ck < 15.0:
        raise ValueError(f"Concrete grade f_ck ({f_ck} N/mm²) is below IS 456 minimum structural grade M15")

    grades = sorted(TABLE_TAU_BD_PLAIN.keys())
    if f_ck >= grades[-1]:
        base_tau = TABLE_TAU_BD_PLAIN[grades[-1]]
    else:
        base_tau = TABLE_TAU_BD_PLAIN[grades[0]]
        for g in grades:
            if f_ck >= g:
                base_tau = TABLE_TAU_BD_PLAIN[g]

    hysd_factor = 1.60 if is_hysd else 1.00
    compression_factor = 1.25 if is_compression else 1.00
    tau_bd_design = base_tau * hysd_factor * compression_factor

    return base_tau, hysd_factor, compression_factor, tau_bd_design


def get_design_tau_bd(f_ck: float, is_hysd: bool = True, is_compression: bool = False) -> float:
    """
    Calculates design bond stress tau_bd (N/mm²) as per IS 456 Cl 26.2.1.1.
    """
    _, _, _, tau_bd_design = get_bond_stress_breakdown(f_ck, is_hysd=is_hysd, is_compression=is_compression)
    return tau_bd_design


# -----------------------------------------------------------------------------
# Clause 23.2.1 & Figure 4: Modification Factor for Tension Reinforcement (F1 / Kt)
# Digitized grid mapping: pt (%) vs fs (N/mm²)
# -----------------------------------------------------------------------------
FIG_4_PT_GRID: List[float] = [0.10, 0.20, 0.30, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40, 1.60, 1.80, 2.00, 2.50, 3.00]
FIG_4_FS_GRID: List[float] = [120.0, 145.0, 190.0, 240.0, 290.0]

# Mapping: pt -> list of F1 values corresponding to FIG_4_FS_GRID
FIG_4_GRID_VALUES: Dict[float, List[float]] = {
    0.10: [2.00, 2.00, 2.00, 2.00, 1.60],
    0.20: [2.00, 2.00, 1.70, 1.45, 1.25],
    0.30: [2.00, 1.85, 1.50, 1.28, 1.10],
    0.40: [2.00, 1.70, 1.35, 1.15, 1.00],
    0.60: [1.85, 1.45, 1.20, 1.02, 0.88],
    0.80: [1.70, 1.33, 1.10, 0.94, 0.82],
    1.00: [1.60, 1.25, 1.04, 0.88, 0.77],
    1.20: [1.52, 1.18, 0.98, 0.84, 0.74],
    1.40: [1.45, 1.12, 0.94, 0.80, 0.72],
    1.60: [1.40, 1.08, 0.90, 0.78, 0.70],
    1.80: [1.36, 1.05, 0.87, 0.76, 0.68],
    2.00: [1.32, 1.02, 0.85, 0.74, 0.67],
    2.50: [1.25, 0.96, 0.80, 0.70, 0.64],
    3.00: [1.20, 0.92, 0.77, 0.68, 0.62],
}


def get_fig4_modification_factor_F1(pt_percent: float, fs_Nmm2: float) -> float:
    """
    Computes modification factor F1 (Kt) for tension reinforcement from IS 456 Fig 4
    using digitized 2D grid bilinear interpolation.

    Args:
        pt_percent: Tension reinforcement percentage 100 * Ast / (b * d)
        fs_Nmm2: Service stress in tension steel 0.58 * f_y * (Ast_req / Ast_prov)

    Clause: IS 456:2000 Clause 23.2.1 & Figure 4
    """
    pt_clamped = max(0.10, min(3.00, pt_percent))
    fs_clamped = max(120.0, min(290.0, fs_Nmm2))

    # Helper for 1D interpolation along fs grid for a given list of F1 values
    def _interp_fs(fs: float, values: List[float]) -> float:
        fs_grid = FIG_4_FS_GRID
        if fs <= fs_grid[0]:
            return values[0]
        if fs >= fs_grid[-1]:
            return values[-1]
        for i in range(len(fs_grid) - 1):
            if fs_grid[i] <= fs <= fs_grid[i + 1]:
                t = (fs - fs_grid[i]) / (fs_grid[i + 1] - fs_grid[i])
                return values[i] + t * (values[i + 1] - values[i])
        return values[-1]

    pts = FIG_4_PT_GRID
    if pt_clamped <= pts[0]:
        return min(2.0, _interp_fs(fs_clamped, FIG_4_GRID_VALUES[pts[0]]))
    if pt_clamped >= pts[-1]:
        return min(2.0, _interp_fs(fs_clamped, FIG_4_GRID_VALUES[pts[-1]]))

    for i in range(len(pts) - 1):
        if pts[i] <= pt_clamped <= pts[i + 1]:
            f1_lower = _interp_fs(fs_clamped, FIG_4_GRID_VALUES[pts[i]])
            f1_upper = _interp_fs(fs_clamped, FIG_4_GRID_VALUES[pts[i + 1]])
            t_pt = (pt_clamped - pts[i]) / (pts[i + 1] - pts[i])
            f1_val = f1_lower + t_pt * (f1_upper - f1_lower)
            return min(2.0, max(0.5, f1_val))

    return 1.0


# -----------------------------------------------------------------------------
# Clause 23.2.1 & Figure 5: Modification Factor for Compression Reinforcement (F2 / Kc)
# Digitized grid mapping: pc (%) -> F2
# -----------------------------------------------------------------------------
FIG_5_PC_GRID: List[float] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
FIG_5_F2_VALUES: List[float] = [1.00, 1.06, 1.12, 1.17, 1.22, 1.26, 1.30, 1.36, 1.43, 1.48, 1.50]


def get_fig5_modification_factor_F2(pc_percent: float) -> float:
    """
    Computes modification factor F2 (Kc) for compression reinforcement from IS 456 Fig 5
    using digitized 1D linear interpolation. Capped at 1.50 per IS 456 Fig 5.

    Args:
        pc_percent: Compression reinforcement percentage 100 * Asc / (b * d)

    Clause: IS 456:2000 Clause 23.2.1 & Figure 5
    """
    if pc_percent <= 0.0:
        return 1.00
    pcs = FIG_5_PC_GRID
    vals = FIG_5_F2_VALUES
    if pc_percent >= pcs[-1]:
        return vals[-1]

    for i in range(len(pcs) - 1):
        if pcs[i] <= pc_percent <= pcs[i + 1]:
            t = (pc_percent - pcs[i]) / (pcs[i + 1] - pcs[i])
            return vals[i] + t * (vals[i + 1] - vals[i])

    return 1.50

