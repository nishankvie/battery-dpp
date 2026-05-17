"""
VeriCell Pitch Deck Generator
Produces VeriCell_Pitch_Deck.pptx — 14 slides, dark theme, hackathon-ready.
Run: python generate_slides.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ─── Colors ───────────────────────────────────────────────────────────────────
BG        = RGBColor(0x06, 0x0a, 0x12)   # near-black navy
TEXT      = RGBColor(0xe8, 0xf0, 0xff)   # near-white
ACCENT    = RGBColor(0x4a, 0xde, 0x80)   # green
RED       = RGBColor(0xf8, 0x71, 0x71)   # red/block
AMBER     = RGBColor(0xfb, 0xbf, 0x24)   # amber/review
MUTED     = RGBColor(0x7a, 0x92, 0xb4)   # muted blue
CARD      = RGBColor(0x0d, 0x15, 0x26)   # card background
BORDER    = RGBColor(0x1e, 0x30, 0x50)   # border/line
WHITE     = RGBColor(0xff, 0xff, 0xff)

# ─── Dimensions (16:9) ────────────────────────────────────────────────────────
W = Inches(13.33)
H = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

blank_layout = prs.slide_layouts[6]  # completely blank


# ─── Helpers ──────────────────────────────────────────────────────────────────

def new_slide():
    slide = prs.slides.add_slide(blank_layout)
    # Full-bleed background
    bg = slide.shapes.add_shape(1, 0, 0, W, H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    return slide


def txb(slide, text, x, y, w, h,
        size=20, bold=False, color=TEXT, align=PP_ALIGN.LEFT,
        italic=False, wrap=True):
    """Add a text box."""
    shape = slide.shapes.add_textbox(x, y, w, h)
    shape.word_wrap = wrap
    tf = shape.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return shape


def txb_multi(slide, lines, x, y, w, h, size=18, color=TEXT, bold_first=False):
    """Add a text box with multiple lines (list of (text, bold, color) tuples)."""
    shape = slide.shapes.add_textbox(x, y, w, h)
    shape.word_wrap = True
    tf = shape.text_frame
    tf.word_wrap = True
    first = True
    for item in lines:
        if isinstance(item, str):
            txt, bld, col = item, False, color
        else:
            txt, bld, col = item[0], item[1], item[2] if len(item) > 2 else color

        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(3)
        run = p.add_run()
        run.text = txt
        run.font.size = Pt(size)
        run.font.bold = bld or (bold_first and first)
        run.font.color.rgb = col
        run.font.name = "Calibri"
    return shape


def box(slide, x, y, w, h, fill=CARD, border=BORDER, border_width=1.5):
    """Add a filled rectangle."""
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = border
    shape.line.width = Pt(border_width)
    return shape


def hline(slide, y, color=BORDER):
    """Horizontal rule."""
    shape = slide.shapes.add_shape(1, Inches(0.5), y, W - Inches(1), Pt(1))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def slide_label(slide, text):
    """Small category label top-left."""
    txb(slide, text, Inches(0.5), Inches(0.18), Inches(6), Inches(0.35),
        size=11, color=MUTED, bold=False)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — HOOK
# ══════════════════════════════════════════════════════════════════════════════
s1 = new_slide()

# Faded watermark "€3B"
txb(s1, "€3B", Inches(2.5), Inches(0.8), Inches(8), Inches(5.5),
    size=220, bold=True, color=RGBColor(0x10, 0x1e, 0x38), align=PP_ALIGN.CENTER)

# Main 3-line statement
txb(s1, "60–70% of EV batteries get destroyed.", Inches(0.8), Inches(1.4), Inches(11.7), Inches(1),
    size=38, bold=True, color=TEXT, align=PP_ALIGN.CENTER)
txb(s1, "Not because they're bad.", Inches(0.8), Inches(2.3), Inches(11.7), Inches(0.9),
    size=36, bold=False, color=MUTED, align=PP_ALIGN.CENTER)
txb(s1, "Because nobody trusts the data.", Inches(0.8), Inches(3.1), Inches(11.7), Inches(0.9),
    size=38, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

hline(s1, Inches(4.25))

txb(s1, "€1–3 Billion destroyed annually.  We fix the trust layer.",
    Inches(0.8), Inches(4.45), Inches(11.7), Inches(0.7),
    size=20, bold=False, color=MUTED, align=PP_ALIGN.CENTER)

txb(s1, "TrustLayer VeriCell", Inches(9.5), Inches(6.9), Inches(3.3), Inches(0.5),
    size=14, bold=True, color=ACCENT, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
s2 = new_slide()
slide_label(s2, "PROBLEM")
txb(s2, "The Battery Data Crisis", Inches(0.5), Inches(0.5), Inches(12), Inches(0.9),
    size=38, bold=True, color=TEXT)
hline(s2, Inches(1.5))

bullets = [
    ("EU Reg. 2023/1542 mandates a Digital Product Passport for every EV battery", False, TEXT),
    ("102 data points: carbon footprint, health, recycled content, supply chain", False, MUTED),
    ("Manufacturers self-report.  Nobody cross-validates.", True, AMBER),
    ("Buyers can't trust SoH claims.  Regulators can't enforce compliance.", False, TEXT),
    ("Result: batteries are scrapped instead of reused — billions wasted.", True, RED),
]

y = Inches(1.7)
for txt, bld, col in bullets:
    dot = slide.shapes if False else None
    bx = box(s2, Inches(0.5), y + Inches(0.07), Inches(0.08), Inches(0.25),
              fill=ACCENT if not bld else RED, border=RGBColor(0,0,0), border_width=0)
    txb(s2, txt, Inches(0.75), y, Inches(12.1), Inches(0.75),
        size=21, bold=bld, color=col)
    y += Inches(0.88)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — MULTI-STAKEHOLDER PAIN
# ══════════════════════════════════════════════════════════════════════════════
s3 = new_slide()
slide_label(s3, "PAIN")
txb(s3, "Three Stakeholders. One Missing Layer.", Inches(0.5), Inches(0.5), Inches(12.3), Inches(0.9),
    size=34, bold=True, color=TEXT)
hline(s3, Inches(1.5))

boxes_data = [
    ("🏢  Business", [
        "Cannot verify supplier data",
        "No ERP action on bad actors",
        "Compliance risk from 2027",
        "Cross-border data inconsistency",
    ], AMBER),
    ("🏛  Regulator", [
        "Cannot detect who falsifies data",
        "No centralized violation tracking",
        "Manual audits only",
        "No real-time EU-wide view",
    ], RED),
    ("👤  Consumer", [
        "Pays €10K+ with no reliable health info",
        "No trusted certificate at point of sale",
        "Cannot assess second-life value",
        "No recourse if data was wrong",
    ], ACCENT),
]

bw = Inches(3.9)
bh = Inches(4.8)
bx_start = Inches(0.4)
gap = Inches(0.27)

for i, (title, points, accent_col) in enumerate(boxes_data):
    bx_x = bx_start + i * (bw + gap)
    bx_y = Inches(1.65)
    box(s3, bx_x, bx_y, bw, bh, fill=CARD, border=accent_col, border_width=2)
    # Title bar
    title_bar = box(s3, bx_x, bx_y, bw, Inches(0.6), fill=accent_col, border=accent_col, border_width=0)
    txb(s3, title, bx_x + Inches(0.15), bx_y + Inches(0.08), bw - Inches(0.3), Inches(0.5),
        size=18, bold=True, color=BG)
    py = bx_y + Inches(0.75)
    for pt in points:
        txb(s3, f"• {pt}", bx_x + Inches(0.2), py, bw - Inches(0.35), Inches(0.7),
            size=16, color=TEXT)
        py += Inches(0.85)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — CURRENT GAP
# ══════════════════════════════════════════════════════════════════════════════
s4 = new_slide()
slide_label(s4, "GAP")
txb(s4, "Existing Tools Store Data. Nobody Validates It.",
    Inches(0.5), Inches(0.5), Inches(12.3), Inches(0.9),
    size=34, bold=True, color=TEXT)
hline(s4, Inches(1.5))

# Table header
col_x = [Inches(0.5), Inches(3.6), Inches(7.8)]
col_w = [Inches(3.0), Inches(4.1), Inches(4.9)]
header_y = Inches(1.65)
box(s4, Inches(0.5), header_y, Inches(12.33), Inches(0.5), fill=BORDER, border=BORDER, border_width=0)
for label, cx, cw in zip(["Tool", "What It Does", "What's Missing"], col_x, col_w):
    txb(s4, label, cx + Inches(0.1), header_y + Inches(0.08), cw, Inches(0.38),
        size=16, bold=True, color=TEXT)

rows = [
    ("Minespider",  "Blockchain supply chain storage",    "No cross-field validation"),
    ("Spherity",    "Digital identity credentials",        "No trust scoring or ERP action"),
    ("Circulor",    "Traceability platform",               "No procurement decision output"),
    ("Raw DPP",     "Self-reported data container",        "Anyone can type any number"),
]

row_colors = [CARD, RGBColor(0x0a, 0x12, 0x22)]
ry = header_y + Inches(0.52)
for idx, (tool, does, missing) in enumerate(rows):
    rh = Inches(0.72)
    box(s4, Inches(0.5), ry, Inches(12.33), rh,
        fill=row_colors[idx % 2], border=BORDER, border_width=0.5)
    for text, cx, cw, col in [
        (tool,    col_x[0], col_w[0], AMBER),
        (does,    col_x[1], col_w[1], MUTED),
        (missing, col_x[2], col_w[2], RED),
    ]:
        txb(s4, text, cx + Inches(0.1), ry + Inches(0.12), cw, Inches(0.5),
            size=16, bold=(col == AMBER), color=col)
    ry += rh

# Bottom bold line
box(s4, Inches(0.5), Inches(6.55), Inches(12.33), Inches(0.65),
    fill=RGBColor(0x1a, 0x08, 0x08), border=RED, border_width=1.5)
txb(s4, "The data exists.  The trust doesn't.",
    Inches(0.7), Inches(6.63), Inches(12), Inches(0.5),
    size=22, bold=True, color=RED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — SOLUTION
# ══════════════════════════════════════════════════════════════════════════════
s5 = new_slide()
slide_label(s5, "SOLUTION")

txb(s5, "TrustLayer VeriCell",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(1.1),
    size=48, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

txb(s5, "AI-powered trust validation for battery DPP data —\nturning unverified passports into live ERP decisions.",
    Inches(1.0), Inches(1.6), Inches(11.3), Inches(1.4),
    size=24, bold=False, color=TEXT, align=PP_ALIGN.CENTER)

hline(s5, Inches(3.1))

output_boxes = [
    ("🔢", "Trust Score", "0 – 100", ACCENT),
    ("⚖️", "Decision", "APPROVE / REVIEW / BLOCK", AMBER),
    ("🔗", "ERP Action", "Live sync to procurement", RGBColor(0x60, 0xa5, 0xfa)),
    ("🔬", "Level 2 Badge", "Physical Sensor Verified", RGBColor(0xc0, 0x84, 0xfc)),
]

ow = Inches(2.88)
oh = Inches(2.8)
ox_start = Inches(0.42)
oy = Inches(3.35)
ogap = Inches(0.21)

for i, (icon, title, sub, col) in enumerate(output_boxes):
    ox = ox_start + i * (ow + ogap)
    box(s5, ox, oy, ow, oh, fill=CARD, border=col, border_width=2.5)
    txb(s5, icon,  ox, oy + Inches(0.3),  ow, Inches(0.8), size=34, align=PP_ALIGN.CENTER)
    txb(s5, title, ox, oy + Inches(1.15), ow, Inches(0.6), size=18, bold=True,  color=col,  align=PP_ALIGN.CENTER)
    txb(s5, sub,   ox, oy + Inches(1.75), ow, Inches(0.7), size=14, bold=False, color=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — HOW IT WORKS
# ══════════════════════════════════════════════════════════════════════════════
s6 = new_slide()
slide_label(s6, "ARCHITECTURE")
txb(s6, "The Validation Pipeline",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s6, Inches(1.3))

flow_steps = [
    ("Battery JSON",       ["102 data points", "13 groups", "EU DPP format"],           MUTED),
    ("Trust Engine",       ["6 AI modules", "8 math checks", "+ Physical sensor"],        ACCENT),
    ("Verified Passport",  ["Trust Score + L2 Badge", "APPROVE/REVIEW/BLOCK", "QR Cert"], AMBER),
    ("ERP Action",         ["Odoo sync", "Live write-back", "Procurement trigger"],      RGBColor(0x60, 0xa5, 0xfa)),
]

fw = Inches(2.8)
fh = Inches(2.2)
fx_start = Inches(0.4)
fy = Inches(1.5)
fgap = Inches(0.44)

for i, (title, subs, col) in enumerate(flow_steps):
    fx = fx_start + i * (fw + fgap)
    box(s6, fx, fy, fw, fh, fill=CARD, border=col, border_width=2)
    txb(s6, title, fx, fy + Inches(0.15), fw, Inches(0.55),
        size=18, bold=True, color=col, align=PP_ALIGN.CENTER)
    sy = fy + Inches(0.75)
    for sub in subs:
        txb(s6, sub, fx + Inches(0.1), sy, fw - Inches(0.2), Inches(0.42),
            size=14, color=MUTED, align=PP_ALIGN.CENTER)
        sy += Inches(0.42)
    # Arrow (except after last)
    if i < len(flow_steps) - 1:
        ax = fx + fw + Inches(0.08)
        txb(s6, "→", ax, fy + Inches(0.75), Inches(0.3), Inches(0.55),
            size=28, bold=True, color=BORDER, align=PP_ALIGN.CENTER)

hline(s6, Inches(3.85))
txb(s6, "6 Engine Modules:", Inches(0.5), Inches(4.0), Inches(3), Inches(0.45),
    size=16, bold=True, color=MUTED)

modules_left  = ["Sustainability Scorer (5 sub-scores, weighted)",
                 "Authenticity Checker (8 cross-field math checks)",
                 "Compliance Tracker (2024 / 2027 / 2031 / 2036)"]
modules_right = ["Sensor Validator (voltage, resistance, temp, SoC)",
                 "Trust Score Calculator (data quality + evidence)",
                 "SoH Composite (5 health parameters)"]

my = Inches(4.5)
for txt in modules_left:
    txb(s6, f"• {txt}", Inches(0.5), my, Inches(6.2), Inches(0.5), size=15, color=TEXT)
    my += Inches(0.5)
my = Inches(4.5)
for txt in modules_right:
    txb(s6, f"• {txt}", Inches(6.9), my, Inches(6.0), Inches(0.5), size=15, color=TEXT)
    my += Inches(0.5)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — COVERAGE
# ══════════════════════════════════════════════════════════════════════════════
s7 = new_slide()
slide_label(s7, "COVERAGE")
txb(s7, "Full EU 2023/1542 Coverage",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s7, Inches(1.3))

txb(s7, "13 Data Groups (A–M)", Inches(0.5), Inches(1.45), Inches(6.2), Inches(0.5),
    size=17, bold=True, color=ACCENT)

groups = [
    "A — General Info",       "B — Carbon Footprint",
    "C — Recycled Content",   "D — Responsible Sourcing",
    "E — Electrical",         "F — Conformity & Labelling",
    "G — Composition",        "H — Authority Information",
    "I — Individual Perf.",   "J — State of Health",
    "K — Expected Lifetime",  "L — Operational Data",
    "M — Identification",
]

gy = Inches(1.95)
for idx, grp in enumerate(groups):
    col_offset = Inches(0) if idx % 2 == 0 else Inches(3.2)
    if idx % 2 == 0 and idx > 0:
        gy += Inches(0.43)
    elif idx == 0:
        pass
    txb(s7, f"• {grp}", Inches(0.5) + col_offset, gy, Inches(3.1), Inches(0.42),
        size=14, color=MUTED)
gy += Inches(0.43)

# Right column: compliance timeline
txb(s7, "Compliance Timeline", Inches(7.1), Inches(1.45), Inches(5.8), Inches(0.5),
    size=17, bold=True, color=ACCENT)

timeline = [
    ("2024 ✅", "DoC, CE marking, labelling",                          ACCENT),
    ("2027 ⚠️", "QR code, carbon declaration (Art. 7)",                AMBER),
    ("2031 📅", "Recycled Co ≥16%, Li ≥6%, Ni ≥6% (Art. 8)",         MUTED),
    ("2036 📅", "Co ≥26%, Li ≥12%, Ni ≥15%",                          MUTED),
]

ty = Inches(1.95)
for year, req, col in timeline:
    box(s7, Inches(7.1), ty, Inches(5.7), Inches(0.72), fill=CARD, border=col, border_width=1.5)
    txb(s7, year, Inches(7.2), ty + Inches(0.08), Inches(1.2), Inches(0.55),
        size=16, bold=True, color=col)
    txb(s7, req, Inches(8.5), ty + Inches(0.1), Inches(4.2), Inches(0.52),
        size=14, color=TEXT)
    ty += Inches(0.82)

# Bottom stat bar
box(s7, Inches(0.5), Inches(6.55), Inches(12.33), Inches(0.65),
    fill=RGBColor(0x05, 0x14, 0x20), border=ACCENT, border_width=1.5)
txb(s7, "102 data points  ·  4 compliance horizons  ·  3 chemistry types  ·  13 data groups",
    Inches(0.7), Inches(6.63), Inches(12), Inches(0.5),
    size=19, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — KEY FEATURES
# ══════════════════════════════════════════════════════════════════════════════
s8 = new_slide()
slide_label(s8, "FEATURES")
txb(s8, "What Makes It Work",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s8, Inches(1.3))

features = [
    ("🔬", "Level 2 Physical Sensor Verification",
     "Software validation = Level 1. Level 2 means declared sensor values\n(voltage, resistance, SoC, temperature) are cross-validated against\nactual BMS readings from the physical battery. No competitor offers this.",
     RGBColor(0xc0, 0x84, 0xfc)),
    ("🔐", "Trust Score That Can't Be Gamed",
     "Math-enforced ceiling: max trust = (real_data% × 0.5) + 50\nA supplier with 0% verified data cannot score above 50/100.",
     ACCENT),
    ("📊", "Role-Based Access — 4 Levels",
     "Consumer: health + QR certificate\nTechnician: sensor data + disassembly\nCompany: supply chain risk + compliance\nRegulator: all 102 points, unredacted.",
     AMBER),
    ("⚡", "Live ERP Sync (Odoo)",
     "BLOCK decision → writes to ERP product record in real-time\nNo manual entry. Procurement trigger is automatic.",
     RED),
]

fw2 = Inches(5.9)
fh2 = Inches(2.55)
positions = [
    (Inches(0.4), Inches(1.45)),
    (Inches(6.95), Inches(1.45)),
    (Inches(0.4),  Inches(4.2)),
    (Inches(6.95), Inches(4.2)),
]

for (fx, fy), (icon, title, desc, col) in zip(positions, features):
    box(s8, fx, fy, fw2, fh2, fill=CARD, border=col, border_width=2)
    txb(s8, icon,  fx + Inches(0.2), fy + Inches(0.18), Inches(0.7), Inches(0.7), size=28)
    txb(s8, title, fx + Inches(0.95), fy + Inches(0.18), fw2 - Inches(1.1), Inches(0.6),
        size=17, bold=True, color=col)
    txb(s8, desc,  fx + Inches(0.2), fy + Inches(0.9), fw2 - Inches(0.4), Inches(1.5),
        size=14, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — DEMO SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════════
s9 = new_slide()
slide_label(s9, "LIVE DEMO")
txb(s9, "Live Demo — 3 Batteries, Real Decisions",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=34, bold=True, color=TEXT)
hline(s9, Inches(1.3))

# BLOCK alert banner
box(s9, Inches(0.5), Inches(1.45), Inches(12.33), Inches(0.65),
    fill=RGBColor(0x2a, 0x06, 0x06), border=RED, border_width=2)
txb(s9, "⚠️  1 SUPPLIER BLOCKED — Immediate procurement action required",
    Inches(0.7), Inches(1.53), Inches(12), Inches(0.5),
    size=18, bold=True, color=RED, align=PP_ALIGN.CENTER)

# Risk matrix
matrix_y = Inches(2.3)
box(s9, Inches(0.5), matrix_y, Inches(12.33), Inches(0.48),
    fill=BORDER, border=BORDER, border_width=0)
for label, cx in zip(["Supplier", "Trust Score", "Decision", "2024 Status", "Auth Checks"],
                      [0.6, 3.5, 5.8, 8.1, 10.5]):
    txb(s9, label, Inches(cx), matrix_y + Inches(0.07), Inches(2.2), Inches(0.38),
        size=14, bold=True, color=TEXT)

matrix_rows = [
    ("Volvo Cars (NMC811)",      "71.5 / 100", "✅ APPROVE",  "COMPLIANT",     "8/8 ✅", ACCENT),
    ("BMW Group (NMC712)",       "65.5 / 100", "🔄 REVIEW",   "COMPLIANT",     "6/8 🔄", AMBER),
    ("Shenzhen Generic (LFP)",   "6.0 / 100",  "🔴 BLOCK",    "AT RISK",       "2/5 ❌", RED),
]

ry2 = matrix_y + Inches(0.5)
for supplier, score, decision, status, auth, col in matrix_rows:
    rh2 = Inches(0.62)
    box(s9, Inches(0.5), ry2, Inches(12.33), rh2, fill=CARD, border=BORDER, border_width=0.5)
    txb(s9, supplier,  Inches(0.6),  ry2 + Inches(0.1), Inches(2.8), Inches(0.45), size=14, color=TEXT)
    txb(s9, score,     Inches(3.5),  ry2 + Inches(0.1), Inches(2.2), Inches(0.45), size=15, bold=True, color=col)
    txb(s9, decision,  Inches(5.8),  ry2 + Inches(0.1), Inches(2.2), Inches(0.45), size=14, bold=True, color=col)
    txb(s9, status,    Inches(8.1),  ry2 + Inches(0.1), Inches(2.2), Inches(0.45), size=14, color=MUTED)
    txb(s9, auth,      Inches(10.5), ry2 + Inches(0.1), Inches(1.8), Inches(0.45), size=14, color=col)
    ry2 += rh2

hline(s9, Inches(5.3))
demo_points = [
    "Drill down → Trust Score gauge → Sync to Odoo ERP → toast confirmation",
    "Government Portal → EU compliance map → violation chart by EU Article",
    "Battery Passport → Consumer → QR Certificate (Level 2 Physical Verified badge)",
]
dy = Inches(5.45)
for pt in demo_points:
    txb(s9, f"→  {pt}", Inches(0.6), dy, Inches(12.2), Inches(0.5), size=15, color=MUTED)
    dy += Inches(0.5)

txb(s9, "[ Replace this area with a live screenshot of the Enterprise Dashboard ]",
    Inches(0.5), Inches(7.1), Inches(12.33), Inches(0.35),
    size=12, color=BORDER, italic=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — TECH DEPTH
# ══════════════════════════════════════════════════════════════════════════════
s10 = new_slide()
slide_label(s10, "TECH")
txb(s10, "Built to Be Real",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s10, Inches(1.3))

tech_cols = [
    ("Stack", [
        "Python 3.11 + Streamlit 1.32",
        "Plotly 5.18 (charts + EU map)",
        "xmlrpc.client — stdlib only",
        "qrcode[pil] (QR certificates)",
        "python-pptx (this deck!)",
    ], ACCENT),
    ("Data Layer", [
        "3 manufacturer JSON files",
        "EU DPP format (102 data points)",
        "Chemistry benchmarks: NMC811, NMC712, LFP",
        "EU compliance thresholds per year",
        "Live Odoo: vericell.odoo.com",
    ], RGBColor(0x60, 0xa5, 0xfa)),
    ("Smart Logic", [
        "@st.cache_data — engine runs once",
        "Deterministic + fully auditable",
        "ERP adapter pattern (swap Odoo→SAP = config change)",
        "Trust ceiling formula — ungameable",
        "Cross-field math — 8 validation checks",
    ], AMBER),
]

cw3 = Inches(3.9)
ch3 = Inches(5.3)
cx3_start = Inches(0.4)
cy3 = Inches(1.5)
cgap3 = Inches(0.27)

for i, (title, points, col) in enumerate(tech_cols):
    cx3 = cx3_start + i * (cw3 + cgap3)
    box(s10, cx3, cy3, cw3, ch3, fill=CARD, border=col, border_width=2)
    title_bar = box(s10, cx3, cy3, cw3, Inches(0.55), fill=col, border=col, border_width=0)
    txb(s10, title, cx3 + Inches(0.15), cy3 + Inches(0.08), cw3, Inches(0.42),
        size=17, bold=True, color=BG)
    py3 = cy3 + Inches(0.7)
    for pt in points:
        txb(s10, f"• {pt}", cx3 + Inches(0.15), py3, cw3 - Inches(0.3), Inches(0.75),
            size=14, color=TEXT)
        py3 += Inches(0.82)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — WHY THIS WINS
# ══════════════════════════════════════════════════════════════════════════════
s11 = new_slide()
slide_label(s11, "ADVANTAGE")
txb(s11, "Our Unfair Advantage",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s11, Inches(1.3))

advantages = [
    ("🔬  Physical Sensor Verification — no competitor has this",
     "Every other platform validates documents. We validate the physical battery. BMS readings vs declared values. Second-life operators can finally trust the SoH.",
     RGBColor(0xc0, 0x84, 0xfc)),
    ("Only platform that outputs ERP actions",
     "Not dashboards — actual procurement triggers. BLOCK → Odoo writes in real-time.",
     ACCENT),
    ("ERP-agnostic architecture",
     "Same JSON output works with Odoo, SAP, weclapp, Dynamics. Adapter swap = config change.",
     RGBColor(0x60, 0xa5, 0xfa)),
    ("Math-enforced trust scoring",
     "Score formula cannot be gamed. 0% verified data = max score of 50/100. Period.",
     AMBER),
    ("Private trust layer — like AVILOO for used EVs",
     "No regulatory approval needed to operate. We issue the badge. Buyers pay more for certified batteries.",
     RED),
]

ay = Inches(1.5)
for title, desc, col in advantages:
    box(s11, Inches(0.5), ay, Inches(12.33), Inches(0.88),
        fill=CARD, border=col, border_width=2)
    box(s11, Inches(0.5), ay, Inches(0.12), Inches(0.88),
        fill=col, border=col, border_width=0)
    txb(s11, title, Inches(0.8), ay + Inches(0.06), Inches(5.5), Inches(0.38),
        size=17, bold=True, color=col)
    txb(s11, desc,  Inches(6.5), ay + Inches(0.06), Inches(6.2), Inches(0.76),
        size=14, color=MUTED)
    ay += Inches(0.98)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — IMPACT
# ══════════════════════════════════════════════════════════════════════════════
s12 = new_slide()
slide_label(s12, "IMPACT")
txb(s12, "What Changes",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s12, Inches(1.3))

impact_cols = [
    ("🏢  For Companies", [
        "Automated supplier risk scoring",
        "ERP blocks bad batteries before procurement",
        "Compliance evidence ready for audits",
        "Real-time decision — no manual review",
    ], AMBER),
    ("🏛  For Regulators", [
        "Real-time violation tracking dashboard",
        "EU compliance map by country",
        "Downloadable audit reports per battery",
        "Cross-field fraud detection — automated",
    ], RGBColor(0x60, 0xa5, 0xfa)),
    ("🌍  For the Market", [
        "More batteries reused, not destroyed",
        "€3B+ inefficiency reduced",
        "Trusted second-life battery economy",
        "EU 2027 compliance — ready now",
    ], ACCENT),
]

iw = Inches(3.9)
ih = Inches(4.8)
ix_start = Inches(0.4)
iy = Inches(1.6)
igap = Inches(0.27)

for i, (title, points, col) in enumerate(impact_cols):
    ix = ix_start + i * (iw + igap)
    box(s12, ix, iy, iw, ih, fill=CARD, border=col, border_width=2)
    title_bar = box(s12, ix, iy, iw, Inches(0.6), fill=col, border=col, border_width=0)
    txb(s12, title, ix + Inches(0.15), iy + Inches(0.08), iw, Inches(0.48),
        size=17, bold=True, color=BG)
    py12 = iy + Inches(0.75)
    for pt in points:
        txb(s12, f"• {pt}", ix + Inches(0.18), py12, iw - Inches(0.35), Inches(0.75),
            size=15, color=TEXT)
        py12 += Inches(0.88)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — FUTURE / SCALE
# ══════════════════════════════════════════════════════════════════════════════
s13 = new_slide()
slide_label(s13, "ROADMAP")
txb(s13, "Where This Goes",
    Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.8),
    size=36, bold=True, color=TEXT)
hline(s13, Inches(1.3))

phases = [
    ("NOW", "Phase 1",
     ["Trust Engine + Odoo ERP", "3 manufacturer demo", "4-role access system", "EU 2023/1542 compliance"],
     ACCENT),
    ("6 months", "Phase 2",
     ["API upload portal for manufacturers", "SAP / weclapp integrations", "Level 3: TÜV co-signed certs", "Onboard first paying customer"],
     AMBER),
    ("12 months", "Phase 3",
     ["Insurance & leasing data feed", "White-label engine for ERP vendors", "Solar + industrial battery expansion", "Pan-EU rollout"],
     RGBColor(0x60, 0xa5, 0xfa)),
]

pw = Inches(3.7)
ph = Inches(3.5)
px_start = Inches(0.45)
py13 = Inches(1.5)
pgap = Inches(0.27)

for i, (when, phase, points, col) in enumerate(phases):
    px = px_start + i * (pw + pgap)
    box(s13, px, py13, pw, ph, fill=CARD, border=col, border_width=2)
    box(s13, px, py13, pw, Inches(0.95), fill=col, border=col, border_width=0)
    txb(s13, when,  px + Inches(0.15), py13 + Inches(0.06), pw, Inches(0.42),
        size=20, bold=True, color=BG)
    txb(s13, phase, px + Inches(0.15), py13 + Inches(0.5),  pw, Inches(0.38),
        size=13, bold=False, color=BG)
    ppy = py13 + Inches(1.1)
    for pt in points:
        txb(s13, f"• {pt}", px + Inches(0.15), ppy, pw - Inches(0.25), Inches(0.58),
            size=14, color=TEXT)
        ppy += Inches(0.57)

# Revenue box
box(s13, Inches(0.45), Inches(5.2), Inches(12.33), Inches(1.85),
    fill=RGBColor(0x05, 0x14, 0x20), border=ACCENT, border_width=1.5)
txb(s13, "Revenue Model", Inches(0.65), Inches(5.3), Inches(3), Inches(0.45),
    size=16, bold=True, color=ACCENT)
rev_items = [
    ("€30–80 / battery", "per validation (second-life operators)"),
    ("€1.5K–5K / month", "SaaS license (fleet operators, recyclers)"),
    ("€50K–500K / year", "enterprise + insurance data contracts"),
]
rx = Inches(0.65)
for amt, desc in rev_items:
    txb(s13, amt,  rx, Inches(5.8), Inches(2.2), Inches(0.5), size=16, bold=True, color=AMBER)
    txb(s13, desc, rx, Inches(6.3), Inches(2.2), Inches(0.55), size=13, color=MUTED)
    rx += Inches(4.1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — CLOSE
# ══════════════════════════════════════════════════════════════════════════════
s14 = new_slide()

# 3 muted problem lines
txb(s14, "Manufacturers claim.",
    Inches(0.8), Inches(0.9), Inches(11.7), Inches(0.75),
    size=36, bold=False, color=MUTED, align=PP_ALIGN.CENTER)
txb(s14, "Regulators demand proof.",
    Inches(0.8), Inches(1.7), Inches(11.7), Inches(0.75),
    size=36, bold=False, color=MUTED, align=PP_ALIGN.CENTER)
txb(s14, "Buyers need certainty.",
    Inches(0.8), Inches(2.5), Inches(11.7), Inches(0.75),
    size=36, bold=False, color=MUTED, align=PP_ALIGN.CENTER)

# Green bold statement — the key differentiator
txb(s14, "We provide it — from algorithm to physical sensor.",
    Inches(0.5), Inches(3.45), Inches(12.3), Inches(0.95),
    size=40, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

# Thin divider
hline(s14, Inches(4.6), color=BORDER)

# Closing statement
txb(s14, "We built the layer that connects them.",
    Inches(0.8), Inches(4.85), Inches(11.7), Inches(0.85),
    size=32, bold=True, color=TEXT, align=PP_ALIGN.CENTER)

# Tagline — single line, small
txb(s14, "TrustLayer VeriCell  —  Trust the battery. Not just the paperwork.",
    Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.6),
    size=17, bold=False, color=MUTED, align=PP_ALIGN.CENTER)


# ─── Save ─────────────────────────────────────────────────────────────────────
output_path = "VeriCell_Pitch_Deck.pptx"
prs.save(output_path)
print(f"✅ Saved: {output_path}  ({prs.slides.__len__()} slides)")
print("   Open in PowerPoint / Google Slides / Keynote → File → Export as PDF")
print("   Tip: On Slide 9 (Demo), add a screenshot of the Enterprise Dashboard.")
