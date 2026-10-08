# StructAI — IS 456:2000 Technical Verification Report

> [!NOTE]
> This document contains **independently hand-verifiable engineering calculation examples** designed to validate every core calculation engine in StructAI against **IS 456:2000**.
>
> Formula derivation, intermediate mathematical steps, and code clause citations are documented for each example.

---

## 1. Flexure Design Verification (Annex G & Clause 38.1)

### Flexure Example 1: Singly Reinforced Rectangular Beam (Fe 415 & M20)

#### Inputs
- **Section Dimensions:** Width $b = 250\text{ mm}$, Overall Depth $D = 500\text{ mm}$, Effective Depth $d = 450\text{ mm}$
- **Materials:** Concrete Grade $f_{ck} = 20\text{ N/mm}^2$ (M20), Steel Grade $f_y = 415\text{ N/mm}^2$ (Fe 415)
- **Design Load:** Factored Bending Moment $M_u = 100.0\text{ kNm} = 100 \times 10^6\text{ N}\cdot\text{mm}$

#### Hand Calculations & Intermediate Values
1. **Limiting Neutral Axis Depth Ratio ($x_{u,max}/d$):**
   - Per Clause 38.1 Note, for Fe 415 steel:
     $$\frac{x_{u,max}}{d} = 0.48$$
     $$x_{u,max} = 0.48 \times 450 = 216.00\text{ mm}$$

2. **Limiting Moment of Resistance ($M_{u,lim}$):**
   - Per Annex G-1.1 (c):
     $$M_{u,lim} = 0.36 \left(\frac{x_{u,max}}{d}\right) \left(1 - 0.42 \frac{x_{u,max}}{d}\right) f_{ck} b d^2$$
     $$M_{u,lim} = 0.36 \times 0.48 \times (1 - 0.42 \times 0.48) \times 20 \times 250 \times 450^2 = 139,688,640\text{ N}\cdot\text{mm} = 139.69\text{ kNm}$$

3. **Section Classification Check:**
   - Applied $M_u = 100.0\text{ kNm} \le M_{u,lim} = 139.69\text{ kNm}$.
   - Section is **Singly Reinforced & Under-Reinforced**.

4. **Required Tension Steel Area ($A_{st,req}$):**
   - Per Annex G-1.1 (b):
     $$A_{st,req} = \frac{0.5 f_{ck}}{f_y} \left[1 - \sqrt{1 - \frac{4.6 M_u}{f_{ck} b d^2}}\right] b d$$
     $$\text{Discriminant} = 1 - \frac{4.6 \times 100 \times 10^6}{20 \times 250 \times 450^2} = 1 - 0.45432 = 0.54568$$
     $$A_{st,req} = \frac{0.5 \times 20}{415} \times [1 - \sqrt{0.54568}] \times 250 \times 450 = 708.34\text{ mm}^2$$

5. **Actual Neutral Axis Depth ($x_u$):**
   - Per force equilibrium (Clause 38.1):
     $$x_u = \frac{0.87 f_y A_{st}}{0.36 f_{ck} b} = \frac{0.87 \times 415 \times 708.34}{0.36 \times 20 \times 250} = 142.10\text{ mm}$$

6. **Code Steel Limits:**
   - Minimum Tension Steel (Clause 26.5.1.1 a):
     $$A_{st,min} = \frac{0.85 b d}{f_y} = \frac{0.85 \times 250 \times 450}{415} = 230.42\text{ mm}^2$$
   - Maximum Tension Steel (Clause 26.5.1.1 b):
     $$A_{st,max} = 0.04 b D = 0.04 \times 250 \times 500 = 5000.00\text{ mm}^2$$

#### Verification Comparison Table
| Parameter | Equation / Clause | Hand Value | StructAI Value | Status |
| :--- | :--- | :--- | :--- | :--- |
| $x_{u,max}/d$ | Cl 38.1 Note | 0.48 | 0.48 | EXACT |
| $M_{u,lim}$ | Annex G-1.1 c | 139.69 kNm | 139.69 kNm | PASS |
| $A_{st,req}$ | Annex G-1.1 b | 708.34 mm² | 708.34 mm² | PASS |
| $x_u$ | Cl 38.1 | 142.10 mm | 142.10 mm | PASS |
| $A_{st,min}$ | Cl 26.5.1.1 a | 230.42 mm² | 230.42 mm² | PASS |
| $A_{st,max}$ | Cl 26.5.1.1 b | 5000.00 mm² | 5000.00 mm² | PASS |

---

### Flexure Example 2: Singly Reinforced Rectangular Beam (Fe 500 & M25)

#### Inputs
- **Section Dimensions:** Width $b = 300\text{ mm}$, Overall Depth $D = 600\text{ mm}$, Effective Depth $d = 540\text{ mm}$
- **Materials:** Concrete Grade $f_{ck} = 25\text{ N/mm}^2$ (M25), Steel Grade $f_y = 500\text{ N/mm}^2$ (Fe 500)
- **Design Load:** Factored Bending Moment $M_u = 200.0\text{ kNm} = 200 \times 10^6\text{ N}\cdot\text{mm}$

#### Hand Calculations & Intermediate Values
1. **Limiting Neutral Axis Depth Ratio ($x_{u,max}/d$):**
   - For Fe 500 steel: $\frac{x_{u,max}}{d} = 0.46 \Rightarrow x_{u,max} = 0.46 \times 540 = 248.40\text{ mm}$.

2. **Limiting Moment of Resistance ($M_{u,lim}$):**
   $$M_{u,lim} = 0.36 \times 0.46 \times (1 - 0.42 \times 0.46) \times 25 \times 300 \times 540^2 = 290.15\text{ kNm}$$

3. **Required Tension Steel Area ($A_{st,req}$):**
   $$\text{Discriminant} = 1 - \frac{4.6 \times 200 \times 10^6}{25 \times 300 \times 540^2} = 1 - 0.42067 = 0.57933$$
   $$A_{st,req} = \frac{0.5 \times 25}{500} \times [1 - \sqrt{0.57933}] \times 300 \times 540 = 967.42\text{ mm}^2$$

4. **Actual Neutral Axis Depth ($x_u$):**
   $$x_u = \frac{0.87 \times 500 \times 967.42}{0.36 \times 25 \times 300} = 155.86\text{ mm}$$

5. **Code Steel Limits:**
   - $A_{st,min} = \frac{0.85 \times 300 \times 540}{500} = 275.40\text{ mm}^2$
   - $A_{st,max} = 0.04 \times 300 \times 600 = 7200.00\text{ mm}^2$

---

## 2. Shear Design Verification (Clause 40 & Clause 26.5.1)

### Shear Example 1: Section Requiring Calculated Shear Stirrups

#### Inputs
- **Section Dimensions:** $b = 250\text{ mm}$, $d = 450\text{ mm}$
- **Materials:** $f_{ck} = 20\text{ N/mm}^2$ (M20), Stirrup Steel $f_{yv} = 415\text{ N/mm}^2$ (Fe 415)
- **Tension Steel Provided:** $A_{st} = 708.34\text{ mm}^2$
- **Design Load:** Factored Shear Force $V_u = 100.0\text{ kN} = 100,000\text{ N}$
- **Stirrup Bar Details:** 2-legged 8mm stirrup ($A_{sv} = 2 \times \frac{\pi}{4} \times 8^2 = 100.53\text{ mm}^2$)

#### Hand Calculations & Intermediate Values
1. **Nominal Shear Stress ($\tau_v$):**
   - Per Clause 40.1:
     $$\tau_v = \frac{V_u}{b d} = \frac{100,000}{250 \times 450} = 0.889\text{ N/mm}^2$$

2. **Maximum Permissible Shear Stress ($\tau_{c,max}$):**
   - Per Table 20 for M20: $\tau_{c,max} = 2.80\text{ N/mm}^2$. Check: $\tau_v (0.889) \le \tau_{c,max} (2.80) \Rightarrow$ **PASS**.

3. **Concrete Design Shear Strength ($\tau_c$):**
   - Percentage of tension steel:
     $$p_t = \frac{100 \times 708.34}{250 \times 450} = 0.6296\%$$
   - From Table 19 for M20 concrete:
     - For $p_t = 0.50\%$, $\tau_c = 0.48\text{ N/mm}^2$
     - For $p_t = 0.75\%$, $\tau_c = 0.56\text{ N/mm}^2$
   - Bilinear Interpolation:
     $$\tau_c = 0.48 + \left(\frac{0.6296 - 0.50}{0.75 - 0.50}\right) \times (0.56 - 0.48) = 0.48 + (0.5184 \times 0.08) = 0.521\text{ N/mm}^2$$

4. **Net Shear Force Carried by Steel ($V_{us}$):**
   - Since $\tau_v (0.889) > \tau_c (0.521)$, shear stirrups are required.
   - Per Clause 40.4:
     $$V_{us} = V_u - (\tau_c b d) = 100,000 - (0.521 \times 250 \times 450) = 100,000 - 58,613 = 41,387\text{ N} = 41.39\text{ kN}$$

5. **Calculated Stirrup Spacing ($s_v$):**
   - Per Clause 40.4 (a):
     $$s_v = \frac{0.87 f_{yv} A_{sv} d}{V_{us}} = \frac{0.87 \times 415 \times 100.53 \times 450}{41,387} = 394.8\text{ mm}$$

6. **Code Spacing Limits:**
   - Minimum Shear Steel Limit (Clause 26.5.1.6):
     $$s_{v,min} = \frac{0.87 f_{yv} A_{sv}}{0.4 b} = \frac{0.87 \times 415 \times 100.53}{0.4 \times 250} = 362.96\text{ mm}$$
   - Maximum Spacing Code Limit (Clause 26.5.1.5):
     $$s_{v,max,code} = \min(0.75 d, 300\text{ mm}) = \min(0.75 \times 450, 300) = \min(337.5, 300) = 300.0\text{ mm}$$
   - **Governing Maximum Permissible Spacing:** $\min(300.0, 362.96) = 300.0\text{ mm}$.

---

### Shear Example 2: Nominal Minimum Shear Reinforcement Only

#### Inputs
- Same section ($250 \times 450\text{ mm}$, M20, Fe 415) with low factored shear force $V_u = 30.0\text{ kN}$.

#### Hand Calculations & Intermediate Values
1. Nominal shear stress: $\tau_v = \frac{30,000}{250 \times 450} = 0.267\text{ N/mm}^2$.
2. Concrete shear strength: $\tau_c = 0.521\text{ N/mm}^2$.
3. Check: $\tau_v (0.267) \le \tau_c (0.521) \Rightarrow$ Shear stirrups not required for strength ($V_{us} = 0.0\text{ kN}$).
4. Nominal minimum stirrups apply per Clause 26.5.1.6. Governing spacing limit = $300.0\text{ mm}$.

---

## 3. Development Length Verification (Clause 26.2.1)

### Development Length Example: Fe 415 HYSD Bar in Tension vs Compression

#### Inputs
- Steel Grade $f_y = 415\text{ N/mm}^2$, Concrete Grade $f_{ck} = 20\text{ N/mm}^2$ (M20), Bar Diameter $\phi = 20\text{ mm}$

#### Hand Calculations (Tension Bar)
1. **Plain Bar Design Bond Stress ($\tau_{bd,plain}$):**
   - Per Clause 26.2.1.1 Table for M20: $\tau_{bd,plain} = 1.20\text{ N/mm}^2$.
2. **HYSD Bar Modification:**
   - Per Clause 26.2.1.1, increase by $60\% \Rightarrow \text{HYSD Factor} = 1.60$.
3. **Bar in Tension:**
   - Compression factor = $1.00$.
4. **Design Bond Stress ($\tau_{bd,design}$):**
   $$\tau_{bd,design} = 1.20 \times 1.60 \times 1.00 = 1.92\text{ N/mm}^2$$
5. **Design Steel Stress ($\sigma_s$):**
   $$\sigma_s = 0.87 f_y = 0.87 \times 415 = 361.05\text{ N/mm}^2$$
6. **Development Length Ratio ($L_d/\phi$):**
   $$\frac{L_d}{\phi} = \frac{\sigma_s}{4 \tau_{bd,design}} = \frac{361.05}{4 \times 1.92} = 47.01$$
7. **Development Length ($L_d$) for $20\text{ mm}$ Bar:**
   $$L_d = 47.01 \times 20 = 940.23\text{ mm}$$

#### Hand Calculations (Compression Bar)
1. Per Clause 26.2.1.1, increase bond stress by $25\%$ for compression:
   $$\tau_{bd,design} = 1.20 \times 1.60 \times 1.25 = 2.40\text{ N/mm}^2$$
2. Development Length Ratio:
   $$\frac{L_d}{\phi} = \frac{361.05}{4 \times 2.40} = 37.61$$
3. Development Length ($L_d$) for $20\text{ mm}$ Bar:
   $$L_d = 37.61 \times 20 = 752.19\text{ mm}$$

---

## 4. Deflection Control Verification (Clause 23.2.1, Fig 4, Fig 5)

### Deflection Example: Simply Supported Beam with Tension & Compression Steel

#### Inputs
- Simply Supported Beam, Clear Span $L = 5000\text{ mm}$, Effective Depth $d = 450\text{ mm}$, Width $b = 250\text{ mm}$
- Steel Grade $f_y = 415\text{ N/mm}^2$, $A_{st,req} = 708.34\text{ mm}^2$, $A_{st,prov} = 708.34\text{ mm}^2$, $A_{sc,prov} = 226.19\text{ mm}^2$ ($2 \times 12\text{mm}$ compression bars)

#### Hand Calculations
1. **Basic Span-to-Depth Ratio ($(L/d)_{basic}$):**
   - Per Clause 23.2.1 for Simply Supported beam: $(L/d)_{basic} = 20.0$.
2. **Span Correction Factor:**
   - Span $L = 5.0\text{ m} \le 10\text{ m} \Rightarrow \text{Factor} = 1.00$.
3. **Design Stress in Tension Steel ($f_s$):**
   $$f_s = 0.58 f_y \left(\frac{A_{st,req}}{A_{st,prov}}\right) = 0.58 \times 415 \times 1.0 = 240.7\text{ N/mm}^2$$
4. **Tension Steel Percentage ($p_t$):**
   $$p_t = \frac{100 \times 708.34}{250 \times 450} = 0.63\%$$
5. **Tension Modification Factor ($F_1$ / Fig 4 Digitized Grid):**
   - For $p_t = 0.63\%$ and $f_s = 240.7\text{ N/mm}^2 \Rightarrow F_1 = 1.01$.
6. **Compression Steel Percentage ($p_c$):**
   $$p_c = \frac{100 \times 226.19}{250 \times 450} = 0.201\%$$
7. **Compression Modification Factor ($F_2$ / Fig 5 Digitized Grid):**
   - For $p_c = 0.201\% \Rightarrow F_2 = 1.06$.
8. **Overall Allowable Span-to-Depth Ratio:**
   $$(L/d)_{allowable} = 20.0 \times 1.01 \times 1.06 = 21.41$$
9. **Actual Span-to-Depth Ratio:**
   $$(L/d)_{actual} = \frac{5000}{450} = 11.11$$
10. **Check Result:**
    $$(L/d)_{actual} (11.11) \le (L/d)_{allowable} (21.41) \Rightarrow \textbf{PASS}$$
