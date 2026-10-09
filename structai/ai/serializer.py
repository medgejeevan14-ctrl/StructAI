"""
Serialization layer for converting BeamDesignSummary dataclass into a clean,
JSON-compatible dictionary context payload for LLM prompts.
"""

from typing import Dict, Any
from structai.codes.is456.beam import BeamDesignSummary


def serialize_beam_design(summary: BeamDesignSummary) -> Dict[str, Any]:
    """
    Serializes a BeamDesignSummary into a clean, deterministic, JSON-compatible dictionary.

    Preserves:
    - Numerical values & units
    - Clause references
    - Check statuses (PASS, FAIL, WARNING, NOT_IMPLEMENTED)

    Does NOT perform new engineering calculations.
    """
    geom = summary.geometry
    mat = summary.materials
    loads = summary.loads
    flex = summary.flexure
    shear = summary.shear
    det = summary.detailing
    dev = det.development_length
    defl = det.deflection

    return {
        "overall_status": {
            "is_overall_pass": summary.is_overall_pass,
            "summary_notes": summary.summary_notes,
        },
        "geometry": {
            "width_b_mm": geom.b,
            "overall_depth_D_mm": geom.D,
            "effective_depth_d_mm": geom.d,
            "cover_d_prime_mm": geom.d_prime,
            "span_L_mm": geom.span,
            "support_condition": geom.support_condition.value,
        },
        "materials": {
            "f_ck_Nmm2": mat.f_ck,
            "f_y_Nmm2": mat.f_y,
            "f_yv_Nmm2": mat.f_yv,
            "E_s_Nmm2": mat.E_s,
            "is_hysd": mat.is_hysd,
        },
        "factored_loads": {
            "bending_moment_M_u_kNm": loads.M_u,
            "shear_force_V_u_kN": loads.V_u,
            "torsion_T_u_kNm": loads.T_u,
        },
        "flexure_design": {
            "M_u_kNm": flex.M_u_kNm,
            "M_u_lim_kNm": flex.M_u_lim_kNm,
            "xu_max_d_ratio": flex.xu_max_d_ratio,
            "xu_max_mm": flex.xu_max_mm,
            "xu_mm": flex.xu_mm,
            "is_under_reinforced": flex.is_under_reinforced,
            "is_doubly_reinforced_required": flex.is_doubly_reinforced_required,
            "Ast_req_mm2": flex.Ast_req_mm2,
            "Ast_min_mm2": flex.Ast_min_mm2,
            "Ast_max_mm2": flex.Ast_max_mm2,
            "pt_req_percent": flex.pt_req_percent,
            "governing_Ast_mm2": flex.governing_Ast_mm2,
            "clauses": flex.clauses,
            "notes": flex.notes,
        },
        "shear_design": {
            "V_u_kN": shear.V_u_kN,
            "tau_v_Nmm2": shear.tau_v_Nmm2,
            "tau_c_Nmm2": shear.tau_c_Nmm2,
            "tau_c_max_Nmm2": shear.tau_c_max_Nmm2,
            "pt_provided_percent": shear.pt_provided_percent,
            "shear_reinforcement_required": shear.shear_reinforcement_required,
            "is_section_safe_in_shear": shear.is_section_safe_in_shear,
            "V_us_kN": shear.V_us_kN,
            "sv_req_calc_mm": shear.sv_req_calc_mm,
            "sv_req_min_rebar_mm": shear.sv_req_min_rebar_mm,
            "sv_max_code_limit_mm": shear.sv_max_code_limit_mm,
            "governing_max_spacing_mm": shear.governing_max_spacing_mm,
            "clauses": shear.clauses,
            "notes": shear.notes,
        },
        "detailing_and_serviceability": {
            "development_length": {
                "tau_bd_plain_Nmm2": dev.tau_bd_plain_Nmm2,
                "hysd_factor": dev.hysd_factor,
                "compression_factor": dev.compression_factor,
                "tau_bd_design_Nmm2": dev.tau_bd_design_Nmm2,
                "sigma_s_Nmm2": dev.sigma_s_Nmm2,
                "bar_diameter_mm": dev.bar_diameter_mm,
                "ld_mm": dev.ld_mm,
                "ld_phi_ratio": dev.ld_phi_ratio,
                "clause": dev.clause,
            },
            "deflection_check": {
                "basic_span_depth_ratio": defl.basic_span_depth_ratio,
                "span_10m_correction_factor": defl.span_10m_correction_factor,
                "fs_Nmm2": defl.fs_Nmm2,
                "pt_provided_percent": defl.pt_provided_percent,
                "pc_provided_percent": defl.pc_provided_percent,
                "modification_factor_F1_tension": defl.modification_factor_F1_tension,
                "modification_factor_F2_compression": defl.modification_factor_F2_compression,
                "modification_factor_F3_flanged_status": defl.modification_factor_F3_flanged_status.value,
                "allowable_span_depth_ratio": defl.allowable_span_depth_ratio,
                "actual_span_depth_ratio": defl.actual_span_depth_ratio,
                "status": defl.status.value,
                "clause": defl.clause,
            },
            "code_checks": [
                {
                    "check_name": chk.check_name,
                    "clause": chk.clause,
                    "status": chk.status.value,
                    "demand": chk.demand,
                    "capacity": chk.capacity,
                    "unit": chk.unit,
                    "message": chk.message,
                }
                for chk in det.code_checks
            ],
            "clauses": det.clauses,
        },
    }
