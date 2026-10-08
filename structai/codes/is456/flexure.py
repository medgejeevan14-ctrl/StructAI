"""
IS 456:2000 Singly Reinforced Rectangular Beam Flexural Design Engine.

Provisions implemented:
- Clause 38.1 & Annex G-1.1: Limiting depth of neutral axis xu_max
- Annex G-1.1 (c): Limiting moment of resistance Mu_lim
- Annex G-1.1 (b): Required tension steel Ast for singly reinforced section
- Clause 26.5.1.1 (a): Minimum tension reinforcement Ast,min
- Clause 26.5.1.1 (b): Maximum tension reinforcement Ast,max
"""

import math
from typing import List
from structai.core.datatypes import BeamGeometry, MaterialProperties, FactoredLoads, FlexureDesignResult
from structai.codes.is456.constants import get_xu_max_d_ratio


def design_flexure_singly_reinforced(
    geometry: BeamGeometry,
    materials: MaterialProperties,
    loads: FactoredLoads,
) -> FlexureDesignResult:
    """
    Designs flexural tension reinforcement for a singly reinforced rectangular beam
    in accordance with IS 456:2000 Annex G and Clause 38.1.

    Args:
        geometry: Beam section dimensions (b, D, d) in mm
        materials: Material properties (f_ck, f_y, E_s) in N/mm²
        loads: Factored design loads (M_u in kNm)

    Returns:
        FlexureDesignResult: Detailed results including xu, Mu_lim, Ast_req, Ast_min, Ast_max, clauses used.
    """
    clauses: List[str] = [
        "IS 456:2000 Clause 38.1 (Limit State of Collapse: Flexure)",
        "IS 456:2000 Annex G-1.1 (Limiting Depth of Neutral Axis & Moment Capacity)",
        "IS 456:2000 Clause 26.5.1.1 (a) (Minimum Tension Reinforcement)",
        "IS 456:2000 Clause 26.5.1.1 (b) (Maximum Tension Reinforcement)",
    ]
    notes: List[str] = []

    b = geometry.b
    D = geometry.D
    d = geometry.d
    f_ck = materials.f_ck
    f_y = materials.f_y
    M_u_kNm = loads.M_u
    M_u_Nmm = loads.M_u_Nmm  # kNm to Nmm conversion (1 kNm = 1e6 Nmm)

    # 1. Calculate limiting neutral axis depth ratio xu_max / d
    # Clause 38.1 Note & Annex G-1.1
    xu_max_d_ratio = get_xu_max_d_ratio(f_y, materials.E_s)
    xu_max_mm = xu_max_d_ratio * d

    # 2. Calculate limiting moment of resistance Mu_lim
    # IS 456 Annex G-1.1 (c): Mu_lim = 0.36 * (xu_max/d) * (1 - 0.42 * (xu_max/d)) * f_ck * b * d^2
    Mu_lim_Nmm = 0.36 * xu_max_d_ratio * (1.0 - 0.42 * xu_max_d_ratio) * f_ck * b * (d ** 2)
    Mu_lim_kNm = Mu_lim_Nmm / 1e6

    # 3. Check if doubly reinforced section is required
    if M_u_kNm > Mu_lim_kNm:
        # Section cannot resist moment as singly reinforced within code limiting neutral axis depth
        notes.append(
            f"Factored moment M_u ({M_u_kNm:.2f} kNm) exceeds limiting moment capacity "
            f"M_u_lim ({Mu_lim_kNm:.2f} kNm). Section requires doubly reinforced design (compression steel) "
            f"or larger cross-section. Doubly reinforced design is postponed to Phase 2."
        )
        # Calculate Ast required corresponding to Mu_lim as baseline
        Ast_req_mm2 = (0.36 * f_ck * b * xu_max_mm) / (0.87 * f_y)
        xu_mm = xu_max_mm
        is_under_reinforced = False
        is_doubly_required = True
    else:
        is_doubly_required = False
        is_under_reinforced = True
        
        if M_u_Nmm <= 0:
            Ast_req_mm2 = 0.0
            xu_mm = 0.0
            notes.append("Applied moment M_u is zero or negative. Nominal minimum reinforcement applies.")
        else:
            # 4. Calculate required tension steel area Ast_req for singly reinforced beam
            # IS 456 Annex G-1.1 (b): Ast = (0.5 * f_ck / f_y) * [1 - sqrt(1 - (4.6 * M_u) / (f_ck * b * d^2))] * b * d
            discriminant = 1.0 - (4.6 * M_u_Nmm) / (f_ck * b * (d ** 2))
            if discriminant < 0:
                # Numerical safety check (should not occur if M_u <= M_u_lim)
                discriminant = 0.0
            
            Ast_req_mm2 = (0.5 * f_ck / f_y) * (1.0 - math.sqrt(discriminant)) * b * d

            # Calculate actual neutral axis depth xu from force equilibrium:
            # 0.87 * f_y * Ast = 0.36 * f_ck * b * xu  => xu = (0.87 * f_y * Ast) / (0.36 * f_ck * b)
            # IS 456 Clause 38.1 & Annex G-1.1
            xu_mm = (0.87 * f_y * Ast_req_mm2) / (0.36 * f_ck * b)

    # 5. Check Minimum Tension Reinforcement (IS 456 Clause 26.5.1.1 a)
    # Ast_min / (b * d) = 0.85 / f_y  =>  Ast_min = (0.85 * b * d) / f_y
    Ast_min_mm2 = (0.85 * b * d) / f_y

    # 6. Check Maximum Tension Reinforcement (IS 456 Clause 26.5.1.1 b)
    # Ast_max = 0.04 * b * D
    Ast_max_mm2 = 0.04 * b * D

    # Governing provided Ast for design checks
    governing_Ast_mm2 = max(Ast_req_mm2, Ast_min_mm2)
    pt_req_percent = (100.0 * governing_Ast_mm2) / (b * d)

    return FlexureDesignResult(
        M_u_kNm=M_u_kNm,
        M_u_lim_kNm=Mu_lim_kNm,
        xu_max_mm=xu_max_mm,
        xu_max_d_ratio=xu_max_d_ratio,
        xu_mm=xu_mm,
        is_under_reinforced=is_under_reinforced,
        is_doubly_reinforced_required=is_doubly_required,
        Ast_req_mm2=Ast_req_mm2,
        Ast_min_mm2=Ast_min_mm2,
        Ast_max_mm2=Ast_max_mm2,
        pt_req_percent=pt_req_percent,
        governing_Ast_mm2=governing_Ast_mm2,
        clauses=clauses,
        notes=notes,
    )
