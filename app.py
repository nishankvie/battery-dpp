"""
Battery DPP Verification System
Reg. (EU) 2023/1542 — Digital Product Passport
"""

import streamlit as st
import json
import os
import sys
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.verification_engine import (
    run_full_verification, load_battery, validate_sensors,
    calculate_sustainability_score, run_authenticity_checks,
    run_compliance_tracker, calculate_trust_score, calculate_soh_composite,
    score_to_color, score_to_label, score_to_css, BATTERY_REGISTRY
)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Battery DPP Verifier",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #060a12; }

.hero {
  background: linear-gradient(135deg, #0d1526 0%, #111c33 60%, #0d1526 100%);
  border: 1px solid #1a2744;
  border-radius: 16px;
  padding: 2rem 2.5rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}
.hero::after {
  content:'';position:absolute;top:0;right:0;width:300px;height:100%;
  background:radial-gradient(ellipse at right,rgba(59,130,246,0.07),transparent 70%);
  pointer-events:none;
}
.hero .reg-tag {
  display:inline-block;background:rgba(59,130,246,0.12);
  border:1px solid rgba(59,130,246,0.35);color:#60a5fa;
  padding:2px 10px;border-radius:20px;font-size:0.72rem;
  font-family:'JetBrains Mono',monospace;letter-spacing:0.5px;margin-bottom:0.7rem;
}
.hero h1 { color:#f0f6ff;font-size:1.9rem;font-weight:700;margin:0 0 0.3rem;letter-spacing:-0.3px; }
.hero p  { color:#7a92b4;margin:0;font-size:0.88rem; }

.section-hdr {
  color:#4a6080;font-size:0.68rem;text-transform:uppercase;
  letter-spacing:1.8px;font-weight:600;margin:1.4rem 0 0.7rem;
  padding-bottom:0.35rem;border-bottom:1px solid #131d2e;
}

.card {
  background:#0d1526;border:1px solid #141f35;
  border-radius:10px;padding:1.1rem 1.3rem;margin-bottom:0.7rem;
}
.card .lbl { color:#4a6080;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.25rem; }
.card .val { color:#e8f0ff;font-size:1.35rem;font-weight:700; }
.card .sub { color:#4a6080;font-size:0.78rem;margin-top:0.15rem; }

.plain-card {
  background:#0d1526;border:1px solid #141f35;border-radius:12px;
  padding:1.3rem;text-align:center;height:130px;
  display:flex;flex-direction:column;justify-content:center;align-items:center;gap:0.3rem;
}
.plain-card .ico  { font-size:1.8rem; }
.plain-card .ttl  { color:#7a92b4;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.6px; }
.plain-card .big  { font-size:1.3rem;font-weight:700; }
.plain-card .sml  { color:#4a6080;font-size:0.75rem; }

.check-row {
  display:flex;align-items:flex-start;gap:0.75rem;
  padding:0.85rem 1rem;background:#0d1526;border:1px solid #141f35;
  border-radius:8px;margin-bottom:0.45rem;
}
.check-row.pass { border-left:3px solid #16a34a; }
.check-row.warn { border-left:3px solid #d97706; }
.check-row.fail { border-left:3px solid #dc2626; }
.check-row .ico { font-size:1rem;flex-shrink:0;margin-top:2px; }
.check-row .nm  { color:#d1dff0;font-weight:600;font-size:0.87rem; }
.check-row .dt  { color:#5a7090;font-size:0.79rem;margin-top:0.18rem;line-height:1.4; }
.check-row .fm  { color:#2d4060;font-size:0.73rem;margin-top:0.15rem;font-family:'JetBrains Mono',monospace; }

.anomaly {
  background:rgba(220,38,38,0.07);border:1px solid rgba(220,38,38,0.25);
  border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.4rem;
  color:#fca5a5;font-size:0.82rem;line-height:1.5;
}
.anomaly::before { content:'⚠ ';font-weight:700;color:#ef4444; }

.warn-box {
  background:rgba(217,119,6,0.07);border:1px solid rgba(217,119,6,0.25);
  border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.4rem;
  color:#fcd34d;font-size:0.82rem;
}

.ok-box {
  background:rgba(22,163,74,0.07);border:1px solid rgba(22,163,74,0.25);
  border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.4rem;
  color:#86efac;font-size:0.82rem;
}

.sbar-wrap { margin-bottom:0.75rem; }
.sbar-top  { display:flex;justify-content:space-between;margin-bottom:0.28rem; }
.sbar-top .nm  { color:#8aa0bc;font-size:0.82rem; }
.sbar-top .val { color:#e8f0ff;font-weight:600;font-size:0.82rem; }
.sbar-bg   { background:#131d2e;border-radius:4px;height:7px;overflow:hidden; }
.sbar-fill { height:100%;border-radius:4px; }

.tl-item {
  display:flex;gap:1rem;padding:0.75rem 1rem;
  background:#0d1526;border-radius:8px;margin-bottom:0.4rem;align-items:flex-start;
}
.tl-yr { color:#60a5fa;font-weight:700;font-size:0.88rem;
  min-width:36px;font-family:'JetBrains Mono',monospace;margin-top:2px; }
.tl-body .st { font-weight:600;font-size:0.88rem;margin-bottom:0.2rem; }
.tl-body .fl { color:#5a7090;font-size:0.78rem;line-height:1.4; }

.dt-tbl { width:100%;border-collapse:collapse;font-size:0.8rem; }
.dt-tbl th { background:#0d1526;color:#4a6080;padding:0.55rem 0.75rem;
  text-align:left;font-weight:600;font-size:0.7rem;text-transform:uppercase;
  letter-spacing:0.5px;border-bottom:1px solid #141f35; }
.dt-tbl td { padding:0.5rem 0.75rem;border-bottom:1px solid #0f1828;
  color:#8aa0bc;vertical-align:top; }
.dt-tbl tr:hover td { background:rgba(255,255,255,0.015); }
.br { padding:1px 7px;border-radius:10px;font-size:0.68rem;font-weight:600; }
.br-real { background:rgba(22,163,74,0.15);color:#4ade80; }
.br-mock { background:rgba(217,119,6,0.15);color:#fbbf24; }
.br-l1   { background:rgba(59,130,246,0.12);color:#60a5fa; }
.br-l2   { background:rgba(168,85,247,0.12);color:#c084fc; }
.br-l3   { background:rgba(239,68,68,0.12);color:#f87171; }
.br-l4   { background:rgba(16,185,129,0.12);color:#34d399; }
.br-flag { background:rgba(239,68,68,0.1);color:#fca5a5;max-width:280px;
  display:inline-block;border-radius:4px;padding:2px 6px; }

.sensor-reading {
  background:#0d1526;border:1px solid #141f35;border-radius:10px;
  padding:1rem 1.2rem;text-align:center;
}
.sensor-reading .lbl { color:#4a6080;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.8px; }
.sensor-reading .val { font-size:1.5rem;font-weight:700;margin:0.2rem 0; }
.sensor-reading .base { color:#4a6080;font-size:0.75rem; }

.role-card {
  background:#0d1526;border:2px solid #141f35;border-radius:14px;
  padding:1.5rem 1rem;text-align:center;cursor:pointer;
  transition:all 0.18s ease;
}
.role-card:hover { border-color:#2563eb;background:#111d30; }
.role-card.active { border-color:#3b82f6;background:rgba(59,130,246,0.08); }
.role-card .ico  { font-size:2.2rem;margin-bottom:0.5rem; }
.role-card .ttl  { color:#e8f0ff;font-weight:700;font-size:1rem;margin-bottom:0.2rem; }
.role-card .sub  { color:#4a6080;font-size:0.78rem; }

.batt-card {
  background:#0d1526;border:1px solid #141f35;border-radius:12px;
  padding:1.4rem 1.5rem;margin-bottom:1rem;
  transition:border-color 0.15s;
}
.batt-card:hover { border-color:#1e3a5f; }
.batt-card .mfr  { color:#4a6080;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:0.3rem; }
.batt-card .mdl  { color:#e8f0ff;font-size:1.05rem;font-weight:600;margin-bottom:0.35rem; }
.batt-card .spec { color:#7a92b4;font-size:0.82rem;margin-bottom:0.75rem; }

.sbadge { display:inline-block;padding:3px 11px;border-radius:20px;font-size:0.76rem;font-weight:600; }
.sbadge-v  { background:rgba(22,163,74,0.12); color:#4ade80;border:1px solid rgba(22,163,74,0.3); }
.sbadge-s  { background:rgba(217,119,6,0.12); color:#fbbf24;border:1px solid rgba(217,119,6,0.3); }
.sbadge-nc { background:rgba(220,38,38,0.12); color:#f87171;border:1px solid rgba(220,38,38,0.3); }

[data-testid="stSidebar"] { background:#080e1a !important;border-right:1px solid #131d2e; }
.stButton button {
  background:#0d1526;color:#c8d8f0;border:1px solid #1e3050;
  border-radius:8px;font-family:'Inter',sans-serif;font-weight:500;
  transition:all 0.15s;
}
.stButton button:hover { background:#141f35;border-color:#2a4570; }
.stTabs [data-baseweb="tab-list"] { background:#0d1526;border-radius:8px;padding:3px;gap:3px; }
.stTabs [data-baseweb="tab"] { color:#4a6080;border-radius:6px;font-size:0.85rem; }
.stTabs [aria-selected="true"] { background:#141f35 !important;color:#e8f0ff !important; }
h1,h2,h3 { color:#e8f0ff !important; }
p, .stMarkdown p { color:#7a92b4; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
for k, v in [
    ("role", None), ("page", "role_select"),
    ("selected_battery", None),
    ("sensor", {"temperature_c": 25.0, "voltage_v": 408.0, "resistance_mohm": 34.8, "soc_pct": 80.0}),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# UTIL COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def gauge(score, title, subtitle="", h=260):
    c = score_to_css(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font": {"color": c, "size": 38, "family": "Inter"}, "suffix": "/100"},
        title={"text": f"<b>{title}</b><br><span style='font-size:0.8em;color:#4a6080'>{subtitle}</span>",
               "font": {"color": "#c8d8f0", "size": 13, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#1e3050",
                     "tickfont": {"color": "#4a6080", "size": 9}},
            "bar": {"color": c, "thickness": 0.22},
            "bgcolor": "#0d1526", "bordercolor": "#0d1526",
            "steps": [
                {"range": [0,  25], "color": "rgba(127,29,29,0.25)"},
                {"range": [25, 50], "color": "rgba(127,29,29,0.1)"},
                {"range": [50, 70], "color": "rgba(124,45,18,0.1)"},
                {"range": [70, 90], "color": "rgba(133,77,14,0.1)"},
                {"range": [90,100], "color": "rgba(20,83,45,0.18)"},
            ],
            "threshold": {"line": {"color": c, "width": 2}, "thickness": 0.75, "value": score}
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(t=55, b=5, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def score_bar_html(name, score, weight=None, detail=""):
    c = score_to_css(score)
    em = score_to_color(score)
    lb = score_to_label(score)
    wt = f"<span style='color:#2d4060;font-size:0.72rem'> · {int(weight*100)}% weight</span>" if weight else ""
    dt = f"<div style='color:#2d4060;font-size:0.73rem;margin-top:3px;line-height:1.4'>{detail}</div>" if detail else ""
    return f"""
    <div class="sbar-wrap">
      <div class="sbar-top">
        <span class="nm">{em} {name}{wt}</span>
        <span class="val" style="color:{c}">{score:.0f}/100 — {lb}</span>
      </div>
      <div class="sbar-bg">
        <div class="sbar-fill" style="width:{score}%;background:{c}"></div>
      </div>
      {dt}
    </div>"""


def check_row(chk):
    passed = chk.passed
    cls = "pass" if passed else ("warn" if chk.severity == "WARNING" else "fail")
    ico = "✅" if passed else ("⚠️" if chk.severity == "WARNING" else "❌")
    sc  = score_to_css(chk.score)
    flag_html = ""
    if chk.flag and not passed:
        flag_html = f'<div style="margin-top:5px;background:rgba(220,38,38,0.08);border:1px solid rgba(220,38,38,0.25);border-radius:5px;padding:3px 8px;color:#fca5a5;font-size:0.74rem">{chk.flag}</div>'
    st.markdown(f"""
    <div class="check-row {cls}">
      <div class="ico">{ico}</div>
      <div style="flex:1">
        <div class="nm">{chk.name}
          <span style="float:right;color:{sc};font-weight:700;font-size:0.8rem">{chk.score:.0f}/100</span>
        </div>
        <div class="dt">{chk.detail}</div>
        <div class="fm">📐 {chk.formula}</div>
        {flag_html}
      </div>
    </div>""", unsafe_allow_html=True)


def compliance_timeline(compliance_data):
    for yr, d in compliance_data.items():
        fl_html = ""
        if d["failures"]:
            for f in d["failures"]:
                fl_html += f'<div class="fl">❌ {f}</div>'
        if d["warnings"]:
            for w in d["warnings"]:
                fl_html += f'<div class="fl" style="color:#fbbf24">⚠️ {w}</div>'
        if not d["failures"] and not d["warnings"]:
            fl_html = f'<div class="fl" style="color:#4ade80">✅ All requirements met</div>'
        st.markdown(f"""
        <div class="tl-item">
          <div class="tl-yr">{yr}</div>
          <div class="tl-body" style="flex:1">
            <div class="st" style="color:{d['color']}">{d['emoji']} {d['status']} — {d['score']:.0f}/100</div>
            {fl_html}
          </div>
        </div>""", unsafe_allow_html=True)


def lifecycle_chart(phases):
    if not phases:
        st.info("Lifecycle data not declared.")
        return
    names, vals, cols = [], [], []
    for ph, d in phases.items():
        if d:
            v = d.get("kg_co2", 0)
            names.append(ph.replace("_"," ").title())
            vals.append(v)
            cols.append("#4ade80" if v < 0 else ("#ef4444" if v > 2000 else "#f97316"))
    fig = go.Figure(go.Bar(
        x=names, y=vals, marker_color=cols,
        text=[f"{v:+,.0f} kg" for v in vals], textposition="outside",
        textfont={"color": "#7a92b4", "size": 10}
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=240,
        showlegend=False,
        xaxis={"tickfont": {"color": "#7a92b4", "size": 11}, "gridcolor": "#0f1828"},
        yaxis={"tickfont": {"color": "#7a92b4", "size": 10}, "gridcolor": "#0f1828",
               "title": "kg CO₂e", "titlefont": {"color": "#4a6080", "size": 11}},
        margin=dict(t=20, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def supply_risk_table(origins):
    geo_risk = {
        "DRC": 8, "China": 6, "Indonesia": 5, "Chile": 4,
        "Australia": 2, "Philippines": 5, "Unknown": 7
    }
    rows = []
    for mat, info in origins.items():
        country = info.get("country", "Unknown").split("/")[0]
        risk = info.get("geopolitical_risk", geo_risk.get(country, 5))
        risk_c = "#ef4444" if risk >= 7 else ("#f97316" if risk >= 5 else "#4ade80")
        risk_em = "🔴" if risk >= 7 else ("🟠" if risk >= 5 else "🟢")
        rows.append(f"""
        <tr>
          <td><b style="color:#c8d8f0">{mat.capitalize()}</b></td>
          <td>{country}</td>
          <td><span style="color:{risk_c};font-weight:700">{risk_em} {risk}/10</span></td>
        </tr>""")
    html = f"""
    <table class="dt-tbl">
      <thead><tr><th>Material</th><th>Country of Origin</th><th>Geopolitical Risk</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""
    st.markdown(html, unsafe_allow_html=True)


def recycled_gap_table(data):
    rc = data.get("group_c_recycled", {}).get("data_points", {})
    from engine.verification_engine import THRESHOLDS
    t31 = THRESHOLDS["recycled_content_targets"]["2031"]
    t36 = THRESHOLDS["recycled_content_targets"]["2036"]
    materials = [
        ("Cobalt",  rc.get("dp19_recycled_cobalt",  {}).get("current_pct", 0) or 0, t31["cobalt_pct"],  t36["cobalt_pct"]),
        ("Lithium", rc.get("dp20_recycled_lithium", {}).get("current_pct", 0) or 0, t31["lithium_pct"], t36["lithium_pct"]),
        ("Nickel",  rc.get("dp21_recycled_nickel",  {}).get("current_pct", 0) or 0, t31["nickel_pct"],  t36["nickel_pct"]),
    ]
    rows = []
    for mat, cur, t1, t2 in materials:
        g1 = cur - t1
        g2 = cur - t2
        c1 = "#4ade80" if g1 >= 0 else "#ef4444"
        c2 = "#4ade80" if g2 >= 0 else "#ef4444"
        rows.append(f"""
        <tr>
          <td><b style="color:#c8d8f0">{mat}</b></td>
          <td style="color:#c8d8f0;font-weight:600">{cur}%</td>
          <td>{t1}%</td>
          <td><span style="color:{c1};font-weight:600">{g1:+.0f}%</span></td>
          <td>{t2}%</td>
          <td><span style="color:{c2};font-weight:600">{g2:+.0f}%</span></td>
        </tr>""")
    st.markdown(f"""
    <table class="dt-tbl">
      <thead><tr>
        <th>Material</th><th>Current</th>
        <th>2031 Target</th><th>2031 Gap</th>
        <th>2036 Target</th><th>2036 Gap</th>
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>""", unsafe_allow_html=True)


def all_102_table(data, role):
    access_max = {"Consumer": 1, "Technician": 2, "Company": 2, "Regulator": 4}.get(role, 1)
    group_map = {
        "group_a_general": "A — General Info",
        "group_b_carbon": "B — Carbon Footprint",
        "group_c_recycled": "C — Recycled Content",
        "group_d_sourcing": "D — Responsible Sourcing",
        "group_e_electrical": "E — Electrical Characteristics",
        "group_f_conformity": "F — Conformity & Labelling",
        "group_g_composition": "G — Composition & Disassembly",
        "group_h_authority": "H — Authority Information",
        "group_i_individual_performance": "I — Individual Performance",
        "group_j_soh": "J — State of Health",
        "group_k_lifetime": "K — Expected Lifetime",
        "group_l_operational": "L — Operational Data",
        "group_m_metadata": "M — Identification & Metadata",
    }
    rows = []
    for gk, gname in group_map.items():
        grp = data.get(gk, {}).get("data_points", {})
        for dk, dp in grp.items():
            al = dp.get("access_level", 1)
            if al > access_max:
                val = "🔒 Restricted"
            else:
                v = (dp.get("value") or dp.get("material") or dp.get("reference")
                     or dp.get("status_value") or "")
                if not v:
                    nums = {k: vv for k, vv in dp.items()
                            if isinstance(vv, (int, float)) and k not in ("id", "access_level")}
                    v = " | ".join(f"{k.replace('_',' ')}: {vv}" for k, vv in list(nums.items())[:3]) if nums else "—"
                val = str(v)[:110] + "…" if len(str(v)) > 110 else str(v)
            rows.append({
                "#": dp.get("id", ""),
                "Group": gname,
                "Data Point": dp.get("label", dk),
                "Level": f"L{al}",
                "Status": dp.get("status", ""),
                "Value": val,
                "Flag": dp.get("flag", ""),
            })

    df = pd.DataFrame(rows)

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        grp_f = st.multiselect("Filter Group", list(group_map.values()), key="tbl_grp")
    with fc2:
        stat_f = st.multiselect("Data Status", ["REAL", "MOCK"], key="tbl_stat")
    with fc3:
        flag_f = st.checkbox("Only flagged rows", key="tbl_flag")

    if grp_f:    df = df[df["Group"].isin(grp_f)]
    if stat_f:   df = df[df["Status"].isin(stat_f)]
    if flag_f:   df = df[df["Flag"] != ""]

    # Render as HTML table
    def badge(val):
        if val == "REAL":  return '<span class="br br-real">REAL</span>'
        if val == "MOCK":  return '<span class="br br-mock">MOCK</span>'
        return val

    def level_badge(val):
        m = {"L1": "br-l1", "L2": "br-l2", "L3": "br-l3", "L4": "br-l4"}
        return f'<span class="br {m.get(val,"")}"> {val}</span>'

    rows_html = ""
    for _, r in df.iterrows():
        flag_td = f'<span class="br br-flag">{r["Flag"][:70]}…</span>' if r["Flag"] else ""
        rows_html += f"""<tr>
          <td style="color:#4a6080;font-family:'JetBrains Mono',monospace">{r['#']}</td>
          <td style="color:#4a6080;font-size:0.73rem">{r['Group']}</td>
          <td style="color:#c8d8f0;font-weight:500">{r['Data Point']}</td>
          <td>{level_badge(r['Level'])}</td>
          <td>{badge(r['Status'])}</td>
          <td style="color:#7a92b4;font-size:0.77rem">{r['Value']}</td>
          <td>{flag_td}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;max-height:550px;overflow-y:auto">
    <table class="dt-tbl">
      <thead><tr>
        <th>#</th><th>Group</th><th>Data Point</th>
        <th>Level</th><th>Status</th><th>Value</th><th>Flag</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    <div style="color:#4a6080;font-size:0.75rem;margin-top:0.5rem">
      Showing {len(df)} of {len(rows)} data points
    </div>""", unsafe_allow_html=True)


def sensor_panel(data):
    st.markdown('<div class="section-hdr">🔌 Sensor Simulation — Compare Declared vs Real-World</div>', unsafe_allow_html=True)

    elec = data.get("group_e_electrical", {}).get("data_points", {})
    baseline_v = elec.get("dp36_nominal_voltage", {}).get("value_v", 408)
    baseline_r = data.get("group_j_soh", {}).get("data_points", {}).get("dp85_ohmic_resistance", {}).get("value_mohm", 34.8)

    # Presets
    presets = {
        "🟢 Normal Operation": {"temperature_c": 25.0, "voltage_v": float(baseline_v), "resistance_mohm": float(baseline_r), "soc_pct": 75.0},
        "🟡 Lightly Aged":     {"temperature_c": 28.0, "voltage_v": float(baseline_v) * 0.98, "resistance_mohm": float(baseline_r) * 1.3, "soc_pct": 65.0},
        "🟠 Significantly Aged": {"temperature_c": 32.0, "voltage_v": float(baseline_v) * 0.95, "resistance_mohm": float(baseline_r) * 1.6, "soc_pct": 55.0},
        "🔴 Overheated":       {"temperature_c": 62.0, "voltage_v": float(baseline_v) * 0.92, "resistance_mohm": float(baseline_r) * 1.8, "soc_pct": 40.0},
        "⛔ Post-Accident":    {"temperature_c": 75.0, "voltage_v": float(baseline_v) * 0.78, "resistance_mohm": float(baseline_r) * 2.8, "soc_pct": 18.0},
        "⚙️ Custom":           None,
    }

    preset_choice = st.selectbox("Load Scenario", list(presets.keys()), key="preset_sel")
    if presets[preset_choice] is not None:
        st.session_state.sensor = presets[preset_choice]

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.sensor["temperature_c"] = st.slider(
            "🌡 Cell Temperature (°C)", -20.0, 90.0,
            float(st.session_state.sensor["temperature_c"]), 0.5, key="sl_temp")
        st.session_state.sensor["voltage_v"] = st.slider(
            "⚡ Voltage (V)", float(baseline_v)*0.5, float(baseline_v)*1.1,
            float(st.session_state.sensor["voltage_v"]), 1.0, key="sl_volt")
    with c2:
        st.session_state.sensor["resistance_mohm"] = st.slider(
            "🔩 Internal Resistance (mΩ)", float(baseline_r)*0.5, float(baseline_r)*4.0,
            float(st.session_state.sensor["resistance_mohm"]), 0.5, key="sl_res")
        st.session_state.sensor["soc_pct"] = st.slider(
            "🔋 State of Charge (%)", 0.0, 100.0,
            float(st.session_state.sensor["soc_pct"]), 1.0, key="sl_soc")

    result = validate_sensors(data, st.session_state.sensor)

    # Reading cards
    st.markdown('<div class="section-hdr">Sensor Readings vs Declared Baseline</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    sensor_cards = [
        (c1, "🌡", "Temperature", f"{result['sensor_results']['temperature']['value']}°C",
         result['sensor_results']['temperature']['baseline'],
         result['sensor_results']['temperature']['color']),
        (c2, "⚡", "Voltage", f"{result['sensor_results']['voltage']['value']}V",
         f"Baseline: {result['sensor_results']['voltage']['baseline']}",
         result['sensor_results']['voltage']['color']),
        (c3, "🔩", "Resistance", f"{result['sensor_results']['resistance']['value']}mΩ",
         f"+{result['sensor_results']['resistance']['increase_pct']}% vs baseline",
         result['sensor_results']['resistance']['color']),
        (c4, "🔋", "SoC", f"{result['sensor_results']['soc']['value']}%",
         result['sensor_results']['soc']['baseline'],
         result['sensor_results']['soc']['color']),
    ]
    for col, ico, lbl, val, base, color in sensor_cards:
        col.markdown(f"""
        <div class="sensor-reading">
          <div class="lbl">{ico} {lbl}</div>
          <div class="val" style="color:{color}">{val}</div>
          <div class="base">{base}</div>
          <div style="height:4px;background:#131d2e;border-radius:2px;margin-top:6px">
            <div style="height:4px;background:{color};width:100%;border-radius:2px"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # SoH comparison
    c1, c2, c3 = st.columns(3)
    sc = score_to_css(result["sensor_health_score"])
    gap_c = result["soh_gap_color"]

    with c1:
        st.markdown(f"""<div class="card">
          <div class="lbl">Declared SoH</div>
          <div class="val" style="color:#4ade80">{result['declared_soh_pct']}%</div>
          <div class="sub">From DPP data</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card">
          <div class="lbl">Sensor-Estimated SoH</div>
          <div class="val" style="color:{sc}">{result['sensor_estimated_soh_pct']}%</div>
          <div class="sub">From live readings</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card">
          <div class="lbl">SoH Gap</div>
          <div class="val" style="color:{gap_c}">{result['soh_gap_pct']:+.1f}%</div>
          <div class="sub">Declared vs sensor estimate</div></div>""", unsafe_allow_html=True)

    if result["anomalies"]:
        st.markdown('<div class="section-hdr">🚨 Sensor Anomalies Detected</div>', unsafe_allow_html=True)
        for a in result["anomalies"]:
            sev = "CRITICAL" in a or "CRITICAL" in a.upper()
            cls = "anomaly" if sev else "warn-box"
            st.markdown(f'<div class="{cls}">{a}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-box">✅ All sensor readings within normal parameters</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ROLE SELECT
# ══════════════════════════════════════════════════════════════════════════════

def page_role_select():
    st.markdown("""
    <div class="hero">
      <div class="reg-tag">REG. (EU) 2023/1542 — DIGITAL BATTERY PASSPORT</div>
      <h1>🔋 Battery DPP Verification System</h1>
      <p>Intelligent multi-layer verification · 102 DPP data points · 8 cross-field authenticity checks · Real-time compliance tracking · 4 access levels</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Who are you? — Select your role to personalise what you see</div>', unsafe_allow_html=True)

    roles = [
        ("🙋", "Consumer", "EV Owner / Buyer", "Health score, warranty, safety — plain language"),
        ("🔧", "Technician", "Repair Shop", "SoH data, sensor validation, disassembly"),
        ("🏭", "Company", "Manufacturer / Fleet", "Compliance, carbon, supply chain risk"),
        ("🏛", "Regulator", "Market Surveillance", "Full 102 data points, audit trail, all checks"),
    ]
    cols = st.columns(4)
    for col, (ico, role, sub, desc) in zip(cols, roles):
        with col:
            sel = st.session_state.role == role
            cls = "active" if sel else ""
            st.markdown(f"""
            <div class="role-card {cls}">
              <div class="ico">{ico}</div>
              <div class="ttl">{role}</div>
              <div class="sub">{sub}</div>
            </div>
            <p style="text-align:center;font-size:0.73rem;color:#2d4060;margin-top:0.4rem">{desc}</p>
            """, unsafe_allow_html=True)
            if st.button(f"Select →", key=f"r_{role}", use_container_width=True):
                st.session_state.role = role
                st.session_state.page = "browse"
                st.rerun()

    # Stats strip
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, "102", "DPP Data Points"), (c2, "8", "Cross-Field Auth Checks"),
        (c3, "3", "Batteries in Registry"), (c4, "4", "Compliance Horizons (2024–2036)")
    ]:
        col.markdown(f"""
        <div style="background:#0d1526;border:1px solid #141f35;border-radius:10px;
             padding:1rem;text-align:center">
          <div style="font-size:1.8rem;font-weight:700;color:#3b82f6">{num}</div>
          <div style="font-size:0.75rem;color:#4a6080;margin-top:0.2rem">{lbl}</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BROWSE
# ══════════════════════════════════════════════════════════════════════════════

def page_browse():
    role = st.session_state.role
    icons = {"Consumer": "🙋", "Technician": "🔧", "Company": "🏭", "Regulator": "🏛"}
    with st.sidebar:
        st.markdown(f"### {icons.get(role,'')} {role}")
        st.markdown("---")
        if st.button("← Change Role", use_container_width=True):
            st.session_state.page = "role_select"
            st.session_state.role = None
            st.rerun()

    st.markdown(f"""
    <div class="hero">
      <div class="reg-tag">BATTERY REGISTRY</div>
      <h1>Select a Battery to Verify</h1>
      <p>Logged in as: <b style="color:#60a5fa">{role}</b> — Your view is personalised to show relevant data</p>
    </div>""", unsafe_allow_html=True)

    status_cfg = {
        "VERIFIED":      ("✅ VERIFIED",       "sbadge-v"),
        "SUSPICIOUS":    ("⚠️ SUSPICIOUS",     "sbadge-s"),
        "NON_COMPLIANT": ("❌ NON-COMPLIANT",   "sbadge-nc"),
    }

    for mfr_id, mfr in BATTERY_REGISTRY.items():
        for model_id, model_name in mfr["models"].items():
            bd  = load_battery(mfr_id, model_id)
            meta = bd["meta"]
            st_txt, st_cls = status_cfg.get(meta["verification_status"], ("?", ""))
            sc = score_to_css(meta["overall_score"])

            c_info, c_btn = st.columns([5, 1])
            with c_info:
                flags_html = ""
                for fl in meta.get("anomaly_flags", [])[:2]:
                    flags_html += f'<div class="anomaly" style="margin-top:0.5rem">{fl}</div>'
                st.markdown(f"""
                <div class="batt-card">
                  <div class="mfr">🏭 {mfr['name']} · {mfr['country']}</div>
                  <div class="mdl">{model_name}</div>
                  <div class="spec">⚗️ {meta['chemistry']} · ⚡ {meta['capacity_kwh']} kWh · 🏭 {meta['manufacturer_country']}</div>
                  <span class="sbadge {st_cls}">{st_txt}</span>
                  <span style="margin-left:1.2rem;color:{sc};font-weight:700;font-size:0.88rem">
                    {score_to_color(meta['overall_score'])} Score: {meta['overall_score']}/100
                  </span>
                  <span style="margin-left:1.2rem;color:#4a6080;font-size:0.78rem">
                    Trust: {meta['trust_score']}/100 · Verified data: {meta['data_real_pct']}%
                  </span>
                  {flags_html}
                </div>""", unsafe_allow_html=True)
            with c_btn:
                st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
                if st.button("View →", key=f"v_{mfr_id}_{model_id}", use_container_width=True):
                    st.session_state.selected_battery = (mfr_id, model_id)
                    st.session_state.page = "passport"
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PASSPORT — DISPATCHES TO ROLE VIEW
# ══════════════════════════════════════════════════════════════════════════════

def page_passport():
    mfr_id, model_id = st.session_state.selected_battery
    role = st.session_state.role
    data = load_battery(mfr_id, model_id)
    meta = data["meta"]
    mfr  = BATTERY_REGISTRY.get(mfr_id, {})

    report = run_full_verification(data, st.session_state.sensor)
    soh    = calculate_soh_composite(data)
    trust  = calculate_trust_score(data)

    icons = {"Consumer": "🙋", "Technician": "🔧", "Company": "🏭", "Regulator": "🏛"}
    with st.sidebar:
        st.markdown(f"### {icons.get(role,'')} {role}")
        st.markdown("---")
        if st.button("← Battery List", use_container_width=True):
            st.session_state.page = "browse"
            st.rerun()
        if st.button("↩ Change Role", use_container_width=True):
            st.session_state.page = "role_select"
            st.rerun()
        st.markdown("---")
        st.markdown(f"**{meta['model_name']}**")
        sc_c = score_to_css(report.overall_score)
        st.markdown(f"Score: <span style='color:{sc_c};font-weight:700'>{report.overall_score}/100</span>", unsafe_allow_html=True)
        st.markdown(f"Status: **{report.status}**")
        st.markdown(f"Trust: {report.trust_score}/100")

    # Header
    st_cfg = {
        "VERIFIED":      ("✅ VERIFIED",       "#22c55e"),
        "SUSPICIOUS":    ("⚠️ SUSPICIOUS",     "#f97316"),
        "NON_COMPLIANT": ("❌ NON-COMPLIANT",   "#ef4444"),
    }
    st_txt, st_col = st_cfg.get(report.status, ("?", "#64748b"))

    st.markdown(f"""
    <div class="hero">
      <div class="reg-tag">{mfr.get('name','')} · {meta['chemistry']} · {meta['capacity_kwh']} kWh · Reg. (EU) 2023/1542</div>
      <h1>🔋 {meta['model_name']}</h1>
      <p>Digital Battery Passport — 102 Data Points across 13 Categories</p>
      <div style="margin-top:1rem;display:flex;gap:1rem;flex-wrap:wrap;align-items:center">
        <span style="background:{st_col}18;border:1px solid {st_col}44;color:{st_col};
          padding:4px 14px;border-radius:20px;font-weight:700;font-size:0.88rem">{st_txt}</span>
        <span style="color:#7a92b4;font-size:0.84rem">
          Score <b style="color:{score_to_css(report.overall_score)}">{report.overall_score}/100</b>
        </span>
        <span style="color:#7a92b4;font-size:0.84rem">
          Trust <b style="color:{score_to_css(report.trust_score)}">{report.trust_score}/100</b>
        </span>
        <span style="color:#7a92b4;font-size:0.84rem">
          Verified data <b style="color:#60a5fa">{report.data_real_pct}%</b>
        </span>
        <span style="color:#7a92b4;font-size:0.84rem">
          Auth checks <b style="color:{score_to_css(report.authenticity_passed/report.authenticity_total*100)}">{report.authenticity_passed}/{report.authenticity_total} passed</b>
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Anomaly flags — visible to all roles
    if report.anomaly_flags:
        st.markdown('<div class="section-hdr">⚠️ Verification Anomalies</div>', unsafe_allow_html=True)
        for fl in report.anomaly_flags:
            st.markdown(f'<div class="anomaly">{fl}</div>', unsafe_allow_html=True)

    # Dispatch
    if role == "Consumer":    render_consumer(data, report, soh)
    elif role == "Technician": render_technician(data, report, soh)
    elif role == "Company":   render_company(data, report, soh, trust)
    elif role == "Regulator": render_regulator(data, report, soh, trust)


# ══════════════════════════════════════════════════════════════════════════════
# CONSUMER VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_consumer(data, report, soh):
    meta = data["meta"]
    elec = data.get("group_e_electrical", {}).get("data_points", {})
    op   = data.get("group_l_operational", {}).get("data_points", {})
    neg  = op.get("dp94_negative_events", {})
    doc  = data.get("group_f_conformity", {}).get("data_points", {})

    tabs = st.tabs(["🔋 Health & Safety", "🌱 Environment", "📋 Your Battery", "♻️ End of Life"])

    with tabs[0]:
        c1, c2 = st.columns([1, 1])
        with c1:
            gauge(soh["composite"], "Battery Health", soh["label"])
        with c2:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            hm = {
                "EXCELLENT": ("🟢", "#4ade80", "Your battery is in excellent health. No action needed."),
                "GOOD":      ("🟡", "#facc15", "Your battery is healthy with minor normal wear."),
                "MODERATE":  ("🟠", "#fb923c", "Moderate wear detected. Consider a service check."),
                "POOR":      ("🔴", "#f87171", "Significant degradation. Book a service soon."),
                "CRITICAL":  ("⛔", "#dc2626", "Critical. Stop using and contact your dealer now."),
            }
            ico_h, col_h, msg_h = hm.get(soh["label"], ("🟢","#4ade80",""))
            st.markdown(f"""
            <div style="background:#0d1526;border:1px solid #141f35;border-radius:12px;
                 padding:1.4rem;text-align:center;margin-bottom:1rem">
              <div style="font-size:2.5rem">{ico_h}</div>
              <div style="color:{col_h};font-size:1.1rem;font-weight:700;margin:0.4rem 0">{soh['label']}</div>
              <div style="color:#7a92b4;font-size:0.85rem">{msg_h}</div>
            </div>""", unsafe_allow_html=True)

            checks = [
                (neg.get("accidents", 0) == 0, "No accidents recorded"),
                (neg.get("thermal_runaway", 0) == 0, "No thermal events"),
                (bool(doc.get("dp49_eu_doc", {}).get("issued_by")), "EU certified"),
                (report.authenticity_passed >= report.authenticity_total - 1, "Data verified"),
            ]
            for ok, lbl in checks:
                c_s = "#4ade80" if ok else "#ef4444"
                ic_s = "✅" if ok else "❌"
                st.markdown(f'<div style="padding:0.35rem 0;color:{c_s};font-size:0.87rem">{ic_s} {lbl}</div>',
                            unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">💡 Charging Tips for Longer Battery Life</div>', unsafe_allow_html=True)
        dc = elec.get("dp38_power_capability", {}).get("dc_charging_kw", "N/A")
        tips = [
            ("🔋", "Charge between 20% and 80% daily — this alone significantly extends battery life"),
            ("⚡", f"Limit DC fast charging ({dc} kW) to max twice per day when possible"),
            ("❄️", "Cold weather? Let the car pre-condition before fast charging"),
            ("📱", "Keep your car software updated — updates improve battery management"),
            ("😴", "Storing the car long-term? Leave battery at 40–60% charge"),
        ]
        for tic, tt in tips:
            st.markdown(f'<div style="padding:0.35rem 0;color:#8aa0bc;font-size:0.86rem">{tic} {tt}</div>',
                        unsafe_allow_html=True)

    with tabs[1]:
        sus = report.sustainability_breakdown
        c1, c2 = st.columns([1, 1])
        with c1:
            gauge(sus["total"], "Sustainability", sus["label"], h=240)
        with c2:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            carbon = (data.get("group_b_carbon", {}).get("data_points", {})
                         .get("dp11_carbon_total", {}).get("value_kg_co2_per_kwh"))
            ren = (data.get("group_c_recycled", {}).get("data_points", {})
                       .get("dp23_renewable_energy", {}))
            cell_r = ren.get("cell_manufacturing_pct", 0)
            items = [
                (carbon is not None, f"Carbon footprint: {carbon} kg CO₂e/kWh" if carbon else "Carbon not declared ❌", bool(carbon)),
                (True, f"Battery factory: {cell_r}% renewable energy", cell_r >= 70),
                (True, "Materials: 0% recycled content currently", False),
                (True, "Can be returned free at end of life", True),
            ]
            for _, txt, good in items:
                c_p = "#4ade80" if good else "#f97316"
                i_p = "✅" if good else "⚠️"
                st.markdown(f'<div style="padding:0.4rem 0;color:{c_p};font-size:0.86rem">{i_p} {txt}</div>',
                            unsafe_allow_html=True)

        score_s = sus["total"]
        if score_s >= 70:
            msg = "✅ This battery has a **good** environmental profile with strong renewable energy use."
        elif score_s >= 50:
            msg = "⚠️ **Moderate** footprint. Main improvement needed: increasing recycled material content."
        else:
            msg = "❌ **Below average** sustainability. Key issues: carbon footprint, sourcing, or recycled content."
        st.info(msg)

    with tabs[2]:
        st.markdown('<div class="section-hdr">Battery Specifications — Plain Language</div>', unsafe_allow_html=True)
        ga = data.get("group_a_general", {}).get("data_points", {})
        w  = elec.get("dp43_warranty_calendar", {})
        myr = (data.get("group_k_lifetime", {}).get("data_points", {})
                   .get("dp86_manufacture_commissioning", {}).get("manufacture_year", 2024))

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="plain-card">
              <div class="ico">🔋</div><div class="ttl">Battery Capacity</div>
              <div class="big" style="color:#60a5fa">{meta['capacity_kwh']} kWh</div>
              <div class="sml">{meta['chemistry']} chemistry</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="plain-card">
              <div class="ico">⚡</div><div class="ttl">Max Fast Charge</div>
              <div class="big" style="color:#4ade80">{dc} kW</div>
              <div class="sml">DC fast charging</div></div>""", unsafe_allow_html=True)
        with c3:
            wend = myr + (w.get("years", 0) if isinstance(w.get("years"), int) else 0)
            st.markdown(f"""<div class="plain-card">
              <div class="ico">🛡</div><div class="ttl">Warranty</div>
              <div class="big" style="color:#a78bfa">{w.get('years','N/A')} yrs</div>
              <div class="sml">{w.get('km', 0):,} km · until ~{wend}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Where Was This Battery Made?</div>', unsafe_allow_html=True)
        dp3 = ga.get("dp3_place_of_manufacture", {})
        st.markdown(f"""
        <div class="card">
          <div class="lbl">Cells manufactured</div>
          <div class="val" style="font-size:1rem">{dp3.get('cells_location', 'N/A')}</div>
        </div>
        <div class="card">
          <div class="lbl">Battery assembled</div>
          <div class="val" style="font-size:1rem">{dp3.get('assembly_location', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="section-hdr">♻️ What Happens at End of Life?</div>', unsafe_allow_html=True)
        dp57 = (data.get("group_f_conformity", {}).get("data_points", {})
                    .get("dp57_waste_takeback", {}))
        dp58 = (data.get("group_f_conformity", {}).get("data_points", {})
                    .get("dp58_waste_safety", {}))
        points = dp57.get("dealer_points_eu", 0) or 0

        steps = [
            ("1️⃣", "Contact your nearest dealer", f"{points:,} EU service points available"),
            ("2️⃣", "Free take-back — no charge to you", "Required by EU law (Art. 64)"),
            ("3️⃣", "Battery is professionally recycled", "Materials recovered and reused"),
            ("4️⃣", "Never put in household waste", "Lithium batteries are hazardous — always recycle properly"),
        ]
        for stp, ttl, sub in steps:
            st.markdown(f"""
            <div style="display:flex;gap:1rem;padding:0.7rem 0;border-bottom:1px solid #0f1828">
              <div style="font-size:1.4rem">{stp}</div>
              <div>
                <div style="color:#c8d8f0;font-weight:600;font-size:0.9rem">{ttl}</div>
                <div style="color:#4a6080;font-size:0.8rem">{sub}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown(f"""<div class="warn-box">
          ⚠️ Emergency: {dp58.get('transport_class', 'ADR Class 9')} — 
          damaged batteries must be handled by specialists. 
          Contact your dealer immediately if battery is damaged.</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TECHNICIAN VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_technician(data, report, soh):
    tabs = st.tabs(["📊 SoH & Performance", "🔌 Sensor Validation", "🔧 Disassembly & Tools", "⚡ Full Technical Specs"])

    with tabs[0]:
        c1, c2 = st.columns([1, 2])
        with c1:
            gauge(soh["composite"], "SoH Composite", soh["label"])
        with c2:
            st.markdown('<div class="section-hdr">SoH Component Breakdown</div>', unsafe_allow_html=True)
            for name, comp in soh["components"].items():
                st.markdown(score_bar_html(
                    name.replace("_", " ").title(),
                    comp["score"], comp["weight"],
                    f"Value: {comp['value']}"
                ), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Performance vs Declared Baseline</div>', unsafe_allow_html=True)
        j = data.get("group_j_soh", {}).get("data_points", {})
        i = data.get("group_i_individual_performance", {}).get("data_points", {})

        rows_p = [
            ("Capacity (kWh)",          j.get("dp81_remaining_capacity", {}).get("value_kwh", "N/A"),         j.get("dp81_remaining_capacity", {}).get("pct_of_rated", 100)),
            ("Capacity Loss (%)",        j.get("dp81_remaining_capacity", {}).get("capacity_loss_kwh", 0),     None),
            ("Peak Power (kW)",          i.get("dp76_current_power", {}).get("peak_power_w", 0) / 1000,        i.get("dp76_current_power", {}).get("power_loss_pct", 100)),
            ("Internal Resistance (mΩ)", j.get("dp85_ohmic_resistance", {}).get("value_mohm", "N/A"),          None),
            ("RTW Efficiency (%)",       j.get("dp83_remaining_rtw", {}).get("value_pct", "N/A"),              j.get("dp83_remaining_rtw", {}).get("value_pct", 93)),
            ("Self-Discharge (%/month)", j.get("dp84_self_discharge", {}).get("value_pct_per_month", "N/A"),   None),
            ("SOCE (kWh)",               j.get("dp80_soce", {}).get("value_kwh", "N/A"),                       j.get("dp80_soce", {}).get("pct_of_rated", 100)),
            ("Cycle Count",              data.get("group_l_operational", {}).get("data_points", {}).get("dp93_charge_cycles", {}).get("charge_cycles", 0), None),
        ]

        tbl_rows = ""
        for param, val, pct in rows_p:
            if pct is not None:
                c_s = score_to_css(pct)
                st_html = f'<span style="color:{c_s};font-weight:700">{score_to_color(pct)} {pct:.0f}%</span>'
            else:
                st_html = '<span style="color:#4a6080">—</span>'
            tbl_rows += f"<tr><td style='color:#c8d8f0'>{param}</td><td style='color:#7a92b4'>{val}</td><td>{st_html}</td></tr>"

        st.markdown(f"""
        <table class="dt-tbl"><thead><tr>
          <th>Parameter</th><th>Current Value</th><th>Status</th>
        </tr></thead><tbody>{tbl_rows}</tbody></table>""", unsafe_allow_html=True)

        # Second life
        st.markdown('<div class="section-hdr">Second Life Assessment</div>', unsafe_allow_html=True)
        soh_val = soh["composite"]
        eligible = soh_val >= 80
        c_sl = "#4ade80" if eligible else "#f87171"
        st.markdown(f"""
        <div class="card">
          <div class="lbl">Second Life Eligibility (SoH ≥ 80%)</div>
          <div class="val" style="color:{c_sl}">{'✅ ELIGIBLE' if eligible else '❌ NOT ELIGIBLE'}</div>
          <div class="sub">Current SoH: {soh_val:.0f}% · {'Recommended use: Stationary energy storage' if eligible else 'Consider recycling'}</div>
        </div>""", unsafe_allow_html=True)

    with tabs[1]:
        sensor_panel(data)

    with tabs[2]:
        g = data.get("group_g_composition", {}).get("data_points", {})

        st.markdown('<div class="section-hdr">Cell Configuration</div>', unsafe_allow_html=True)
        cc = g.get("dp71_cell_count", {})
        c1, c2, c3, c4 = st.columns(4)
        for col, lbl, val in [
            (c1, "Total Modules", cc.get("modules", "N/A")),
            (c2, "Cells / Module", cc.get("cells_per_module", "N/A")),
            (c3, "Total Cells", cc.get("total_cells", "N/A")),
            (c4, "Arrangement", cc.get("arrangement_per_module", cc.get("arrangement", "N/A"))),
        ]:
            col.markdown(f"""<div class="card" style="text-align:center">
              <div class="lbl">{lbl}</div>
              <div class="val">{val}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Disassembly Steps</div>', unsafe_allow_html=True)
        steps = g.get("dp67_disassembly_steps", {}).get("steps", [])
        for s in steps:
            st.markdown(f'<div style="padding:0.4rem 0.8rem;margin-bottom:0.3rem;background:#0d1526;border:1px solid #141f35;border-radius:6px;color:#8aa0bc;font-size:0.83rem">{s}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">⚠️ Safety Warnings</div>', unsafe_allow_html=True)
        dw = g.get("dp70_damage_warnings", {})
        for key, val in [
            ("🔴 DANGER TO LIFE", dw.get("danger_to_life", "")),
            ("🔥 FIRE HAZARD", dw.get("fire_hazard", "")),
            ("☣️ CHEMICAL HAZARD", dw.get("chemical_hazard", "")),
            ("🏋️ MECHANICAL HAZARD", dw.get("mechanical_hazard", "")),
        ]:
            if val:
                st.markdown(f'<div class="anomaly"><b>{key}:</b> {val}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-hdr">Required Tools</div>', unsafe_allow_html=True)
            tools = g.get("dp69_required_tools", {})
            for cat, items in [("Safety", tools.get("safety", [])), ("Standard", tools.get("standard", [])), ("Special", tools.get("special", []))]:
                if items:
                    st.markdown(f"**{cat}:**")
                    for t in items:
                        st.markdown(f'<div style="color:#7a92b4;font-size:0.8rem;padding:2px 0">• {t}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="section-hdr">Part Numbers</div>', unsafe_allow_html=True)
            parts = g.get("dp64_part_numbers", {}).get("parts", [])
            if parts:
                rows_t = "".join(f"<tr><td style='color:#c8d8f0'>{p.get('component','')}</td><td style='font-family:JetBrains Mono,monospace;color:#60a5fa'>{p.get('part_number','N/A')}</td></tr>"
                                 for p in parts)
                st.markdown(f'<table class="dt-tbl"><thead><tr><th>Component</th><th>Part Number</th></tr></thead><tbody>{rows_t}</tbody></table>',
                            unsafe_allow_html=True)
            else:
                st.info("Part numbers not available for this battery.")

    with tabs[3]:
        st.markdown('<div class="section-hdr">Complete Electrical Specifications</div>', unsafe_allow_html=True)
        elec = data.get("group_e_electrical", {}).get("data_points", {})
        specs = [
            ("Rated Capacity (Ah)", elec.get("dp34_rated_capacity_ah", {}).get("value_ah")),
            ("Usable Capacity (kWh)", elec.get("dp34_rated_capacity_ah", {}).get("usable_kwh")),
            ("Min Voltage (V)", elec.get("dp35_min_voltage", {}).get("value_v")),
            ("Nominal Voltage (V)", elec.get("dp36_nominal_voltage", {}).get("value_v")),
            ("Max Voltage (V)", elec.get("dp37_max_voltage", {}).get("value_v")),
            ("Peak Discharge (kW)", elec.get("dp38_power_capability", {}).get("peak_discharge_kw")),
            ("DC Charging Max (kW)", elec.get("dp38_power_capability", {}).get("dc_charging_kw")),
            ("AC Charging 3-Phase (kW)", elec.get("dp38_power_capability", {}).get("ac_charging_kw_3phase")),
            ("Recuperation (kW)", elec.get("dp38_power_capability", {}).get("recuperation_kw")),
            ("Cycle Life (to 70% SoH)", elec.get("dp40_expected_lifetime", {}).get("cycles_to_70pct_soh")),
            ("SoH Exhaustion Threshold (%)", elec.get("dp41_capacity_threshold", {}).get("soh_threshold_pct")),
            ("Storage Temp Min (°C)", elec.get("dp42_storage_temperature", {}).get("min_c")),
            ("Storage Temp Max (°C)", elec.get("dp42_storage_temperature", {}).get("max_c")),
            ("RTW Efficiency New (%)", elec.get("dp44_rtw_initial", {}).get("value_pct")),
            ("Cell Internal Resistance (mΩ)", elec.get("dp46_internal_resistance_cell", {}).get("value_mohm")),
            ("Pack Internal Resistance (mΩ)", elec.get("dp47_internal_resistance_pack", {}).get("value_mohm")),
            ("Cycle Test C-Rate", f"{elec.get('dp48_c_rate', {}).get('charge_c','?')}C charge / {elec.get('dp48_c_rate', {}).get('discharge_c','?')}C discharge"),
        ]
        rows_t = "".join(f"<tr><td style='color:#7a92b4'>{lbl}</td><td style='color:#c8d8f0;font-weight:500'>{val if val is not None else '—'}</td></tr>" for lbl, val in specs)
        st.markdown(f'<table class="dt-tbl"><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>{rows_t}</tbody></table>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_company(data, report, soh, trust):
    tabs = st.tabs(["📊 Verification Summary", "🌍 Carbon Footprint", "♻️ Recycled Content", "🌐 Supply Chain", "📅 Compliance Timeline", "🔍 All Data Points"])

    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            gauge(report.sustainability_score, "Sustainability", score_to_label(report.sustainability_score))
        with c2:
            gauge(soh["composite"], "Battery SoH", soh["label"])
        with c3:
            gauge(trust["total"], "Data Trust Score", trust["label"])

        st.markdown('<div class="section-hdr">Sustainability Score Breakdown</div>', unsafe_allow_html=True)
        sus = report.sustainability_breakdown
        for name, comp in sus["components"].items():
            st.markdown(score_bar_html(
                name.replace("_", " ").title(), comp["score"],
                comp["weight"], comp["detail"]
            ), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Authenticity Checks</div>', unsafe_allow_html=True)
        passed = report.authenticity_passed
        total  = report.authenticity_total
        pct    = passed / total * 100
        st.markdown(f"""
        <div style="background:#0d1526;border:1px solid #141f35;border-radius:10px;
             padding:1rem 1.3rem;margin-bottom:1rem">
          <span style="color:#c8d8f0;font-weight:700;font-size:1rem">{passed}/{total} checks passed</span>
          <span style="float:right;color:{score_to_css(pct)};font-weight:700">{pct:.0f}%</span>
          <div style="margin-top:0.5rem;background:#131d2e;border-radius:4px;height:6px">
            <div style="height:6px;border-radius:4px;background:{score_to_css(pct)};width:{pct}%"></div>
          </div>
        </div>""", unsafe_allow_html=True)
        for chk in report.authenticity_checks:
            check_row(chk)

    with tabs[1]:
        carbon_dp = data.get("group_b_carbon", {}).get("data_points", {})
        c11 = carbon_dp.get("dp11_carbon_total", {})
        c12 = carbon_dp.get("dp12_carbon_class", {})
        lc  = carbon_dp.get("dp16_carbon_lifecycle", {})

        c1, c2, c3 = st.columns(3)
        carbon_val = c11.get("value_kg_co2_per_kwh")
        with c1:
            vc = score_to_css(100 - (carbon_val or 50) / 1.2) if carbon_val else "#4a6080"
            st.markdown(f"""<div class="card">
              <div class="lbl">Carbon Footprint</div>
              <div class="val" style="color:{vc}">{carbon_val if carbon_val else 'NOT DECLARED'} <span style="font-size:0.7rem">kg CO₂e/kWh</span></div>
              <div class="sub">Total: {c11.get('total_kg_co2', 'N/A'):,} kg CO₂e</div></div>""", unsafe_allow_html=True)
        with c2:
            cls_c = "#4ade80" if c12.get("declared_class") == "A" else ("#facc15" if c12.get("declared_class") == "B" else "#f87171")
            st.markdown(f"""<div class="card">
              <div class="lbl">Performance Class</div>
              <div class="val" style="color:{cls_c}">Class {c12.get('declared_class', 'N/A')}</div>
              <div class="sub">EU benchmark classification</div></div>""", unsafe_allow_html=True)
        with c3:
            from engine.verification_engine import BENCHMARKS
            bench = BENCHMARKS.get(data["meta"]["chemistry"], {})
            lo, hi = bench.get("carbon_kwh_range", [0, 100])
            in_range = lo <= (carbon_val or 0) <= hi if carbon_val else False
            rc = "#4ade80" if in_range else "#f87171"
            st.markdown(f"""<div class="card">
              <div class="lbl">{data['meta']['chemistry']} Benchmark</div>
              <div class="val" style="color:{rc}">{'✅ IN RANGE' if in_range else '❌ OUT OF RANGE'}</div>
              <div class="sub">{lo}–{hi} kg CO₂e/kWh expected</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Carbon Footprint by Lifecycle Phase</div>', unsafe_allow_html=True)
        lifecycle_chart(lc.get("phases", {}))

        st.markdown('<div class="section-hdr">Lifecycle Phase Details</div>', unsafe_allow_html=True)
        phases = lc.get("phases", {})
        if phases:
            rows_lc = ""
            total_co2 = lc.get("total_kg_co2", 1)
            for ph, d in phases.items():
                if d:
                    v = d.get("kg_co2", 0)
                    pct_lc = d.get("pct", v / total_co2 * 100 if total_co2 else 0)
                    c_lc = "#4ade80" if v < 0 else ("#ef4444" if v > 2000 else "#f97316")
                    rows_lc += f"<tr><td style='color:#c8d8f0'>{ph.replace('_',' ').title()}</td><td style='color:{c_lc};font-weight:600'>{v:+,} kg</td><td style='color:#7a92b4'>{pct_lc:+.0f}%</td></tr>"
            st.markdown(f'<table class="dt-tbl"><thead><tr><th>Phase</th><th>CO₂e</th><th>Share</th></tr></thead><tbody>{rows_lc}</tbody></table>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="section-hdr">Current Recycled Content vs EU Mandatory Targets</div>', unsafe_allow_html=True)
        recycled_gap_table(data)

        st.markdown('<div class="section-hdr">Renewable Energy in Manufacturing</div>', unsafe_allow_html=True)
        ren = data.get("group_c_recycled", {}).get("data_points", {}).get("dp23_renewable_energy", {})
        c1, c2 = st.columns(2)
        cell_r = ren.get("cell_manufacturing_pct", 0) or 0
        pack_r = ren.get("pack_assembly_pct", 0) or 0
        with c1:
            st.markdown(score_bar_html("Cell Manufacturing", cell_r, detail=ren.get("cell_source", "")), unsafe_allow_html=True)
        with c2:
            st.markdown(score_bar_html("Pack Assembly", pack_r, detail=ren.get("assembly_source", "")), unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="section-hdr">Supply Chain Risk by Material</div>', unsafe_allow_html=True)
        origins = (data.get("group_d_sourcing", {}).get("data_points", {})
                       .get("dp29_country_of_origin", {}).get("origins", {}))
        supply_risk_table(origins)

        st.markdown('<div class="section-hdr">Due Diligence & Traceability</div>', unsafe_allow_html=True)
        sc = data.get("group_d_sourcing", {}).get("data_points", {})
        verif = sc.get("dp26_independent_verification", {})
        strat = sc.get("dp24_due_diligence_strategy", {})

        is_blockchain = "blockchain" in str(strat.get("traceability", "")).lower() or "blockchain" in str(verif).lower()
        td_items = [
            (bool(strat.get("frameworks")), f"Due diligence framework: {', '.join(strat.get('frameworks', ['None']))}"),
            (bool(verif.get("verifier") and verif["verifier"] != "None"), f"Independent verifier: {verif.get('verifier', 'None')}"),
            (is_blockchain, f"Blockchain traceability: {strat.get('traceability', 'None')}"),
        ]
        for ok, txt in td_items:
            c_td = "#4ade80" if ok else "#f87171"
            ic_td = "✅" if ok else "❌"
            st.markdown(f'<div style="padding:0.4rem 0;color:{c_td};font-size:0.86rem">{ic_td} {txt}</div>', unsafe_allow_html=True)

        # Supplier table
        st.markdown('<div class="section-hdr">Supply Chain Tier 1 Suppliers</div>', unsafe_allow_html=True)
        suppliers = sc.get("dp28_supplier_names", {}).get("suppliers", [])
        if suppliers:
            rows_s = "".join(f"<tr><td style='color:#60a5fa'>{s.get('role','')}</td><td style='color:#c8d8f0'>{s.get('name','')}</td><td style='color:#7a92b4'>{s.get('location','')}</td></tr>" for s in suppliers)
            st.markdown(f'<table class="dt-tbl"><thead><tr><th>Role</th><th>Company</th><th>Location</th></tr></thead><tbody>{rows_s}</tbody></table>', unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="section-hdr">EU Regulatory Compliance Horizon — 2024 to 2036</div>', unsafe_allow_html=True)
        compliance_timeline(report.compliance_by_year)

        st.markdown('<div class="section-hdr">Required Actions</div>', unsafe_allow_html=True)
        has_actions = False
        for yr, d in report.compliance_by_year.items():
            if d["failures"]:
                has_actions = True
                st.markdown(f"**By {yr}:**")
                for fl in d["failures"]:
                    st.markdown(f'<div class="anomaly">{fl}</div>', unsafe_allow_html=True)
        if not has_actions:
            st.markdown('<div class="ok-box">✅ No required actions identified for any compliance horizon</div>', unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="section-hdr">All 102 DPP Data Points — Filterable</div>', unsafe_allow_html=True)
        all_102_table(data, "Company")


# ══════════════════════════════════════════════════════════════════════════════
# REGULATOR VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_regulator(data, report, soh, trust):
    tabs = st.tabs(["🏛 Conformity Evidence", "🔍 Verification Audit", "📊 Trust Score", "📅 Compliance", "🌱 Sustainability", "🔌 Sensors", "📋 All 102 Points"])

    with tabs[0]:
        st.markdown('<div class="section-hdr">EU Declaration of Conformity</div>', unsafe_allow_html=True)
        conf = data.get("group_f_conformity", {}).get("data_points", {})
        doc_ref = conf.get("dp50_doc_reference", {})
        ce      = conf.get("dp51_ce_marking", {})

        c1, c2 = st.columns(2)
        with c1:
            ref = doc_ref.get("reference", "NOT AVAILABLE")
            nb  = doc_ref.get("notified_body", "NOT AVAILABLE")
            nbr = doc_ref.get("notified_body_ref", "N/A")
            trn = doc_ref.get("test_report_ref", "NOT AVAILABLE")
            dt  = doc_ref.get("date", "N/A")
            ok_ref = ref and ref != "NOT AVAILABLE"
            c_ref = "#4ade80" if ok_ref else "#ef4444"
            st.markdown(f"""
            <div class="card">
              <div class="lbl">Declaration of Conformity Reference</div>
              <div class="val" style="color:{c_ref};font-size:1rem;font-family:'JetBrains Mono',monospace">{ref}</div>
              <div class="sub">Issued: {dt}</div>
            </div>
            <div class="card">
              <div class="lbl">Notified Body</div>
              <div class="val" style="font-size:1rem">{nb}</div>
              <div class="sub">Reference No.: {nbr}</div>
            </div>
            <div class="card">
              <div class="lbl">Test Report Reference</div>
              <div class="val" style="font-size:0.95rem;font-family:'JetBrains Mono',monospace">{trn}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            # Applied standards
            st.markdown('<div class="section-hdr">Applied Harmonised Standards</div>', unsafe_allow_html=True)
            standards = (data.get("group_m_metadata", {}).get("data_points", {})
                             .get("dp101_standards", {}).get("standards", []))
            for std in standards:
                ok_s = std != "Unknown — not declared"
                c_std = "#4ade80" if ok_s else "#f87171"
                ic_std = "✅" if ok_s else "❌"
                st.markdown(f'<div style="padding:0.3rem 0;color:{c_std};font-size:0.83rem">{ic_std} {std}</div>', unsafe_allow_html=True)

        # Test results
        st.markdown('<div class="section-hdr">Test Report Results</div>', unsafe_allow_html=True)
        auth_dp = data.get("group_h_authority", {}).get("data_points", {})
        test    = auth_dp.get("dp73_test_reports", {})
        results = test.get("results", {})
        if results:
            for test_name, result_val in results.items():
                ok_t = "PASS" in str(result_val).upper()
                c_t = "#4ade80" if ok_t else "#f87171"
                ic_t = "✅" if ok_t else "❌"
                st.markdown(f'<div style="padding:0.35rem 0;color:{c_t};font-size:0.84rem">{ic_t} <b>{test_name.replace("_"," ").title()}:</b> {result_val}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="anomaly">No test report results available — notified body testing not documented</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="section-hdr">Authentication Checks — Full Audit Trail</div>', unsafe_allow_html=True)
        passed = report.authenticity_passed
        total  = report.authenticity_total
        pct_a  = passed / total * 100
        st.markdown(f"""
        <div style="background:#0d1526;border:1px solid #141f35;border-radius:10px;padding:1rem 1.3rem;margin-bottom:1rem">
          <span style="color:#c8d8f0;font-size:1rem;font-weight:700">{passed}/{total} checks passed · {pct_a:.0f}%</span>
        </div>""", unsafe_allow_html=True)
        for chk in report.authenticity_checks:
            check_row(chk)

        if report.anomaly_flags:
            st.markdown('<div class="section-hdr">All Anomaly Flags</div>', unsafe_allow_html=True)
            for fl in report.anomaly_flags:
                st.markdown(f'<div class="anomaly">{fl}</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="section-hdr">Trust Score Breakdown</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            gauge(trust["total"], "Trust Score", trust["label"])
        with c2:
            for comp, val in trust["components"].items():
                max_v = 50 if comp == "data_quality" else 30
                pct_t = val / max_v * 100 if max_v else 0
                st.markdown(score_bar_html(comp.replace("_"," ").title(), min(100, pct_t), detail=f"Points: {val}"), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Data Quality by Group (% REAL data)</div>', unsafe_allow_html=True)
        breakdown = trust.get("group_breakdown", {})
        for grp, pct_g in breakdown.items():
            st.markdown(score_bar_html(grp, pct_g), unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Data Provenance Overview</div>', unsafe_allow_html=True)
        real_p = report.data_real_pct
        mock_p = report.data_mock_pct
        fig = go.Figure(go.Pie(
            labels=["✅ Verified REAL", "⚠️ Manufacturer Estimate (MOCK)"],
            values=[real_p, mock_p],
            hole=0.55,
            marker={"colors": ["#16a34a", "#d97706"]},
            textfont={"color": "#c8d8f0", "size": 12}
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=200,
                          margin=dict(t=10, b=10, l=10, r=10),
                          legend={"font": {"color": "#7a92b4"}, "bgcolor": "rgba(0,0,0,0)"})
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tabs[3]:
        st.markdown('<div class="section-hdr">Full Compliance Timeline — Reg. (EU) 2023/1542</div>', unsafe_allow_html=True)
        compliance_timeline(report.compliance_by_year)
        for yr, d in report.compliance_by_year.items():
            if d["requirements"]:
                with st.expander(f"Requirements for {yr} ({len(d['requirements'])} items)"):
                    for req in d["requirements"]:
                        st.markdown(f'<div style="color:#7a92b4;font-size:0.8rem;padding:2px 0">• {req}</div>', unsafe_allow_html=True)

    with tabs[4]:
        render_company(data, report, soh, trust)

    with tabs[5]:
        sensor_panel(data)

    with tabs[6]:
        st.markdown('<div class="section-hdr">Complete DPP — All 102 Data Points (Full Regulator Access)</div>', unsafe_allow_html=True)
        all_102_table(data, "Regulator")

        # Access level distribution
        st.markdown('<div class="section-hdr">Data Points by Access Level</div>', unsafe_allow_html=True)
        levels = {"L1 — Public": 0, "L2 — Restricted": 0, "L3 — Authorities": 0, "L4 — Individual": 0}
        group_map_keys = [
            "group_a_general","group_b_carbon","group_c_recycled","group_d_sourcing",
            "group_e_electrical","group_f_conformity","group_g_composition","group_h_authority",
            "group_i_individual_performance","group_j_soh","group_k_lifetime",
            "group_l_operational","group_m_metadata"
        ]
        for gk in group_map_keys:
            for _, dp in data.get(gk, {}).get("data_points", {}).items():
                al = dp.get("access_level", 1)
                key = f"L{al} — {['Public','Restricted','Authorities','Individual'][al-1]}"
                if key in levels:
                    levels[key] += 1

        c1, c2, c3, c4 = st.columns(4)
        colors_lv = {"L1 — Public": "#60a5fa", "L2 — Restricted": "#c084fc", "L3 — Authorities": "#f87171", "L4 — Individual": "#34d399"}
        for col, (lbl, cnt) in zip([c1, c2, c3, c4], levels.items()):
            c_lv = colors_lv.get(lbl, "#60a5fa")
            col.markdown(f"""<div class="card" style="text-align:center">
              <div class="lbl">{lbl}</div>
              <div class="val" style="color:{c_lv}">{cnt}</div>
              <div class="sub">data points</div></div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    page = st.session_state.page
    if page == "role_select":
        page_role_select()
    elif page == "browse":
        if not st.session_state.role:
            st.session_state.page = "role_select"
            st.rerun()
        page_browse()
    elif page == "passport":
        if not st.session_state.selected_battery:
            st.session_state.page = "browse"
            st.rerun()
        page_passport()


if __name__ == "__main__":
    main()
