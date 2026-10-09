"""
StructAI — Interactive IS 456:2000 Beam Design & AI Compliance Dashboard
Streamlit User Interface for Rectangular RC Beam Design.
"""

import os
import streamlit as st

from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    SupportCondition,
    CheckStatus,
)
from structai.codes.is456.beam import IS456BeamDesignEngine, BeamDesignSummary
from structai.ai.assistant import explain_beam_design
from structai.ai.client import AnthropicAIClient, StructAIConfigurationError, StructAIAIClientError


def format_status_badge(status: CheckStatus) -> str:
    """Formats CheckStatus enum into colorized HTML status badge."""
    color_map = {
        CheckStatus.PASS: "#1e7e34",  # Green
        CheckStatus.FAIL: "#bd2130",  # Red
        CheckStatus.WARNING: "#d39e00",  # Yellow/Amber
        CheckStatus.NOT_APPLICABLE: "#6c757d",  # Gray
        CheckStatus.NOT_IMPLEMENTED: "#6c757d",  # Gray
    }
    color = color_map.get(status, "#6c757d")
    return f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem;">{status.value}</span>'


def main():
    st.set_page_config(
        page_title="StructAI — IS 456:2000 Beam Design & AI Assistant",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Title Banner
    st.title("🏗️ StructAI — Rectangular Beam Design Engine")
    st.caption("IS 456:2000 Code Compliance Auditor & AI Engineering Assistant | v0.1.0")

    st.markdown(
        """
        <div style="background-color: #f8f9fa; border-left: 4px solid #0d6efd; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
            <strong>Engineering Compliance Notice:</strong> Calculations are strictly performed by the deterministic 
            <strong>StructAI IS 456 Engine</strong>. The AI layer provides narrative technical rationale and does not modify structural outputs.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Controls
    st.sidebar.header("📐 Input Telemetry")

    with st.sidebar.expander("1. Beam Geometry", expanded=True):
        b = st.number_input("Width b (mm)", min_value=100.0, max_value=2000.0, value=300.0, step=25.0)
        D = st.number_input("Overall Depth D (mm)", min_value=150.0, max_value=3000.0, value=600.0, step=25.0)
        d = st.number_input("Effective Depth d (mm)", min_value=100.0, max_value=2900.0, value=550.0, step=25.0)
        d_prime = st.number_input("Compression Cover d' (mm)", min_value=20.0, max_value=150.0, value=40.0, step=5.0)
        span = st.number_input("Beam Span L (mm)", min_value=500.0, max_value=30000.0, value=6000.0, step=500.0)
        support_cond_str = st.selectbox(
            "Support Condition",
            options=["SIMPLY_SUPPORTED", "CANTILEVER", "CONTINUOUS"],
            index=0,
        )

    with st.sidebar.expander("2. Material Properties", expanded=True):
        f_ck = st.selectbox("Concrete Grade f_ck (N/mm²)", options=[20.0, 25.0, 30.0, 35.0, 40.0], index=1)
        f_y = st.selectbox("Main Steel Grade f_y (N/mm²)", options=[250.0, 415.0, 500.0, 550.0], index=2)
        f_yv = st.number_input("Stirrup Steel Grade f_yv (N/mm²)", min_value=210.0, max_value=600.0, value=500.0, step=25.0)
        is_hysd = st.checkbox("HYSD / TMT Deformed Bars", value=True)

    with st.sidebar.expander("3. Factored Ultimate Loads", expanded=True):
        M_u = st.number_input("Factored Moment M_u (kNm)", min_value=0.0, value=150.0, step=10.0)
        V_u = st.number_input("Factored Shear V_u (kN)", min_value=0.0, value=80.0, step=5.0)
        T_u = st.number_input("Factored Torsion T_u (kNm)", min_value=0.0, value=0.0, step=5.0)

    with st.sidebar.expander("4. Provided Reinforcement & Stirrups", expanded=False):
        enable_provided_details = st.checkbox("Specify Provided Rebar Details", value=True)
        main_bar_dia = st.selectbox("Main Bar Diameter (mm)", options=[12.0, 16.0, 20.0, 25.0, 28.0, 32.0], index=2)
        ast_prov_input = st.number_input(
            "Provided Ast (mm²)",
            min_value=0.0,
            value=0.0,
            help="Set to 0 to auto-use required governing steel area for shear & detailing checks.",
        )
        stirrup_legs = st.selectbox("Stirrup Legs", options=[2, 4], index=0)
        stirrup_dia = st.selectbox("Stirrup Bar Diameter (mm)", options=[6.0, 8.0, 10.0, 12.0], index=1)
        stirrup_spacing = st.number_input("Provided Stirrup Spacing (mm)", min_value=50.0, max_value=450.0, value=150.0, step=25.0)

    with st.sidebar.expander("🤖 AI Environment Settings", expanded=False):
        user_api_key = st.text_input(
            "Anthropic API Key (Optional)",
            type="password",
            help="Overrides ANTHROPIC_API_KEY environment variable if provided.",
        )

    # Build Domain Inputs & Run Engine
    try:
        support_cond = SupportCondition[support_cond_str]
        geom = BeamGeometry(
            b=b,
            D=D,
            d=d,
            d_prime=d_prime,
            span=span,
            support_condition=support_cond,
        )
        materials = MaterialProperties(
            f_ck=f_ck,
            f_y=f_y,
            f_yv=f_yv,
            is_hysd=is_hysd,
        )
        loads = FactoredLoads(
            M_u=M_u,
            V_u=V_u,
            T_u=T_u,
        )
        stirrups = (
            StirrupDetails(
                num_legs=stirrup_legs,
                bar_diameter=stirrup_dia,
                spacing=stirrup_spacing,
            )
            if enable_provided_details
            else None
        )

        engine = IS456BeamDesignEngine(
            geometry=geom,
            materials=materials,
            loads=loads,
            stirrup_details=stirrups,
            Ast_provided_mm2=ast_prov_input if ast_prov_input > 0 else None,
            stirrup_spacing_provided_mm=stirrup_spacing if enable_provided_details else None,
            main_bar_diameter_mm=main_bar_dia,
        )
        summary: BeamDesignSummary = engine.run_design()
    except Exception as e:
        st.error(f"Configuration Error in Beam Inputs: {e}")
        return

    # Render Overall Status Banner
    has_failed_check = any(c.status == CheckStatus.FAIL for c in summary.detailing.code_checks)
    has_unimplemented = any(c.status == CheckStatus.NOT_IMPLEMENTED for c in summary.detailing.code_checks)

    if summary.is_overall_pass:
        st.success("### ✅ IS 456:2000 BEAM DESIGN COMPLIANT — ALL CODE CHECKS PASSED")
    elif has_failed_check or summary.flexure.is_doubly_reinforced_required:
        st.error("### ❌ IS 456:2000 BEAM DESIGN NON-COMPLIANT — MANDATORY CODE CHECK(S) FAILED")
    elif has_unimplemented:
        st.warning("### ⚠️ IS 456:2000 BEAM DESIGN INCOMPLETE — UNIMPLEMENTED CODE PROVISION(S) EXIST")
    else:
        st.error("### ❌ IS 456:2000 BEAM DESIGN NON-COMPLIANT — ACTION REQUIRED")

    if summary.summary_notes:
        with st.expander("📋 Design Summary & Engine Warnings", expanded=not summary.is_overall_pass):
            for note in summary.summary_notes:
                st.write(f"- {note}")

    # Top Metric Dashboard Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Gov. Required Ast",
            value=f"{summary.flexure.governing_Ast_mm2:.1f} mm²",
            delta=f"min {summary.flexure.Ast_min_mm2:.0f} | max {summary.flexure.Ast_max_mm2:.0f}",
        )
    with col2:
        st.metric(
            label="Nominal Shear τ_v",
            value=f"{summary.shear.tau_v_Nmm2:.3f} N/mm²",
            delta=f"τ_c_max = {summary.shear.tau_c_max_Nmm2:.3f} N/mm²",
        )
    with col3:
        st.metric(
            label="Development Length L_d",
            value=f"{summary.detailing.development_length.ld_mm:.1f} mm",
            delta=f"{summary.detailing.development_length.ld_phi_ratio:.1f} × bar dia",
        )
    with col4:
        act_ratio = summary.detailing.deflection.actual_span_depth_ratio
        act_str = f"{act_ratio:.2f}" if act_ratio is not None else "N/A"
        st.metric(
            label="Deflection L/d Ratio",
            value=act_str,
            delta=f"Allowable = {summary.detailing.deflection.allowable_span_depth_ratio:.2f}",
        )

    # Detailed Module Tabs
    tab_flex, tab_shear, tab_det, tab_ai = st.tabs([
        "📊 Flexural Design (Annex G)",
        "✂️ Shear Design (Cl 40)",
        "📐 Detailing & Audit (Cl 23 & 26)",
        "🤖 AI Explanation (Claude)",
    ])

    # Tab 1: Flexure
    with tab_flex:
        st.subheader("Flexural State Limit Evaluation (IS 456:2000 Annex G & Clause 38.1)")
        flex = summary.flexure
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            st.write(f"**Applied Factored Bending Moment ($M_u$):** `{flex.M_u_kNm:.2f} kNm`")
            st.write(f"**Limiting Bending Moment ($M_{{u,lim}}$):** `{flex.M_u_lim_kNm:.2f} kNm`")
            st.write(f"**Max Neutral Axis Ratio ($x_{{u,max}}/d$):** `{flex.xu_max_d_ratio:.3f}`")
            st.write(f"**Max Neutral Axis Depth ($x_{{u,max}}$):** `{flex.xu_max_mm:.2f} mm`")
            st.write(f"**Actual Neutral Axis Depth ($x_u$):** `{flex.xu_mm:.2f} mm`")

        with fcol2:
            st.write(f"**Under-Reinforced Section:** `{'Yes' if flex.is_under_reinforced else 'No'}`")
            st.write(f"**Doubly Reinforced Required:** `{'Yes (Mu > Mu_lim)' if flex.is_doubly_reinforced_required else 'No'}`")
            st.write(f"**Calculated Required Steel ($A_{{st,req}}$):** `{flex.Ast_req_mm2:.2f} mm²`")
            st.write(f"**Minimum Code Tension Steel ($A_{{st,min}}$):** `{flex.Ast_min_mm2:.2f} mm²`")
            st.write(f"**Maximum Code Tension Steel ($A_{{st,max}}$):** `{flex.Ast_max_mm2:.2f} mm²`")
            st.write(f"**Required Tension Steel Percentage ($p_t$):** `{flex.pt_req_percent:.3f} %`")

        st.markdown("#### Governing IS 456 Clauses")
        for cl in flex.clauses:
            st.caption(f"• {cl}")

    # Tab 2: Shear
    with tab_shear:
        st.subheader("Shear Limit State Evaluation (IS 456:2000 Clause 40 & 26.5.1)")
        shear = summary.shear
        
        # Calculate governing permissible stirrup spacing limit
        if shear.shear_reinforcement_required and shear.sv_req_calc_mm is not None:
            gov_permissible_spacing = min(shear.sv_req_calc_mm, shear.governing_max_spacing_mm)
        else:
            gov_permissible_spacing = shear.governing_max_spacing_mm

        scol1, scol2 = st.columns(2)
        with scol1:
            st.markdown("##### 🔍 Shear Stresses & Capacity")
            st.write(f"**Applied Factored Shear Force ($V_u$):** `{shear.V_u_kN:.2f} kN`")
            st.write(f"**Nominal Shear Stress ($\tau_v$):** `{shear.tau_v_Nmm2:.3f} N/mm²`")
            st.write(f"**Concrete Design Shear Strength ($\tau_c$):** `{shear.tau_c_Nmm2:.3f} N/mm²` (Table 19 2D interpolation)")
            st.write(f"**Max Permissible Shear Stress ($\tau_{{c,max}}$):** `{shear.tau_c_max_Nmm2:.3f} N/mm²` (Table 20)")
            st.write(f"**Tension Steel Percentage ($p_t$):** `{shear.pt_provided_percent:.3f} %`")
            st.write(f"**Section Safe in Shear ($\tau_v \le \tau_{{c,max}}$):** `{'Yes' if shear.is_section_safe_in_shear else 'NO - SECTION FAILS'}`")

        with scol2:
            st.markdown("##### 📏 Stirrup Spacing Requirements")
            st.write(f"**Shear Reinforcement Required:** `{'Yes (τv > τc)' if shear.shear_reinforcement_required else 'No (Minimum stirrups apply)'}`")
            st.write(f"**Net Shear Force for Steel ($V_{{us}}$):** `{shear.V_us_kN:.2f} kN`")
            calc_sv_str = f"{shear.sv_req_calc_mm:.1f} mm" if shear.sv_req_calc_mm is not None else "N/A (τv ≤ τc)"
            st.write(f"**1. Required Spacing for Net Shear $V_{{us}}$ ($s_{{v,calc}}$):** `{calc_sv_str}` (Cl 40.4)")
            st.write(f"**2. Minimum Rebar Spacing Limit ($s_{{v,min\\_rebar}}$):** `{shear.sv_req_min_rebar_mm:.1f} mm` (Cl 26.5.1.6)")
            st.write(f"**3. Maximum Code Spacing Limit ($s_{{v,max\\_code}}$):** `{shear.sv_max_code_limit_mm:.1f} mm` (min(0.75d, 300 mm), Cl 26.5.1.5)")
            st.markdown(f"👉 **Governing Permissible Spacing Limit:** `<span style='color: #0d6efd; font-weight: bold;'>{gov_permissible_spacing:.1f} mm</span>`", unsafe_allow_html=True)

        if enable_provided_details:
            st.markdown("---")
            st.markdown("##### 📐 Provided Stirrup Spacing Audit")
            prov_sp = stirrup_spacing
            if prov_sp <= gov_permissible_spacing + 1e-3:
                st.success(
                    f"✅ **Provided Stirrup Spacing ({prov_sp:.1f} mm)** ≤ Governing Permissible Limit ({gov_permissible_spacing:.1f} mm) — **STIRRUP SPACING COMPLIANT**"
                )
            else:
                st.error(
                    f"❌ **Provided Stirrup Spacing ({prov_sp:.1f} mm)** > Governing Permissible Limit ({gov_permissible_spacing:.1f} mm) — **STIRRUP SPACING EXCEEDED (FAILS)**"
                )

        st.markdown("#### Governing IS 456 Clauses")
        for cl in shear.clauses:
            st.caption(f"• {cl}")

    # Tab 3: Detailing & Code Audit
    with tab_det:
        st.subheader("Detailing & Serviceability Compliance Audit")
        det = summary.detailing
        dev = det.development_length
        defl = det.deflection

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.markdown("##### 📌 Development Length (IS 456 Cl 26.2.1)")
            st.write(f"**Plain Bar Base Bond Stress ($\tau_{{bd,plain}}$):** `{dev.tau_bd_plain_Nmm2:.2f} N/mm²`")
            st.write(f"**HYSD / Deformed Factor:** `+{int((dev.hysd_factor-1)*100)}% ({dev.hysd_factor:.2f})`")
            st.write(f"**Design Bond Stress ($\tau_{{bd,design}}$):** `{dev.tau_bd_design_Nmm2:.2f} N/mm²`")
            st.write(f"**Development Length ($L_d$):** `{dev.ld_mm:.1f} mm` (`{dev.ld_phi_ratio:.1f} φ`)")

        with dcol2:
            st.markdown("##### 📏 Deflection Control (IS 456 Cl 23.2.1 & Fig. 4)")
            st.write(f"**Basic Span-to-Depth Ratio ($(L/d)_{{basic}}$):** `{defl.basic_span_depth_ratio:.1f}`")
            st.write(f"**Tension Modification Factor ($F_1$ / $K_t$):** `{defl.modification_factor_F1_tension:.3f}`")
            st.write(f"**Allowable Span-Depth Ratio ($(L/d)_{{allowable}}$):** `{defl.allowable_span_depth_ratio:.2f}`")
            act_s = f"{defl.actual_span_depth_ratio:.2f}" if defl.actual_span_depth_ratio is not None else "N/A"
            st.write(f"**Actual Span-Depth Ratio ($(L/d)_{{actual}}$):** `{act_s}`")
            st.write(f"**Deflection Control Status:** `{defl.status.value}`")

        st.markdown("---")
        st.markdown("### 📜 Automated IS 456:2000 Code Provision Audit Table")

        table_rows = []
        for chk in det.code_checks:
            badge_html = format_status_badge(chk.status)
            table_rows.append(
                f"<tr>"
                f"<td><strong>{chk.check_name}</strong></td>"
                f"<td><code>{chk.clause}</code></td>"
                f"<td>{chk.demand:.2f} {chk.unit}</td>"
                f"<td>{chk.capacity:.2f} {chk.unit}</td>"
                f"<td>{badge_html}</td>"
                f"<td>{chk.message}</td>"
                f"</tr>"
            )

        table_html = f"""
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background-color: #f1f3f5; border-bottom: 2px solid #dee2e6; text-align: left;">
                    <th style="padding: 8px;">Check Name</th>
                    <th style="padding: 8px;">Clause</th>
                    <th style="padding: 8px;">Demand / Provided</th>
                    <th style="padding: 8px;">Capacity / Limit</th>
                    <th style="padding: 8px;">Status</th>
                    <th style="padding: 8px;">Audit Message</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    # Tab 4: AI Explanation
    with tab_ai:
        st.subheader("🤖 AI Engineering Assistant (Claude Narrative Rationale)")
        st.caption(
            "Translates pre-calculated IS 456 telemetry into a structured technical narrative. "
            "The AI layer never alters engineering calculations."
        )

        if user_api_key:
            os.environ["ANTHROPIC_API_KEY"] = user_api_key

        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

        if not has_key:
            st.info(
                "💡 **API Key Setup Required:** To generate live AI explanations, set the `ANTHROPIC_API_KEY` "
                "environment variable or paste your API key in the sidebar."
            )

        if st.button("🚀 Generate Technical Explanation with Claude", type="primary"):
            if not has_key:
                st.error("Cannot invoke AI assistant: ANTHROPIC_API_KEY is not set.")
            else:
                with st.spinner("Analyzing IS 456 telemetry with Claude..."):
                    try:
                        client = AnthropicAIClient()
                        explanation = explain_beam_design(summary, client=client)

                        st.markdown("### 📝 Executive Summary")
                        st.write(explanation.overall_summary)

                        st.markdown("#### 🎯 Governing Checks")
                        for item in explanation.governing_checks:
                            st.write(f"- {item}")

                        if explanation.failed_checks:
                            st.markdown("#### ❌ Failed Checks & Deficiencies")
                            for item in explanation.failed_checks:
                                st.write(f"- {item}")

                        if explanation.warnings:
                            st.markdown("#### ⚠️ Engineering Warnings")
                            for item in explanation.warnings:
                                st.write(f"- {item}")

                        if explanation.recommendations:
                            st.markdown("#### 💡 Design Optimization Recommendations")
                            for item in explanation.recommendations:
                                st.write(f"- {item}")

                        st.markdown("#### 📖 Detailed Technical Rationale")
                        st.markdown(explanation.detailed_explanation)

                        st.info(f"**Disclaimer:** {explanation.disclaimer}")
                    except Exception as ex:
                        st.error(f"AI Assistant Error: {ex}")


if __name__ == "__main__":
    main()
