"""
IS 456:2000 Detailing and Code Limit Checks.

Provisions implemented:
- Clause 26.2.1: Development length Ld of tension reinforcement
- Clause 23.2.1: Basic span-to-effective-depth ratio for deflection control
- Clause 26.5.1.1 (a & b): Tension reinforcement limits
- Clause 26.5.1.5: Stirrup spacing limits
- Clause 26.5.1.6: Minimum shear reinforcement
- Clause 40.2.3: Maximum shear stress limit
"""

import math
from typing import List, Optional, Tuple
from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    SupportCondition,
    CheckStatus,
    CodeCheckResult,
    DetailingCheckResult,
    DevelopmentLengthResult,
    DeflectionCheckResult,
    FlexureDesignResult,
    ShearDesignResult,
)
from structai.codes.is456.constants import (
    get_bond_stress_breakdown,
    get_fig4_modification_factor_F1,
    get_fig5_modification_factor_F2,
)


def calculate_development_length(
    f_y: float,
    f_ck: float,
    bar_diameter_mm: float = 20.0,
    is_hysd: bool = True,
    is_compression: bool = False,
) -> DevelopmentLengthResult:
    """
    Calculates design development length Ld (mm) and Ld / bar_diameter ratio as per IS 456 Cl 26.2.1.

    Ld = (phi * sigma_s) / (4 * tau_bd)
    where:
    - sigma_s = 0.87 * f_y at ultimate limit state
    - tau_bd = tau_bd_plain * hysd_factor (+60% for HYSD) * compression_factor (+25% for compression)

    Args:
        f_y: Yield strength of steel (N/mm²)
        f_ck: Concrete characteristic compressive strength (N/mm²)
        bar_diameter_mm: Bar diameter phi (mm)
        is_hysd: True if deformed/HYSD bars (60% increase in tau_bd)
        is_compression: True if bar in compression (25% increase in tau_bd)

    Returns:
        DevelopmentLengthResult: Full component breakdown of bond stresses and Ld.

    Clause: IS 456:2000 Clause 26.2.1 & Clause 26.2.1.1
    """
    tau_bd_plain, hysd_factor, comp_factor, tau_bd_design = get_bond_stress_breakdown(
        f_ck, is_hysd=is_hysd, is_compression=is_compression
    )
    sigma_s = 0.87 * f_y
    ld_ratio = sigma_s / (4.0 * tau_bd_design)
    ld_mm = ld_ratio * bar_diameter_mm

    return DevelopmentLengthResult(
        tau_bd_plain_Nmm2=tau_bd_plain,
        hysd_factor=hysd_factor,
        compression_factor=comp_factor,
        tau_bd_design_Nmm2=tau_bd_design,
        sigma_s_Nmm2=sigma_s,
        bar_diameter_mm=bar_diameter_mm,
        ld_mm=ld_mm,
        ld_phi_ratio=ld_ratio,
        clause="IS 456:2000 Cl 26.2.1 & Cl 26.2.1.1",
    )


def calculate_deflection_limits(
    geometry: BeamGeometry,
    materials: MaterialProperties,
    Ast_req_mm2: float,
    Ast_provided_mm2: float,
    Asc_provided_mm2: float = 0.0,
) -> DeflectionCheckResult:
    """
    Calculates basic and allowable span-to-effective-depth ratio (L/d) for deflection control.

    Accounts for:
    - Clause 23.2.1 basic L/d values (Cantilever=7, Simply Supported=20, Continuous=26)
    - Clause 23.2.1 span > 10m modification factor (10 / span_m)
    - Figure 4 modification factor F1 for tension reinforcement (via digitized 2D grid)
    - Figure 5 modification factor F2 for compression reinforcement (via digitized 1D grid)
    - Figure 6 modification factor F3 for flanged beams (marked as NOT_IMPLEMENTED for Phase 1)

    Args:
        geometry: Beam dimensions, effective depth, and support condition
        materials: Material properties f_y, f_ck
        Ast_req_mm2: Required tension reinforcement area (mm²)
        Ast_provided_mm2: Provided tension reinforcement area (mm²)
        Asc_provided_mm2: Provided compression reinforcement area (mm²), default 0.0

    Returns:
        DeflectionCheckResult: Detailed deflection evaluation result.

    Clause: IS 456:2000 Clause 23.2.1, Figure 4, Figure 5
    """
    # 1. Basic L/d ratio based on support condition (Cl 23.2.1)
    if geometry.support_condition == SupportCondition.CANTILEVER:
        basic_ratio = 7.0
    elif geometry.support_condition == SupportCondition.CONTINUOUS:
        basic_ratio = 26.0
    else:
        basic_ratio = 20.0

    # 2. Adjustment for spans > 10 m (Clause 23.2.1)
    span_10m_factor = 1.0
    if geometry.span is not None and geometry.span > 10000.0:
        if geometry.support_condition != SupportCondition.CANTILEVER:
            span_10m_factor = 10000.0 / geometry.span
            basic_ratio *= span_10m_factor

    # 3. Design stress in tension steel fs = 0.58 * f_y * (Ast_req / Ast_prov) (Cl 23.2.1 a)
    ratio_ast = Ast_req_mm2 / max(Ast_provided_mm2, 1e-6)
    fs = 0.58 * materials.f_y * min(1.0, ratio_ast)

    # Percentage of tension steel pt = 100 * Ast_prov / (b * d)
    pt = (100.0 * Ast_provided_mm2) / (geometry.b * geometry.d)
    F1 = get_fig4_modification_factor_F1(pt_percent=pt, fs_Nmm2=fs)

    # Percentage of compression steel pc = 100 * Asc_prov / (b * d)
    pc = (100.0 * Asc_provided_mm2) / (geometry.b * geometry.d)
    F2 = get_fig5_modification_factor_F2(pc_percent=pc)

    # Overall allowable L/d ratio
    allowable_ratio = basic_ratio * F1 * F2

    actual_ratio = None
    status = CheckStatus.PASS
    if geometry.span is not None:
        actual_ratio = geometry.span / geometry.d
        if actual_ratio > allowable_ratio:
            status = CheckStatus.FAIL

    return DeflectionCheckResult(
        basic_span_depth_ratio=basic_ratio,
        span_10m_correction_factor=span_10m_factor,
        fs_Nmm2=fs,
        pt_provided_percent=pt,
        pc_provided_percent=pc,
        modification_factor_F1_tension=F1,
        modification_factor_F2_compression=F2,
        modification_factor_F3_flanged_status=CheckStatus.NOT_IMPLEMENTED,
        allowable_span_depth_ratio=allowable_ratio,
        actual_span_depth_ratio=actual_ratio,
        status=status,
        clause="IS 456:2000 Cl 23.2.1, Fig 4, Fig 5",
    )


def perform_detailing_checks(
    geometry: BeamGeometry,
    materials: MaterialProperties,
    flexure_res: FlexureDesignResult,
    shear_res: ShearDesignResult,
    Ast_provided_mm2: Optional[float] = None,
    Asc_provided_mm2: float = 0.0,
    stirrup_spacing_provided_mm: Optional[float] = None,
    main_bar_diameter_mm: float = 20.0,
) -> DetailingCheckResult:
    """
    Performs comprehensive detailing and code limit checks against IS 456:2000.

    Args:
        geometry: BeamGeometry
        materials: MaterialProperties
        flexure_res: Result of flexural design
        shear_res: Result of shear design
        Ast_provided_mm2: Provided tension steel area (mm²). Defaults to flexure_res.governing_Ast_mm2
        Asc_provided_mm2: Provided compression steel area (mm²). Defaults to 0.0
        stirrup_spacing_provided_mm: Provided stirrup spacing (mm). Defaults to shear_res.governing_max_spacing_mm
        main_bar_diameter_mm: Diameter of main tension bar (mm) for development length calculation

    Returns:
        DetailingCheckResult with individual CodeCheckResult items.
    """
    code_checks: List[CodeCheckResult] = []
    clauses: List[str] = [
        "IS 456:2000 Clause 26.2.1 (Development Length)",
        "IS 456:2000 Clause 23.2.1 (Control of Deflection - Fig 4 & Fig 5)",
        "IS 456:2000 Clause 26.5.1.1 (a & b) (Tension Reinforcement Limits)",
        "IS 456:2000 Clause 26.5.1.5 (Maximum Stirrup Spacing)",
        "IS 456:2000 Clause 26.5.1.6 (Minimum Shear Reinforcement)",
        "IS 456:2000 Clause 40.2.3 (Maximum Shear Stress)",
    ]

    Ast_prov = Ast_provided_mm2 if Ast_provided_mm2 is not None else flexure_res.governing_Ast_mm2
    sv_prov = stirrup_spacing_provided_mm if stirrup_spacing_provided_mm is not None else shear_res.governing_max_spacing_mm

    # Check 1: Minimum Tension Reinforcement (Cl 26.5.1.1 a)
    min_ast_pass = Ast_prov >= flexure_res.Ast_min_mm2
    code_checks.append(
        CodeCheckResult(
            check_name="Minimum Tension Reinforcement",
            clause="IS 456:2000 Cl 26.5.1.1 (a)",
            status=CheckStatus.PASS if min_ast_pass else CheckStatus.FAIL,
            demand=flexure_res.Ast_min_mm2,
            capacity=Ast_prov,
            unit="mm²",
            message=f"Provided Ast ({Ast_prov:.1f} mm²) >= Minimum Ast ({flexure_res.Ast_min_mm2:.1f} mm²)"
            if min_ast_pass
            else f"Provided Ast ({Ast_prov:.1f} mm²) < Minimum Ast ({flexure_res.Ast_min_mm2:.1f} mm²)",
        )
    )

    # Check 2: Maximum Tension Reinforcement (Cl 26.5.1.1 b)
    max_ast_pass = Ast_prov <= flexure_res.Ast_max_mm2
    code_checks.append(
        CodeCheckResult(
            check_name="Maximum Tension Reinforcement",
            clause="IS 456:2000 Cl 26.5.1.1 (b)",
            status=CheckStatus.PASS if max_ast_pass else CheckStatus.FAIL,
            demand=Ast_prov,
            capacity=flexure_res.Ast_max_mm2,
            unit="mm²",
            message=f"Provided Ast ({Ast_prov:.1f} mm²) <= Maximum Ast ({flexure_res.Ast_max_mm2:.1f} mm²)"
            if max_ast_pass
            else f"Provided Ast ({Ast_prov:.1f} mm²) > Maximum Ast ({flexure_res.Ast_max_mm2:.1f} mm²)",
        )
    )

    # Check 3: Maximum Shear Stress Check (Cl 40.2.3)
    tau_v_pass = shear_res.is_section_safe_in_shear
    code_checks.append(
        CodeCheckResult(
            check_name="Maximum Shear Stress",
            clause="IS 456:2000 Cl 40.2.3 & Table 20",
            status=CheckStatus.PASS if tau_v_pass else CheckStatus.FAIL,
            demand=shear_res.tau_v_Nmm2,
            capacity=shear_res.tau_c_max_Nmm2,
            unit="N/mm²",
            message=f"Nominal shear stress tau_v ({shear_res.tau_v_Nmm2:.3f} N/mm²) <= tau_c_max ({shear_res.tau_c_max_Nmm2:.3f} N/mm²)"
            if tau_v_pass
            else f"CRITICAL: Nominal shear stress tau_v ({shear_res.tau_v_Nmm2:.3f} N/mm²) > tau_c_max ({shear_res.tau_c_max_Nmm2:.3f} N/mm²)",
        )
    )

    # Check 4a: Maximum Stirrup Spacing Code Limit (Cl 26.5.1.5)
    code_spacing_pass = sv_prov <= shear_res.sv_max_code_limit_mm + 1e-3
    code_checks.append(
        CodeCheckResult(
            check_name="Maximum Stirrup Spacing (Code Limit)",
            clause="IS 456:2000 Cl 26.5.1.5",
            status=CheckStatus.PASS if code_spacing_pass else CheckStatus.FAIL,
            demand=sv_prov,
            capacity=shear_res.sv_max_code_limit_mm,
            unit="mm",
            message=f"Stirrup spacing ({sv_prov:.1f} mm) <= min(0.75d, 300mm) ({shear_res.sv_max_code_limit_mm:.1f} mm)"
            if code_spacing_pass
            else f"Stirrup spacing ({sv_prov:.1f} mm) > min(0.75d, 300mm) ({shear_res.sv_max_code_limit_mm:.1f} mm)",
        )
    )

    # Check 4b: Required Stirrup Spacing for Shear Strength (Cl 40.4)
    if shear_res.shear_reinforcement_required and shear_res.sv_req_calc_mm is not None:
        strength_spacing_pass = sv_prov <= shear_res.sv_req_calc_mm + 1e-3
        code_checks.append(
            CodeCheckResult(
                check_name="Stirrup Spacing for Shear Strength",
                clause="IS 456:2000 Cl 40.4",
                status=CheckStatus.PASS if strength_spacing_pass else CheckStatus.FAIL,
                demand=sv_prov,
                capacity=shear_res.sv_req_calc_mm,
                unit="mm",
                message=f"Provided stirrup spacing ({sv_prov:.1f} mm) <= Required spacing for shear strength V_us ({shear_res.sv_req_calc_mm:.1f} mm)"
                if strength_spacing_pass
                else f"Provided stirrup spacing ({sv_prov:.1f} mm) > Required spacing for shear strength V_us ({shear_res.sv_req_calc_mm:.1f} mm)",
            )
        )
    else:
        code_checks.append(
            CodeCheckResult(
                check_name="Stirrup Spacing for Shear Strength",
                clause="IS 456:2000 Cl 40.4",
                status=CheckStatus.NOT_APPLICABLE,
                demand=0.0,
                capacity=shear_res.governing_max_spacing_mm,
                unit="mm",
                message=f"Nominal shear stress tau_v ({shear_res.tau_v_Nmm2:.3f} N/mm²) <= tau_c ({shear_res.tau_c_Nmm2:.3f} N/mm²); stirrups not required for net shear strength.",
            )
        )

    # Check 5: Minimum Shear Reinforcement Spacing Limit (Cl 26.5.1.6)
    min_shear_pass = sv_prov <= shear_res.sv_req_min_rebar_mm + 1e-3
    code_checks.append(
        CodeCheckResult(
            check_name="Minimum Shear Reinforcement Spacing",
            clause="IS 456:2000 Cl 26.5.1.6",
            status=CheckStatus.PASS if min_shear_pass else CheckStatus.FAIL,
            demand=sv_prov,
            capacity=shear_res.sv_req_min_rebar_mm,
            unit="mm",
            message=f"Stirrup spacing ({sv_prov:.1f} mm) <= Minimum shear rebar spacing limit ({shear_res.sv_req_min_rebar_mm:.1f} mm)"
            if min_shear_pass
            else f"Stirrup spacing ({sv_prov:.1f} mm) > Minimum shear rebar spacing limit ({shear_res.sv_req_min_rebar_mm:.1f} mm)",
        )
    )

    # Check 6: Development Length Check (Cl 26.2.1)
    dev_length_res = calculate_development_length(
        materials.f_y, materials.f_ck, bar_diameter_mm=main_bar_diameter_mm, is_hysd=materials.is_hysd
    )
    code_checks.append(
        CodeCheckResult(
            check_name="Development Length Ld",
            clause="IS 456:2000 Cl 26.2.1",
            status=CheckStatus.PASS,
            demand=dev_length_res.ld_mm,
            capacity=dev_length_res.ld_mm,
            unit="mm",
            message=f"Required development length Ld = {dev_length_res.ld_mm:.1f} mm ({dev_length_res.ld_phi_ratio:.1f} * bar diameter)",
            details={
                "ld_ratio": dev_length_res.ld_phi_ratio,
                "bar_diameter_mm": main_bar_diameter_mm,
                "tau_bd_plain": dev_length_res.tau_bd_plain_Nmm2,
                "hysd_factor": dev_length_res.hysd_factor,
                "tau_bd_design": dev_length_res.tau_bd_design_Nmm2,
            },
        )
    )

    # Check 7: Span-to-Effective-Depth Deflection Check (Cl 23.2.1)
    defl_res = calculate_deflection_limits(
        geometry, materials, flexure_res.Ast_req_mm2, Ast_prov, Asc_provided_mm2=Asc_provided_mm2
    )
    
    if defl_res.actual_span_depth_ratio is not None:
        code_checks.append(
            CodeCheckResult(
                check_name="Deflection Span/Depth Ratio",
                clause="IS 456:2000 Cl 23.2.1",
                status=defl_res.status,
                demand=defl_res.actual_span_depth_ratio,
                capacity=defl_res.allowable_span_depth_ratio,
                unit="ratio",
                message=f"Actual L/d ({defl_res.actual_span_depth_ratio:.2f}) <= Allowable L/d ({defl_res.allowable_span_depth_ratio:.2f})"
                if defl_res.status == CheckStatus.PASS
                else f"Actual L/d ({defl_res.actual_span_depth_ratio:.2f}) > Allowable L/d ({defl_res.allowable_span_depth_ratio:.2f}) - Deflection check FAILS",
            )
        )
    else:
        code_checks.append(
            CodeCheckResult(
                check_name="Deflection Span/Depth Ratio",
                clause="IS 456:2000 Cl 23.2.1",
                status=CheckStatus.NOT_APPLICABLE,
                demand=0.0,
                capacity=defl_res.allowable_span_depth_ratio,
                unit="ratio",
                message=f"Allowable L/d ratio limit = {defl_res.allowable_span_depth_ratio:.2f} (Span length not provided)",
            )
        )

    # Check 8: Flanged Beam Deflection Factor (Fig 6)
    code_checks.append(
        CodeCheckResult(
            check_name="Flanged Beam Deflection Modification (Fig 6)",
            clause="IS 456:2000 Fig 6",
            status=CheckStatus.NOT_IMPLEMENTED,
            demand=0.0,
            capacity=1.0,
            unit="ratio",
            message="Flanged beam modification factor F3 (Fig 6) is NOT_IMPLEMENTED for Phase 1 (rectangular section).",
        )
    )

    return DetailingCheckResult(
        development_length=dev_length_res,
        deflection=defl_res,
        development_length_mm=dev_length_res.ld_mm,
        ld_phi_ratio=dev_length_res.ld_phi_ratio,
        basic_span_depth_ratio=defl_res.basic_span_depth_ratio,
        modification_factor_F1=defl_res.modification_factor_F1_tension,
        modification_factor_F2=defl_res.modification_factor_F2_compression,
        allowable_span_depth_ratio=defl_res.allowable_span_depth_ratio,
        actual_span_depth_ratio=defl_res.actual_span_depth_ratio,
        deflection_check_pass=(defl_res.status == CheckStatus.PASS) if defl_res.actual_span_depth_ratio is not None else None,
        code_checks=code_checks,
        clauses=clauses,
    )

