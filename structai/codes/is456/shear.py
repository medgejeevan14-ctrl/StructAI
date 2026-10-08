"""
IS 456:2000 Shear Design Engine for Rectangular Beams.

Provisions implemented:
- Clause 40.1: Nominal shear stress tau_v
- Clause 40.2.1 & Table 19: Design shear strength of concrete tau_c with exact linear interpolation
- Clause 40.2.3 & Table 20: Maximum permissible shear stress tau_c_max
- Clause 40.4: Design of shear reinforcement (vertical stirrups)
- Clause 26.5.1.6: Minimum shear reinforcement
- Clause 26.5.1.5: Maximum spacing of stirrups
"""

from typing import List, Optional, Tuple
from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    ShearDesignResult,
)
from structai.codes.is456.constants import (
    TABLE_19_PT_PERCENT,
    TABLE_19_FCK_GRADES,
    TABLE_19_VALUES,
    get_tau_c_max,
)


def interpolate_tau_c(pt_percent: float, f_ck: float) -> float:
    """
    Computes design shear strength tau_c (N/mm²) from IS 456:2000 Table 19
    using exact 1D/2D linear interpolation.

    Args:
        pt_percent: Percentage of tension reinforcement 100 * Ast / (b * d)
        f_ck: Characteristic compressive strength of concrete (N/mm²)

    Returns:
        float: Design shear strength tau_c (N/mm²)

    Clause: IS 456:2000 Table 19 & Note
    """
    if f_ck < 15.0:
        raise ValueError(f"Concrete grade f_ck ({f_ck} N/mm²) is below M15")

    # Bound pt percentage as per Table 19 notes:
    # "For pt < 0.15%, use value for pt = 0.15%"
    # "For pt > 3.00%, use value for pt = 3.00%"
    pt_effective = max(0.15, min(3.00, pt_percent))

    # Helper function for 1D interpolation along pt_percent array for a given f_ck key in TABLE_19_VALUES
    def _interpolate_1d(pt: float, values: List[float]) -> float:
        pts = TABLE_19_PT_PERCENT
        if pt <= pts[0]:
            return values[0]
        if pt >= pts[-1]:
            return values[-1]
        
        for i in range(len(pts) - 1):
            if pts[i] <= pt <= pts[i + 1]:
                t = (pt - pts[i]) / (pts[i + 1] - pts[i])
                return values[i] + t * (values[i + 1] - values[i])
        return values[-1]

    # Concrete grade handling
    fck_grades = TABLE_19_FCK_GRADES
    if f_ck >= fck_grades[-1]:
        # For M40 and above
        return _interpolate_1d(pt_effective, TABLE_19_VALUES[40.0])

    if f_ck in TABLE_19_VALUES:
        return _interpolate_1d(pt_effective, TABLE_19_VALUES[f_ck])

    # If intermediate concrete grade is provided (e.g. M22.5), perform 2D linear interpolation
    fck_lower = fck_grades[0]
    fck_upper = fck_grades[-1]
    for i in range(len(fck_grades) - 1):
        if fck_grades[i] <= f_ck <= fck_grades[i + 1]:
            fck_lower = fck_grades[i]
            fck_upper = fck_grades[i + 1]
            break

    tau_c_lower = _interpolate_1d(pt_effective, TABLE_19_VALUES[fck_lower])
    tau_c_upper = _interpolate_1d(pt_effective, TABLE_19_VALUES[fck_upper])

    t_fck = (f_ck - fck_lower) / (fck_upper - fck_lower)
    return tau_c_lower + t_fck * (tau_c_upper - tau_c_lower)


def design_shear(
    geometry: BeamGeometry,
    materials: MaterialProperties,
    loads: FactoredLoads,
    Ast_provided_mm2: float,
    stirrup_details: Optional[StirrupDetails] = None,
) -> ShearDesignResult:
    """
    Designs shear reinforcement and checks shear stress limits as per IS 456:2000.

    Args:
        geometry: Beam section dimensions (b, d) in mm
        materials: Material properties (f_ck, f_yv) in N/mm²
        loads: Factored design loads (V_u in kN)
        Ast_provided_mm2: Tension steel area provided (mm²) for Table 19 tau_c lookup
        stirrup_details: Optional stirrup bar diameter and leg details to evaluate specific spacing

    Returns:
        ShearDesignResult: Complete shear analysis results, required spacing, max spacing, status.
    """
    clauses: List[str] = [
        "IS 456:2000 Clause 40.1 (Nominal Shear Stress tau_v)",
        "IS 456:2000 Clause 40.2.1 & Table 19 (Design Shear Strength of Concrete tau_c)",
        "IS 456:2000 Clause 40.2.3 & Table 20 (Maximum Permissible Shear Stress tau_c_max)",
        "IS 456:2000 Clause 40.4 (Shear Reinforcement Design)",
        "IS 456:2000 Clause 26.5.1.6 (Minimum Shear Reinforcement)",
        "IS 456:2000 Clause 26.5.1.5 (Maximum Spacing of Stirrups)",
    ]
    notes: List[str] = []

    b = geometry.b
    d = geometry.d
    f_ck = materials.f_ck
    f_yv = materials.f_yv
    V_u_kN = loads.V_u
    V_u_N = loads.V_u_N  # kN to N conversion (1 kN = 1000 N)

    # 1. Calculate nominal shear stress tau_v (Clause 40.1)
    # tau_v = V_u / (b * d)
    tau_v_Nmm2 = V_u_N / (b * d)

    # 2. Maximum permissible shear stress tau_c_max (Clause 40.2.3 & Table 20)
    tau_c_max_Nmm2 = get_tau_c_max(f_ck)

    # Check maximum shear stress limit
    if tau_v_Nmm2 > tau_c_max_Nmm2:
        is_section_safe = False
        notes.append(
            f"CRITICAL: Nominal shear stress tau_v ({tau_v_Nmm2:.3f} N/mm²) exceeds "
            f"maximum permissible shear stress tau_c_max ({tau_c_max_Nmm2:.3f} N/mm²) "
            f"as per Clause 40.2.3 & Table 20. Beam section size MUST be increased or "
            f"concrete grade increased."
        )
    else:
        is_section_safe = True

    # 3. Design shear strength of concrete tau_c (Clause 40.2.1 & Table 19)
    # pt = 100 * Ast / (b * d)
    pt_percent = (100.0 * Ast_provided_mm2) / (b * d)
    tau_c_Nmm2 = interpolate_tau_c(pt_percent, f_ck)

    # Determine default or provided stirrup bar details for spacing calculations
    if stirrup_details is None:
        # Default 2-legged 8mm stirrup if not specified (A_sv = 2 * pi * 8^2 / 4 = 100.53 mm²)
        import math
        A_sv_mm2 = 2.0 * (math.pi / 4.0) * (8.0 ** 2)
    else:
        A_sv_mm2 = stirrup_details.A_sv

    # 4. Check minimum shear reinforcement requirement (Clause 26.5.1.6)
    # Asv / (b * sv) >= 0.4 / (0.87 * f_yv)  =>  sv_min_rebar = (0.87 * f_yv * Asv) / (0.4 * b)
    sv_req_min_rebar_mm = (0.87 * f_yv * A_sv_mm2) / (0.4 * b)

    # 5. Maximum spacing code limit (Clause 26.5.1.5)
    # sv_max = min(0.75 * d, 300 mm)
    sv_max_code_limit_mm = min(0.75 * d, 300.0)

    # Combined max permissible spacing limit
    governing_max_spacing_mm = min(sv_max_code_limit_mm, sv_req_min_rebar_mm)

    # 6. Evaluate shear reinforcement requirement (Clause 40.4)
    if tau_v_Nmm2 > tau_c_Nmm2:
        shear_rebar_required = True
        # Net shear force to be carried by stirrups: V_us = V_u - tau_c * b * d
        V_us_N = V_u_N - (tau_c_Nmm2 * b * d)
        V_us_kN = V_us_N / 1000.0

        # Required stirrup spacing for strength (Clause 40.4 a):
        # sv = (0.87 * f_yv * Asv * d) / V_us
        if V_us_N > 0:
            sv_req_calc_mm = (0.87 * f_yv * A_sv_mm2 * d) / V_us_N
        else:
            sv_req_calc_mm = governing_max_spacing_mm

        notes.append(
            f"Nominal shear stress tau_v ({tau_v_Nmm2:.3f} N/mm²) > tau_c ({tau_c_Nmm2:.3f} N/mm²). "
            f"Shear stirrups required for net shear force V_us = {V_us_kN:.2f} kN."
        )
    else:
        shear_rebar_required = False
        V_us_kN = 0.0
        sv_req_calc_mm = None
        notes.append(
            f"Nominal shear stress tau_v ({tau_v_Nmm2:.3f} N/mm²) <= tau_c ({tau_c_Nmm2:.3f} N/mm²). "
            f"Nominal minimum shear reinforcement required as per Clause 26.5.1.6."
        )

    return ShearDesignResult(
        V_u_kN=V_u_kN,
        tau_v_Nmm2=tau_v_Nmm2,
        tau_c_Nmm2=tau_c_Nmm2,
        tau_c_max_Nmm2=tau_c_max_Nmm2,
        pt_provided_percent=pt_percent,
        shear_reinforcement_required=shear_rebar_required,
        is_section_safe_in_shear=is_section_safe,
        V_us_kN=V_us_kN,
        sv_req_calc_mm=sv_req_calc_mm,
        sv_req_min_rebar_mm=sv_req_min_rebar_mm,
        sv_max_code_limit_mm=sv_max_code_limit_mm,
        governing_max_spacing_mm=governing_max_spacing_mm,
        clauses=clauses,
        notes=notes,
    )
