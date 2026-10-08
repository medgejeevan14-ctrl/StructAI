import os
import sys
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    SupportCondition,
)
from structai.codes.is456.beam import IS456BeamDesignEngine


def run_sample_calculation():
    print("=" * 80)
    print("        STRUCTAI: IS 456:2000 MANUALLY VERIFIABLE BEAM DESIGN SAMPLE")
    print("=" * 80)

    # Problem Inputs:
    # Width b = 300 mm
    # Overall Depth D = 550 mm
    # Effective Depth d = 500 mm (Cover = 50 mm)
    # Span L = 6.0 m = 6000 mm (Simply Supported)
    # Concrete Grade f_ck = 25 N/mm² (M25)
    # Main Steel Grade f_y = 500 N/mm² (Fe 500)
    # Stirrup Steel Grade f_yv = 415 N/mm² (Fe 415)
    # Factored Ultimate Bending Moment M_u = 150.0 kNm
    # Factored Ultimate Shear Force V_u = 95.0 kN

    geom = BeamGeometry(
        b=300.0,
        D=550.0,
        d=500.0,
        d_prime=50.0,
        span=6000.0,
        support_condition=SupportCondition.SIMPLY_SUPPORTED,
    )
    materials = MaterialProperties(
        f_ck=25.0,
        f_y=500.0,
        f_yv=415.0,
        is_hysd=True,
    )
    loads = FactoredLoads(
        M_u=150.0,
        V_u=95.0,
    )
    stirrups = StirrupDetails(
        num_legs=2,
        bar_diameter=8.0,
        spacing=150.0,
    )

    print("\n1. INPUT DESIGN PARAMETERS:")
    print("-" * 50)
    print(f"  Beam Width (b)               : {geom.b} mm")
    print(f"  Overall Depth (D)            : {geom.D} mm")
    print(f"  Effective Depth (d)          : {geom.d} mm")
    print(f"  Effective Span (L)           : {geom.span} mm ({geom.span/1000:.1f} m)")
    print(f"  Support Condition            : {geom.support_condition.value}")
    print(f"  Concrete Grade (f_ck)        : {materials.f_ck} N/mm2 (M25)")
    print(f"  Main Steel Grade (f_y)       : {materials.f_y} N/mm2 (Fe 500)")
    print(f"  Stirrup Steel Grade (f_yv)   : {materials.f_yv} N/mm2 (Fe 415)")
    print(f"  Factored Bending Moment (M_u): {loads.M_u} kNm ({loads.M_u_Nmm:.2e} N*mm)")
    print(f"  Factored Shear Force (V_u)   : {loads.V_u} kN ({loads.V_u_N:.2e} N)")

    engine = IS456BeamDesignEngine(
        geometry=geom,
        materials=materials,
        loads=loads,
        stirrup_details=stirrups,
        stirrup_spacing_provided_mm=150.0,
        main_bar_diameter_mm=20.0,
    )

    summary = engine.run_design()
    flex = summary.flexure
    shear = summary.shear
    det = summary.detailing

    print("\n2. FLEXURAL DESIGN INTERMEDIATE CALCULATIONS (Annex G & Cl 38.1):")
    print("-" * 50)
    print(f"  [Cl 38.1 Note] Limiting Neutral Axis Ratio (xu_max/d) : {flex.xu_max_d_ratio}")
    print(f"  [Cl 38.1] Limiting Neutral Axis Depth (xu_max)        : {flex.xu_max_mm:.2f} mm")
    print(f"  [Annex G-1.1 c] Limiting Moment Capacity (M_u_lim)    : {flex.M_u_lim_kNm:.2f} kNm")
    print(f"  Section Status wrt M_u_lim                             : {'Singly Reinforced (M_u <= M_u_lim)' if not flex.is_doubly_reinforced_required else 'Doubly Reinforced Required (M_u > M_u_lim)'}")
    print(f"  [Annex G-1.1 b] Required Tension Steel (Ast_req)     : {flex.Ast_req_mm2:.2f} mm2")
    print(f"  [Cl 38.1] Actual Neutral Axis Depth (xu)             : {flex.xu_mm:.2f} mm")
    print(f"  [Cl 26.5.1.1 a] Minimum Tension Steel (Ast_min)        : {flex.Ast_min_mm2:.2f} mm2")
    print(f"  [Cl 26.5.1.1 b] Maximum Tension Steel (Ast_max)        : {flex.Ast_max_mm2:.2f} mm2")
    print(f"  Governing Design Tension Steel Area (Ast_gov)         : {flex.governing_Ast_mm2:.2f} mm2")
    print(f"  Reinforcement Ratio pt = 100*Ast/(b*d)                : {flex.pt_req_percent:.3f} %")

    print("\n3. SHEAR DESIGN INTERMEDIATE CALCULATIONS (Cl 40 & Cl 26.5.1):")
    print("-" * 50)
    print(f"  [Cl 40.1] Nominal Shear Stress (tau_v = V_u / b*d)    : {shear.tau_v_Nmm2:.3f} N/mm2")
    print(f"  [Cl 40.2.3 Table 20] Max Permissible Shear (tau_c_max): {shear.tau_c_max_Nmm2:.3f} N/mm2")
    print(f"  [Cl 40.2.3] Shear Stress Limit Check                  : {'SAFE (tau_v <= tau_c_max)' if shear.is_section_safe_in_shear else 'UNSAFE (tau_v > tau_c_max)'}")
    print(f"  [Cl 40.2.1 Table 19] Design Shear Strength (tau_c)   : {shear.tau_c_Nmm2:.3f} N/mm2 (interpolated for pt={shear.pt_provided_percent:.3f}%, M25)")
    print(f"  Shear Reinforcement Requirement                       : {'Shear Stirrups Required (tau_v > tau_c)' if shear.shear_reinforcement_required else 'Nominal Minimum Stirrups Required (tau_v <= tau_c)'}")
    print(f"  [Cl 40.4] Net Shear Force Carried by Steel (V_us)     : {shear.V_us_kN:.2f} kN")
    if shear.sv_req_calc_mm is not None:
        print(f"  [Cl 40.4 a] Calculated Stirrup Spacing for V_us       : {shear.sv_req_calc_mm:.1f} mm")
    print(f"  [Cl 26.5.1.6] Min Shear Steel Spacing Limit (sv_min) : {shear.sv_req_min_rebar_mm:.1f} mm (for 2-leg 8mm stirrup, Asv=100.53 mm2)")
    print(f"  [Cl 26.5.1.5] Maximum Spacing Code Limit (sv_max_code): {shear.sv_max_code_limit_mm:.1f} mm (min of 0.75d={0.75*geom.d}mm, 300mm)")
    print(f"  Governing Maximum Permissible Spacing                 : {shear.governing_max_spacing_mm:.1f} mm")

    print("\n4. DETAILING & CODE COMPLIANCE CHECKS:")
    print("-" * 50)
    print(f"  [Cl 26.2.1] Development Length (L_d for 20mm bar)     : {det.development_length_mm:.1f} mm (Ratio L_d/phi = {det.ld_phi_ratio:.1f})")
    print(f"  [Cl 23.2.1] Basic Span/Depth Ratio ((L/d)_basic)      : {det.basic_span_depth_ratio:.1f}")
    print(f"  [Cl 23.2.1 a] Tension Steel Modification Factor (F1)  : {det.modification_factor_F1:.3f}")
    print(f"  [Cl 23.2.1] Allowable Span/Depth Ratio ((L/d)_allow)  : {det.allowable_span_depth_ratio:.2f}")
    print(f"  Actual Span/Depth Ratio ((L/d)_actual)                : {det.actual_span_depth_ratio:.2f}")

    print("\n5. CODE CHECKS SUMMARY TABLE:")
    print("-" * 80)
    print(f"{'CHECK NAME':<38} | {'STATUS':<7} | {'DEMAND / CAP':<18} | {'CLAUSE':<22}")
    print("-" * 80)
    for chk in det.code_checks:
        unit_str = chk.unit.replace("²", "2")
        demand_cap = f"{chk.demand:.2f} / {chk.capacity:.2f} {unit_str}"
        print(f"{chk.check_name:<38} | {chk.status.value:<7} | {demand_cap:<18} | {chk.clause:<22}")
    print("-" * 80)

    print(f"\nOVERALL DESIGN RESULT: {'>>> PASS <<<' if summary.is_overall_pass else '>>> FAIL <<<'}")
    print("=" * 80)


if __name__ == "__main__":
    run_sample_calculation()
