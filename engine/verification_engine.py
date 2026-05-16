"""
Battery DPP Verification Engine
Covers all 102 data points across 4 modules:
1. Sustainability Scorer
2. Authenticity Checker (cross-field math)
3. Compliance Tracker (2024 → 2031 → 2036)
4. Sensor Validator
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARKS = json.load(open(os.path.join(BASE, "data/benchmarks/chemistry_benchmarks.json")))
THRESHOLDS = json.load(open(os.path.join(BASE, "data/compliance/eu_2023_1542_thresholds.json")))

# ─── Color / Rating helpers ───────────────────────────────────────────────────
def score_to_color(score: float) -> str:
    if score >= 90:   return "🟢"
    if score >= 70:   return "🟡"
    if score >= 50:   return "🟠"
    if score >= 25:   return "🔴"
    return "⛔"

def score_to_label(score: float) -> str:
    if score >= 90:   return "EXCELLENT"
    if score >= 70:   return "GOOD"
    if score >= 50:   return "MODERATE"
    if score >= 25:   return "POOR"
    return "CRITICAL"

def score_to_css(score: float) -> str:
    if score >= 90:   return "#22c55e"   # green
    if score >= 70:   return "#eab308"   # yellow
    if score >= 50:   return "#f97316"   # orange
    if score >= 25:   return "#ef4444"   # red
    return "#7f1d1d"                      # dark red

# ─── Check Result dataclass ───────────────────────────────────────────────────
@dataclass
class CheckResult:
    name: str
    passed: bool
    score: float           # 0–100
    detail: str
    formula: str = ""
    severity: str = "INFO" # INFO / WARNING / CRITICAL
    flag: Optional[str] = None

@dataclass
class VerificationReport:
    battery_id: str
    overall_score: float
    trust_score: float
    sustainability_score: float
    sustainability_breakdown: dict
    authenticity_passed: int
    authenticity_total: int
    authenticity_checks: list
    compliance_by_year: dict
    sensor_result: Optional[dict]
    anomaly_flags: list
    data_real_pct: float
    data_mock_pct: float
    status: str            # VERIFIED / SUSPICIOUS / NON_COMPLIANT
    status_color: str


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — SUSTAINABILITY SCORER
# ══════════════════════════════════════════════════════════════════════════════

def _carbon_score(carbon_per_kwh, chemistry: str) -> tuple[float, str]:
    """Score 0-100. Compare declared CO2/kWh against chemistry benchmark."""
    if carbon_per_kwh is None:
        return 0.0, "Carbon footprint not declared — 0 points"

    bench = BENCHMARKS.get(chemistry, {})
    lo, hi = bench.get("carbon_kwh_range", [50, 90])
    mid = (lo + hi) / 2

    if carbon_per_kwh <= lo:
        score = 100.0
        detail = f"{carbon_per_kwh} kg CO₂e/kWh — below benchmark minimum ({lo}). Excellent."
    elif carbon_per_kwh <= mid:
        score = 100 - ((carbon_per_kwh - lo) / (mid - lo)) * 30
        detail = f"{carbon_per_kwh} kg CO₂e/kWh — lower half of {chemistry} benchmark ({lo}–{hi})."
    elif carbon_per_kwh <= hi:
        score = 70 - ((carbon_per_kwh - mid) / (hi - mid)) * 35
        detail = f"{carbon_per_kwh} kg CO₂e/kWh — upper half of {chemistry} benchmark ({lo}–{hi})."
    elif carbon_per_kwh <= hi * 1.2:
        score = 35 - ((carbon_per_kwh - hi) / (hi * 0.2)) * 25
        detail = f"{carbon_per_kwh} kg CO₂e/kWh — above benchmark max ({hi}). Needs improvement."
    else:
        score = 5.0
        detail = f"{carbon_per_kwh} kg CO₂e/kWh — significantly above {chemistry} benchmark. POOR."

    return max(0.0, min(100.0, score)), detail


def _recycled_score(data: dict) -> tuple[float, str]:
    """Score 0-100 based on recycled content vs 2031 targets."""
    rc = data.get("group_c_recycled", {}).get("data_points", {})
    co = rc.get("dp19_recycled_cobalt", {}).get("current_pct", 0) or 0
    li = rc.get("dp20_recycled_lithium", {}).get("current_pct", 0) or 0
    ni = rc.get("dp21_recycled_nickel", {}).get("current_pct", 0) or 0

    targets_2031 = THRESHOLDS["recycled_content_targets"]["2031"]
    co_t, li_t, ni_t = targets_2031["cobalt_pct"], targets_2031["lithium_pct"], targets_2031["nickel_pct"]

    chemistry = data["meta"]["chemistry"]
    has_cobalt = BENCHMARKS.get(chemistry, {}).get("cobalt_pct_cathode", 0) > 0
    has_nickel = BENCHMARKS.get(chemistry, {}).get("nickel_pct_cathode", 0) > 0

    # LFP: only lithium matters
    if not has_cobalt and not has_nickel:
        li_progress = min(li / li_t, 1.0) if li_t > 0 else 1.0
        score = li_progress * 80 + 20  # baseline 20 for having no conflict materials
        detail = f"LFP chemistry — no cobalt/nickel. Li recycled: {li}% (target 2031: {li_t}%). Score reflects lower risk profile."
        return score, detail

    scores = []
    details = []
    if has_cobalt:
        s = min(co / co_t, 1.0) * 100 if co_t > 0 else 100
        scores.append(s * 0.5)
        details.append(f"Co: {co}%/{co_t}% target")
    if True:  # lithium always relevant
        s = min(li / li_t, 1.0) * 100 if li_t > 0 else 100
        scores.append(s * 0.25)
        details.append(f"Li: {li}%/{li_t}% target")
    if has_nickel:
        s = min(ni / ni_t, 1.0) * 100 if ni_t > 0 else 100
        scores.append(s * 0.25)
        details.append(f"Ni: {ni}%/{ni_t}% target")

    score = sum(scores)
    detail = f"Progress to 2031 targets — {', '.join(details)}"
    return max(0.0, min(100.0, score)), detail


def _renewable_score(data: dict) -> tuple[float, str]:
    """Score 0-100 based on renewable energy in manufacturing."""
    rc = data.get("group_c_recycled", {}).get("data_points", {})
    dp = rc.get("dp23_renewable_energy", {})
    cell = dp.get("cell_manufacturing_pct", 0) or 0
    pack = dp.get("pack_assembly_pct", 0) or 0

    # Weight: cell manufacturing (60%) more carbon-intensive than pack assembly (40%)
    weighted = cell * 0.60 + pack * 0.40
    score = weighted  # 0–100
    detail = f"Cell manufacturing: {cell}% renewable, Pack assembly: {pack}% renewable → Weighted: {weighted:.0f}%"
    return score, detail


def _supply_chain_score(data: dict) -> tuple[float, str]:
    """Score 0-100 (higher = better). Penalises high geopolitical + ESG risk."""
    geo = THRESHOLDS["geopolitical_risk_scores"]
    esg = THRESHOLDS["esg_risk_scores"]

    dp = data.get("group_d_sourcing", {}).get("data_points", {})
    origins = dp.get("dp29_country_of_origin", {}).get("origins", {})
    traceability = dp.get("dp26_independent_verification", {})
    trace_method = traceability.get("result", "")
    is_blockchain = "full compliance" in trace_method.lower() or "blockchain" in str(traceability).lower()
    traceability_bonus = 20 if is_blockchain else 5

    chemistry = data["meta"]["chemistry"]
    bench = BENCHMARKS.get(chemistry, {})

    risks = []
    details = []
    for mat, info in origins.items():
        country = info.get("country", "Unknown").split("/")[0]
        g = geo.get(country, 5)
        e = esg.get(country, 5)
        combined = (g * 0.6 + e * 0.4)
        risks.append(combined)
        details.append(f"{mat.capitalize()}: {country} (risk {combined:.0f}/10)")

    if risks:
        avg_risk = sum(risks) / len(risks)
        base_score = max(0, 100 - avg_risk * 8)
    else:
        avg_risk = 5
        base_score = 50

    score = min(100, base_score + traceability_bonus)
    detail = f"{', '.join(details)}. Traceability: {'✅ Blockchain' if is_blockchain else '⚠️ Partial/None'}."
    return score, detail


def _circularity_score(data: dict) -> tuple[float, str]:
    """Score 0-100. Recyclability, second-life potential, EoL partners."""
    dp_d = data.get("group_d_sourcing", {}).get("data_points", {})
    evidence = dp_d.get("dp33_recycled_source_evidence", {})
    has_partner = bool(evidence.get("recycling_partners", []))

    dp_f = data.get("group_f_conformity", {}).get("data_points", {})
    takeback = dp_f.get("dp57_waste_takeback", {}).get("dealer_points_eu", 0) or 0

    soh = data.get("group_j_soh", {}).get("data_points", {}).get("dp81_remaining_capacity", {}).get("pct_of_rated", 100)
    second_life_eligible = soh >= 80

    # Chemistry circularity (LFP harder to recycle economically, NMC better)
    chemistry = data["meta"]["chemistry"]
    chem_bonus = {"NMC811": 15, "NMC712": 12, "LFP": 5}.get(chemistry, 10)

    partner_score = 30 if has_partner else 0
    takeback_score = min(20, takeback / 200)  # max 20 at 4000+ points
    second_life_score = 20 if second_life_eligible else 0

    score = partner_score + takeback_score + second_life_score + chem_bonus + 15  # 15 baseline

    detail = (f"Recycling partners: {'✅' if has_partner else '❌'}. "
              f"EU take-back network: {takeback} points. "
              f"Second-life eligible: {'✅' if second_life_eligible else '❌'}. "
              f"Chemistry recyclability: {chemistry}.")

    return min(100.0, score), detail


def calculate_sustainability_score(data: dict) -> dict:
    """Full sustainability score with all 5 components."""
    chemistry = data["meta"]["chemistry"]
    carbon_raw = (data.get("group_b_carbon", {})
                      .get("data_points", {})
                      .get("dp11_carbon_total", {})
                      .get("value_kg_co2_per_kwh"))

    carbon_s, carbon_d = _carbon_score(carbon_raw, chemistry)
    recycled_s, recycled_d = _recycled_score(data)
    renewable_s, renewable_d = _renewable_score(data)
    supply_s, supply_d = _supply_chain_score(data)
    circularity_s, circularity_d = _circularity_score(data)

    weights = {"carbon": 0.30, "recycled": 0.25, "renewable": 0.20, "supply_chain": 0.15, "circularity": 0.10}
    total = (carbon_s * weights["carbon"] + recycled_s * weights["recycled"] +
             renewable_s * weights["renewable"] + supply_s * weights["supply_chain"] +
             circularity_s * weights["circularity"])

    return {
        "total": round(total, 1),
        "color": score_to_color(total),
        "label": score_to_label(total),
        "css_color": score_to_css(total),
        "components": {
            "carbon":      {"score": round(carbon_s, 1),     "weight": 0.30, "detail": carbon_d,     "color": score_to_color(carbon_s)},
            "recycled":    {"score": round(recycled_s, 1),   "weight": 0.25, "detail": recycled_d,   "color": score_to_color(recycled_s)},
            "renewable":   {"score": round(renewable_s, 1),  "weight": 0.20, "detail": renewable_d,  "color": score_to_color(renewable_s)},
            "supply_chain":{"score": round(supply_s, 1),     "weight": 0.15, "detail": supply_d,     "color": score_to_color(supply_s)},
            "circularity": {"score": round(circularity_s, 1),"weight": 0.10, "detail": circularity_d,"color": score_to_color(circularity_s)},
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — AUTHENTICITY CHECKER (8 cross-field checks)
# ══════════════════════════════════════════════════════════════════════════════

def run_authenticity_checks(data: dict) -> list[CheckResult]:
    checks = []
    meta = data["meta"]
    chemistry = meta["chemistry"]
    bench = BENCHMARKS.get(chemistry, {})

    # ── Check 1: Voltage × Capacity = Energy ──────────────────────────────
    elec = data.get("group_e_electrical", {}).get("data_points", {})
    voltage = elec.get("dp36_nominal_voltage", {}).get("value_v")
    cap_ah = elec.get("dp34_rated_capacity_ah", {}).get("value_ah")
    declared_kwh = meta.get("capacity_kwh")
    if voltage and cap_ah and declared_kwh:
        calculated = (voltage * cap_ah) / 1000
        deviation = abs(calculated - declared_kwh) / declared_kwh
        passed = deviation <= 0.03
        checks.append(CheckResult(
            name="Energy Consistency (V × Ah = kWh)",
            passed=passed,
            score=100 if passed else max(0, 100 - deviation * 1000),
            detail=f"{voltage}V × {cap_ah}Ah = {calculated:.1f} kWh vs declared {declared_kwh} kWh. Deviation: {deviation*100:.1f}%",
            formula=f"Nominal Voltage ({voltage}V) × Rated Capacity ({cap_ah}Ah) / 1000 = {calculated:.2f} kWh",
            severity="CRITICAL" if not passed else "INFO",
        ))
    
    # ── Check 2: Module × Cell = Total cells ──────────────────────────────
    comp = data.get("group_g_composition", {}).get("data_points", {})
    cell_data = comp.get("dp71_cell_count", {})
    modules = cell_data.get("modules")
    cells_per = cell_data.get("cells_per_module")
    total_cells = cell_data.get("total_cells")
    if modules and cells_per and total_cells:
        calculated_cells = modules * cells_per
        passed = calculated_cells == total_cells
        checks.append(CheckResult(
            name="Cell Count Consistency (Modules × Cells/Module)",
            passed=passed,
            score=100 if passed else 0,
            detail=f"{modules} modules × {cells_per} cells = {calculated_cells} vs declared {total_cells}",
            formula=f"Modules ({modules}) × Cells per module ({cells_per}) = {calculated_cells}",
            severity="WARNING" if not passed else "INFO",
        ))

    # ── Check 3: Carbon value vs chemistry benchmark ──────────────────────
    carbon = (data.get("group_b_carbon", {}).get("data_points", {})
                  .get("dp11_carbon_total", {}).get("value_kg_co2_per_kwh"))
    if carbon is not None:
        lo, hi = bench.get("carbon_kwh_range", [30, 100])
        margin = (hi - lo) * 0.15  # 15% outside range still possible
        passed = (lo - margin) <= carbon <= (hi + margin)
        flag = data.get("group_b_carbon", {}).get("data_points", {}).get("dp11_carbon_total", {}).get("flag")
        checks.append(CheckResult(
            name="Carbon Footprint vs Chemistry Benchmark",
            passed=passed,
            score=100 if passed else max(0, 50 - abs(carbon - (lo+hi)/2) * 2),
            detail=f"Declared: {carbon} kg CO₂e/kWh. {chemistry} benchmark: {lo}–{hi} kg CO₂e/kWh.",
            formula=f"Declared CO₂/kWh ({carbon}) within {chemistry} range ({lo}–{hi}) ± 15% tolerance",
            severity="CRITICAL" if not passed else "INFO",
            flag=flag,
        ))

    # ── Check 4: Carbon class matches declared value ──────────────────────
    carbon_dp = data.get("group_b_carbon", {}).get("data_points", {}).get("dp12_carbon_class", {})
    declared_class = carbon_dp.get("declared_class")
    if carbon is not None and declared_class:
        boundaries = THRESHOLDS["carbon_class_boundaries"]
        calculated_class = None
        for cls, (lo_c, hi_c) in boundaries.items():
            if lo_c <= carbon < hi_c:
                calculated_class = cls
                break
        passed = calculated_class == declared_class
        checks.append(CheckResult(
            name="Carbon Class Consistency",
            passed=passed,
            score=100 if passed else 0,
            detail=f"Declared class: {declared_class}. Calculated class from {carbon} kg CO₂e/kWh: {calculated_class}.",
            formula=f"Class A: <40, B: 40-80, C: 80-120, D: >120 kg CO₂e/kWh",
            severity="CRITICAL" if not passed else "INFO",
            flag=carbon_dp.get("flag"),
        ))

    # ── Check 5: Material stoichiometry vs declared weights ───────────────
    sourcing = data.get("group_d_sourcing", {}).get("data_points", {})
    mat_list = sourcing.get("dp30_raw_material_quantities", {}).get("materials", [])
    total_mass = sourcing.get("dp30_raw_material_quantities", {}).get("total_module_mass_kg")
    mat_dict = {m["name"].lower(): m["mass_kg"] for m in mat_list if m.get("mass_kg")}
    
    cobalt_pct_bench = bench.get("cobalt_pct_cathode", 0)
    nickel_pct_bench = bench.get("nickel_pct_cathode", 0)

    if total_mass and cobalt_pct_bench > 0 and "cobalt" in mat_dict:
        # Very rough check: cobalt should be ~cobalt_pct_cathode/100 × ~20% of active mass
        expected_co = total_mass * (cobalt_pct_bench / 100) * 0.22  # ~22% cathode in pack
        actual_co = mat_dict.get("cobalt", 0)
        deviation = abs(actual_co - expected_co) / max(expected_co, 1)
        passed = deviation <= 0.50  # 50% tolerance — rough estimate
        checks.append(CheckResult(
            name="Material Stoichiometry — Cobalt Weight Plausibility",
            passed=passed,
            score=100 if passed else max(0, 100 - deviation * 80),
            detail=f"Declared Co: {actual_co} kg. Expected from {chemistry} stoichiometry: ~{expected_co:.1f} kg. Deviation: {deviation*100:.0f}%",
            formula=f"Expected Co ≈ total_mass ({total_mass} kg) × cathode_fraction (22%) × Co_pct ({cobalt_pct_bench}%)",
            severity="WARNING" if not passed else "INFO",
        ))

    # ── Check 6: EU DoC present and consistent ────────────────────────────
    conf = data.get("group_f_conformity", {}).get("data_points", {})
    doc = conf.get("dp49_eu_doc", {})
    doc_ref = conf.get("dp50_doc_reference", {})
    doc_present = doc.get("issued_by") is not None or doc.get("present") is False
    ref_present = doc_ref.get("reference") is not None
    notified_present = doc_ref.get("notified_body") is not None
    passed = doc_present and ref_present and notified_present
    checks.append(CheckResult(
        name="EU Declaration of Conformity Completeness",
        passed=passed,
        score=100 if passed else (33 if doc_present else 0),
        detail=f"DoC issued: {'✅' if doc_present else '❌'} | Reference number: {'✅' if ref_present else '❌'} | Notified body: {'✅' if notified_present else '❌'}",
        formula="DoC required under Art. 18 Reg. (EU) 2023/1542. Notified body under Art. 20.",
        severity="CRITICAL" if not passed else "INFO",
        flag=conf.get("dp49_eu_doc", {}).get("flag"),
    ))

    # ── Check 7: Supply chain traceability claim vs verification ─────────
    sc = data.get("group_d_sourcing", {}).get("data_points", {})
    strategy = sc.get("dp24_due_diligence_strategy", {})
    verification = sc.get("dp26_independent_verification", {})
    has_framework = bool(strategy.get("frameworks", []) and strategy["frameworks"][0] != "None declared")
    has_verifier = bool(verification.get("verifier") and verification["verifier"] != "None")
    has_blockchain = "blockchain" in str(strategy.get("traceability", "")).lower()
    passed = has_framework and has_verifier
    score = (40 if has_framework else 0) + (40 if has_verifier else 0) + (20 if has_blockchain else 0)
    checks.append(CheckResult(
        name="Supply Chain Due Diligence & Traceability",
        passed=passed,
        score=float(score),
        detail=f"OECD framework: {'✅' if has_framework else '❌'} | Independent verifier: {'✅' if has_verifier else '❌'} | Blockchain traceability: {'✅' if has_blockchain else '❌'}",
        formula="Art. 49-52 Reg. (EU) 2023/1542 — due diligence + independent verification required",
        severity="CRITICAL" if not passed else ("WARNING" if not has_blockchain else "INFO"),
        flag=verification.get("flag"),
    ))

    # ── Check 8: Data completeness vs claimed trust level ─────────────────
    real_pct = meta.get("data_real_pct", 0)
    trust = meta.get("trust_score", 0)
    max_possible_trust = real_pct * 0.5 + 50  # trust can't exceed this
    passed = trust <= max_possible_trust + 5  # 5 point tolerance
    checks.append(CheckResult(
        name="Data Completeness vs Trust Score Consistency",
        passed=passed,
        score=100 if passed else max(0, 100 - (trust - max_possible_trust) * 5),
        detail=f"Real/verified data: {real_pct}%. Trust score: {trust}/100. Max possible from verified data: {max_possible_trust:.0f}.",
        formula=f"Max trust = (real_pct × 0.5) + 50 base = {max_possible_trust:.0f}. Trust claimed: {trust}.",
        severity="WARNING" if not passed else "INFO",
    ))

    return checks


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — COMPLIANCE TRACKER
# ══════════════════════════════════════════════════════════════════════════════

def _check_year_compliance(data: dict, year: int) -> dict:
    meta = data["meta"]
    chemistry = meta["chemistry"]
    reqs = THRESHOLDS[f"mandatory_requirements_{year}"]
    failures = []
    warnings = []
    score = 100

    if year >= 2024:
        conf = data.get("group_f_conformity", {}).get("data_points", {})
        if not conf.get("dp49_eu_doc", {}).get("issued_by"):
            failures.append("EU Declaration of Conformity missing (Art. 18)")
            score -= 25
        if not conf.get("dp51_ce_marking", {}).get("affixed") or conf.get("dp51_ce_marking", {}).get("affixed") == "unverified":
            failures.append("CE marking not verifiable (Art. 19)")
            score -= 15
        if not conf.get("dp52_labelling", {}).get("separate_collection_symbol"):
            failures.append("Missing 'separate collection' symbol (Art. 13)")
            score -= 10
        # Manufacturer ID
        ma = data.get("group_a_general", {}).get("data_points", {}).get("dp1_manufacturer", {})
        if ma.get("eu_representative") is None and meta.get("manufacturer_country") != "EU":
            warnings.append("No EU responsible person declared for non-EU manufacturer")

    if year >= 2027:
        carbon = (data.get("group_b_carbon", {}).get("data_points", {})
                      .get("dp11_carbon_total", {}).get("value_kg_co2_per_kwh"))
        if carbon is None:
            failures.append("Carbon footprint not declared — mandatory from 2027 (Art. 7)")
            score -= 20
        meta_dp = data.get("group_m_metadata", {}).get("data_points", {})
        if not meta_dp.get("dp98_qr_code", {}).get("affixed"):
            failures.append("QR code / Digital Battery Passport not implemented (Art. 13(6))")
            score -= 15
        if not meta_dp.get("dp97_unique_identifier", {}).get("format", "").startswith("ISO"):
            warnings.append("Battery identifier may not comply with ISO/IEC 15459-1")

    if year >= 2031:
        rc = data.get("group_c_recycled", {}).get("data_points", {})
        targets = THRESHOLDS["recycled_content_targets"]["2031"]
        bench = BENCHMARKS.get(chemistry, {})
        
        if bench.get("cobalt_pct_cathode", 0) > 0:
            co = rc.get("dp19_recycled_cobalt", {}).get("current_pct", 0) or 0
            if co < targets["cobalt_pct"]:
                failures.append(f"Cobalt recycled content {co}% below 2031 target {targets['cobalt_pct']}% (Art. 8)")
                score -= max(0, (targets["cobalt_pct"] - co) * 1.5)

        li = rc.get("dp20_recycled_lithium", {}).get("current_pct", 0) or 0
        if li < targets["lithium_pct"]:
            failures.append(f"Lithium recycled content {li}% below 2031 target {targets['lithium_pct']}% (Art. 8)")
            score -= max(0, (targets["lithium_pct"] - li) * 2)

        if bench.get("nickel_pct_cathode", 0) > 0:
            ni = rc.get("dp21_recycled_nickel", {}).get("current_pct", 0) or 0
            if ni < targets["nickel_pct"]:
                failures.append(f"Nickel recycled content {ni}% below 2031 target {targets['nickel_pct']}% (Art. 8)")
                score -= max(0, (targets["nickel_pct"] - ni) * 2)

    if year >= 2036:
        rc = data.get("group_c_recycled", {}).get("data_points", {})
        targets = THRESHOLDS["recycled_content_targets"]["2036"]
        bench = BENCHMARKS.get(chemistry, {})
        if bench.get("cobalt_pct_cathode", 0) > 0:
            co = rc.get("dp19_recycled_cobalt", {}).get("current_pct", 0) or 0
            if co < targets["cobalt_pct"]:
                failures.append(f"Cobalt recycled {co}% below 2036 target {targets['cobalt_pct']}%")
                score -= max(0, (targets["cobalt_pct"] - co))
        li = rc.get("dp20_recycled_lithium", {}).get("current_pct", 0) or 0
        if li < targets["lithium_pct"]:
            failures.append(f"Lithium recycled {li}% below 2036 target {targets['lithium_pct']}%")
            score -= max(0, (targets["lithium_pct"] - li) * 1.5)

    score = max(0.0, min(100.0, score))
    if score >= 80 and not failures:
        status = "COMPLIANT"
        color = "#22c55e"
        emoji = "✅"
    elif score >= 50 or (failures and score >= 40):
        status = "AT RISK"
        color = "#f97316"
        emoji = "⚠️"
    else:
        status = "NON-COMPLIANT"
        color = "#ef4444"
        emoji = "❌"

    return {
        "year": year,
        "score": round(score, 1),
        "status": status,
        "color": color,
        "emoji": emoji,
        "failures": failures,
        "warnings": warnings,
        "requirements": reqs,
    }


def run_compliance_tracker(data: dict) -> dict:
    return {
        2024: _check_year_compliance(data, 2024),
        2027: _check_year_compliance(data, 2027),
        2031: _check_year_compliance(data, 2031),
        2036: _check_year_compliance(data, 2036),
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — SENSOR VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════

def validate_sensors(data: dict, sensor_readings: dict) -> dict:
    """
    Compare live sensor readings vs declared baseline values.
    sensor_readings: {
        "temperature_c": float,
        "voltage_v": float,
        "resistance_mohm": float,
        "soc_pct": float
    }
    """
    elec = data.get("group_e_electrical", {}).get("data_points", {})
    soh_dp = data.get("group_j_soh", {}).get("data_points", {})
    op_dp = data.get("group_l_operational", {}).get("data_points", {})

    baseline_v = elec.get("dp36_nominal_voltage", {}).get("value_v", 400)
    baseline_r = soh_dp.get("dp85_ohmic_resistance", {}).get("value_mohm", 35)
    baseline_soc = op_dp.get("dp96_state_of_charge", {}).get("delivery_soc_pct", 80)
    temp_max = BENCHMARKS.get(data["meta"]["chemistry"], {}).get("operating_temp_max_c", 55)
    temp_min = BENCHMARKS.get(data["meta"]["chemistry"], {}).get("operating_temp_min_c", -20)

    results = {}
    anomalies = []
    total_score = 100

    # Temperature check
    temp = sensor_readings.get("temperature_c", 25)
    if temp > temp_max:
        dev = temp - temp_max
        sev = "CRITICAL" if dev > 10 else "WARNING"
        anomalies.append(f"Temperature {temp}°C exceeds max {temp_max}°C by {dev:.1f}°C — {sev}")
        total_score -= min(40, dev * 3)
        results["temperature"] = {"value": temp, "baseline": f"≤{temp_max}°C", "status": sev, "color": "#ef4444"}
    elif temp < temp_min:
        dev = temp_min - temp
        anomalies.append(f"Temperature {temp}°C below operating minimum {temp_min}°C — WARNING")
        total_score -= min(20, dev * 1.5)
        results["temperature"] = {"value": temp, "baseline": f"≥{temp_min}°C", "status": "WARNING", "color": "#f97316"}
    else:
        results["temperature"] = {"value": temp, "baseline": f"{temp_min}–{temp_max}°C", "status": "NORMAL", "color": "#22c55e"}

    # Voltage check
    volt = sensor_readings.get("voltage_v", baseline_v)
    volt_dev = abs(volt - baseline_v) / baseline_v
    if volt_dev > 0.10:
        anomalies.append(f"Voltage {volt}V deviates {volt_dev*100:.1f}% from nominal {baseline_v}V — CRITICAL")
        total_score -= min(35, volt_dev * 200)
        results["voltage"] = {"value": volt, "baseline": f"{baseline_v}V", "deviation_pct": round(volt_dev*100, 1), "status": "CRITICAL", "color": "#ef4444"}
    elif volt_dev > 0.05:
        anomalies.append(f"Voltage {volt}V deviates {volt_dev*100:.1f}% from nominal — WARNING")
        total_score -= volt_dev * 100
        results["voltage"] = {"value": volt, "baseline": f"{baseline_v}V", "deviation_pct": round(volt_dev*100, 1), "status": "WARNING", "color": "#f97316"}
    else:
        results["voltage"] = {"value": volt, "baseline": f"{baseline_v}V", "deviation_pct": round(volt_dev*100, 1), "status": "NORMAL", "color": "#22c55e"}

    # Resistance check (increase = battery aging)
    res = sensor_readings.get("resistance_mohm", baseline_r)
    res_increase = (res - baseline_r) / max(baseline_r, 1) * 100  # % increase
    if res_increase > 50:
        anomalies.append(f"Internal resistance {res}mΩ — {res_increase:.0f}% above baseline {baseline_r}mΩ. Significant aging — CRITICAL")
        total_score -= min(40, res_increase * 0.5)
        results["resistance"] = {"value": res, "baseline": f"{baseline_r}mΩ", "increase_pct": round(res_increase, 1), "status": "CRITICAL", "color": "#ef4444"}
    elif res_increase > 25:
        anomalies.append(f"Internal resistance {res}mΩ — {res_increase:.0f}% above baseline. Moderate aging — WARNING")
        total_score -= res_increase * 0.4
        results["resistance"] = {"value": res, "baseline": f"{baseline_r}mΩ", "increase_pct": round(res_increase, 1), "status": "WARNING", "color": "#f97316"}
    elif res_increase > 0:
        results["resistance"] = {"value": res, "baseline": f"{baseline_r}mΩ", "increase_pct": round(res_increase, 1), "status": "NORMAL", "color": "#22c55e"}
    else:
        results["resistance"] = {"value": res, "baseline": f"{baseline_r}mΩ", "increase_pct": 0, "status": "NORMAL", "color": "#22c55e"}

    # SoC check
    soc = sensor_readings.get("soc_pct", 80)
    if soc < 10:
        anomalies.append(f"SoC {soc}% — deep discharge risk (threshold: 10%)")
        total_score -= 20
        results["soc"] = {"value": soc, "baseline": "10-90%", "status": "WARNING", "color": "#f97316"}
    elif soc > 98:
        anomalies.append(f"SoC {soc}% — overcharge risk (max recommended: 90%)")
        total_score -= 10
        results["soc"] = {"value": soc, "baseline": "10-90%", "status": "WARNING", "color": "#f97316"}
    else:
        results["soc"] = {"value": soc, "baseline": "10-90%", "status": "NORMAL", "color": "#22c55e"}

    total_score = max(0.0, min(100.0, total_score))

    # Estimate real-world SoH from resistance increase
    declared_soh = soh_dp.get("dp81_remaining_capacity", {}).get("pct_of_rated", 100)
    if res_increase > 0:
        # Every 20% resistance increase ≈ 5% SoH loss (simplified NMC aging curve)
        estimated_soh = declared_soh - (res_increase / 20) * 5
    else:
        estimated_soh = declared_soh

    soh_gap = declared_soh - estimated_soh

    return {
        "sensor_results": results,
        "anomalies": anomalies,
        "sensor_health_score": round(total_score, 1),
        "declared_soh_pct": declared_soh,
        "sensor_estimated_soh_pct": round(max(0, estimated_soh), 1),
        "soh_gap_pct": round(soh_gap, 1),
        "soh_gap_color": "#22c55e" if soh_gap < 5 else ("#f97316" if soh_gap < 15 else "#ef4444"),
        "overall_status": "NORMAL" if not anomalies else ("WARNING" if total_score > 50 else "CRITICAL"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — TRUST SCORE
# ══════════════════════════════════════════════════════════════════════════════

def calculate_trust_score(data: dict) -> dict:
    """Trust score from data completeness, verification, and conformity evidence."""
    real_pct = data["meta"].get("data_real_pct", 0)
    
    # Third-party verification
    sc = data.get("group_d_sourcing", {}).get("data_points", {})
    verifier = sc.get("dp26_independent_verification", {}).get("verifier", "")
    has_thirdparty = bool(verifier and verifier not in ["None", ""])
    thirdparty_score = 30 if has_thirdparty else 0

    # DoC presence
    conf = data.get("group_f_conformity", {}).get("data_points", {})
    doc_ref = conf.get("dp50_doc_reference", {}).get("reference")
    doc_score = 10 if doc_ref else 0

    # Test report
    auth = data.get("group_h_authority", {}).get("data_points", {})
    test_report = auth.get("dp73_test_reports", {}).get("report_number")
    test_score = 10 if test_report else 0

    total = (real_pct * 0.50) + thirdparty_score + doc_score + test_score

    # Per-group breakdown
    groups = {
        "A — General":       _group_real_pct(data, "group_a_general"),
        "B — Carbon":        _group_real_pct(data, "group_b_carbon"),
        "C — Recycled":      _group_real_pct(data, "group_c_recycled"),
        "D — Sourcing":      _group_real_pct(data, "group_d_sourcing"),
        "E — Electrical":    _group_real_pct(data, "group_e_electrical"),
        "F — Conformity":    _group_real_pct(data, "group_f_conformity"),
        "G — Composition":   _group_real_pct(data, "group_g_composition"),
        "H — Authority":     _group_real_pct(data, "group_h_authority"),
        "I — Performance":   _group_real_pct(data, "group_i_individual_performance"),
        "J — SoH":           _group_real_pct(data, "group_j_soh"),
        "K — Lifetime":      _group_real_pct(data, "group_k_lifetime"),
        "L — Operational":   _group_real_pct(data, "group_l_operational"),
        "M — Metadata":      _group_real_pct(data, "group_m_metadata"),
    }

    return {
        "total": round(min(100, total), 1),
        "color": score_to_color(total),
        "label": score_to_label(total),
        "css_color": score_to_css(total),
        "components": {
            "data_quality": round(real_pct * 0.5, 1),
            "third_party_verification": thirdparty_score,
            "doc_present": doc_score,
            "test_report": test_score,
        },
        "group_breakdown": groups,
    }


def _group_real_pct(data: dict, group_key: str) -> float:
    group = data.get(group_key, {}).get("data_points", {})
    if not group:
        return 0.0
    total = len(group)
    real = sum(1 for dp in group.values() if dp.get("status") == "REAL")
    return round(real / total * 100, 0) if total > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 6 — SoH COMPOSITE
# ══════════════════════════════════════════════════════════════════════════════

def calculate_soh_composite(data: dict) -> dict:
    """Composite SoH score from all 5 SoH parameters."""
    j = data.get("group_j_soh", {}).get("data_points", {})
    i = data.get("group_i_individual_performance", {}).get("data_points", {})

    cap_pct = j.get("dp81_remaining_capacity", {}).get("pct_of_rated", 100) or 100
    power_pct = j.get("dp82_remaining_power", {}).get("pct_of_rated", 100) or 100
    rtw = j.get("dp83_remaining_rtw", {}).get("value_pct", 93) or 93
    self_disc = j.get("dp84_self_discharge", {}).get("value_pct_per_month", 1.8) or 1.8
    res_inc = j.get("dp85_ohmic_resistance", {}).get("increase_pct", 0) or 0

    # Normalise each to 0–100
    cap_score = cap_pct
    power_score = power_pct
    rtw_score = min(100, (rtw / 95) * 100)  # 95% RTW = 100 score
    self_disc_score = max(0, 100 - (self_disc - 1.5) * 20)  # 1.5% = 100, 5% = 30
    res_score = max(0, 100 - res_inc)  # 0% increase = 100, 100% increase = 0

    composite = (cap_score * 0.35 + power_score * 0.25 + rtw_score * 0.20
                 + self_disc_score * 0.10 + res_score * 0.10)

    return {
        "composite": round(composite, 1),
        "color": score_to_color(composite),
        "label": score_to_label(composite),
        "css_color": score_to_css(composite),
        "components": {
            "capacity":          {"score": round(cap_score, 1),       "weight": 0.35, "value": f"{cap_pct}% retained"},
            "power":             {"score": round(power_score, 1),     "weight": 0.25, "value": f"{power_pct}% retained"},
            "rtw_efficiency":    {"score": round(rtw_score, 1),       "weight": 0.20, "value": f"{rtw}% efficiency"},
            "self_discharge":    {"score": round(self_disc_score, 1), "weight": 0.10, "value": f"{self_disc}%/month"},
            "resistance_health": {"score": round(res_score, 1),       "weight": 0.10, "value": f"+{res_inc}% increase"},
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# MASTER RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_full_verification(data: dict, sensor_readings: dict = None) -> VerificationReport:
    """Run all verification modules and return a full report."""
    if sensor_readings is None:
        # Use battery's declared operational values as default
        op = data.get("group_l_operational", {}).get("data_points", {})
        sensor_readings = {
            "temperature_c": op.get("dp95_operating_temperature", {}).get("avg_cell_c", 25),
            "voltage_v": data.get("group_e_electrical", {}).get("data_points", {}).get("dp36_nominal_voltage", {}).get("value_v", 400),
            "resistance_mohm": data.get("group_j_soh", {}).get("data_points", {}).get("dp85_ohmic_resistance", {}).get("value_mohm", 35),
            "soc_pct": op.get("dp96_state_of_charge", {}).get("current_soc_pct", 80),
        }

    sustainability = calculate_sustainability_score(data)
    auth_checks = run_authenticity_checks(data)
    compliance = run_compliance_tracker(data)
    sensor = validate_sensors(data, sensor_readings)
    trust = calculate_trust_score(data)
    soh = calculate_soh_composite(data)

    auth_passed = sum(1 for c in auth_checks if c.passed)
    auth_total = len(auth_checks)

    # Overall status
    anomalies = data["meta"].get("anomaly_flags", [])
    critical_fails = [c for c in auth_checks if not c.passed and c.severity == "CRITICAL"]
    
    status = data["meta"].get("verification_status", "VERIFIED")
    status_colors = {"VERIFIED": "#22c55e", "SUSPICIOUS": "#f97316", "NON_COMPLIANT": "#ef4444"}
    status_color = status_colors.get(status, "#6b7280")

    return VerificationReport(
        battery_id=data["meta"]["model_id"],
        overall_score=data["meta"]["overall_score"],
        trust_score=trust["total"],
        sustainability_score=sustainability["total"],
        sustainability_breakdown=sustainability,
        authenticity_passed=auth_passed,
        authenticity_total=auth_total,
        authenticity_checks=auth_checks,
        compliance_by_year=compliance,
        sensor_result=sensor,
        anomaly_flags=anomalies,
        data_real_pct=data["meta"]["data_real_pct"],
        data_mock_pct=data["meta"]["data_mock_pct"],
        status=status,
        status_color=status_color,
    )


def load_battery(manufacturer_id: str, model_id: str) -> dict:
    path = os.path.join(BASE, f"data/manufacturers/{manufacturer_id}/{model_id}.json")
    with open(path) as f:
        return json.load(f)


BATTERY_REGISTRY = {
    "volvo": {
        "name": "Volvo Cars",
        "country": "Sweden",
        "models": {
            "ex90_nmc811_111kwh": "EX90 Twin Motor MY24 — NMC811 111 kWh"
        }
    },
    "bmw": {
        "name": "BMW Group",
        "country": "Germany",
        "models": {
            "ix_nmc712_105kwh": "iX xDrive50 MY24 — NMC712 105 kWh"
        }
    },
    "generic_oem": {
        "name": "Shenzhen PowerCell Tech Co., Ltd.",
        "country": "China",
        "models": {
            "lfp_80kwh": "PCB-EV-80 — LFP 80 kWh"
        }
    }
}
