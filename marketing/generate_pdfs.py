#!/usr/bin/env python3
"""Generate print-ready PDFs for DataCore Hackathon AMAD materials."""

import os
from reportlab.lib.units import mm
from reportlab.lib.colors import CMYKColor
from reportlab.pdfgen import canvas

# ── Brand Colors (DeviceCMYK — print-safe) ───────────────────────────────────
NAVY        = CMYKColor(0.48, 0.53, 0.00, 0.77)   # #1E1B3A
NAVY_LITE   = CMYKColor(0.40, 0.45, 0.00, 0.70)   # diagonal overlay (subtle lighter)
ORANGE      = CMYKColor(0.00, 0.61, 0.81, 0.09)   # #E85B2C
PURPLE      = CMYKColor(0.21, 0.27, 0.00, 0.35)   # #8378A5
CREAM       = CMYKColor(0.00, 0.02, 0.07, 0.04)   # #F5EFE4
WHITE       = CMYKColor(0.00, 0.00, 0.00, 0.00)
DIM_CREAM   = CMYKColor(0.00, 0.02, 0.07, 0.65)   # divider lines

BLEED = 3 * mm
BOLD   = "Helvetica-Bold"
NORMAL = "Helvetica"


# ── Helpers ───────────────────────────────────────────────────────────────────

def fill_background(c, w, h):
    """Navy fill + subtle diagonal overlay stripes."""
    c.setFillColor(NAVY)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColor(NAVY_LITE)
    step = 80 * mm
    c.setLineWidth(30)
    for i in range(-4, int(h / step) + 6):
        y0 = i * step
        c.line(0, y0, w, y0 + w * 0.22)


def wrap(c, text, x, y, width, font, size, color, leading_mult=1.5):
    """Word-wrap text block; return y after last baseline."""
    if not text.strip():
        return y
    c.setFillColor(color)
    c.setFont(font, size)
    lead = size * leading_mult
    words = text.split()
    line = []
    for word in words:
        trial = " ".join(line + [word])
        if c.stringWidth(trial, font, size) <= width:
            line.append(word)
        else:
            if line:
                c.drawString(x, y, " ".join(line))
                y -= lead
            line = [word]
    if line:
        c.drawString(x, y, " ".join(line))
        y -= lead
    return y


def hline(c, x1, y, x2, color=DIM_CREAM, lw=0.8):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)


def vline(c, x, y1, y2, color=DIM_CREAM, lw=0.4):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x, y1, x, y2)


def section_header(c, label, x, y, bar_w=25*mm):
    """Orange heading + short orange underbar. Returns y after bar."""
    c.setFillColor(ORANGE)
    c.setFont(BOLD, 16)
    c.drawString(x, y, label)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(1)
    c.line(x, y - 5, x + bar_w, y - 5)
    return y - 22


# ─────────────────────────────────────────────────────────────────────────────
# FILE 1 — ROLL-UP BANNER  850 mm × 2000 mm
# ─────────────────────────────────────────────────────────────────────────────

def generate_banner(out_path):
    LW = 850 * mm
    LH = 2000 * mm
    PW = LW + 2 * BLEED
    PH = LH + 2 * BLEED

    c = canvas.Canvas(out_path, pagesize=(PW, PH))
    c.setTitle("DataCore Roll-Up Banner 85×200cm")

    fill_background(c, PW, PH)

    # Live-area anchors
    LX   = BLEED           # left edge of live area
    BY   = BLEED           # bottom edge of live area
    ML   = LX + 45 * mm   # main left text margin
    TW   = LW - 90 * mm   # main text width
    R    = LX + LW - 40 * mm  # right text anchor

    # Section boundaries (y from page bottom)
    FOOT_H  = 300 * mm
    BENE_H  = 1100 * mm
    HERO_H  = 300 * mm
    HEAD_H  = 300 * mm  # top section

    FOOT_TOP  = BY + FOOT_H
    BENE_BOT  = FOOT_TOP
    BENE_TOP  = BENE_BOT + BENE_H
    HERO_BOT  = BENE_TOP
    HERO_TOP  = HERO_BOT + HERO_H
    HEAD_BOT  = HERO_TOP
    HEAD_TOP  = HEAD_BOT + HEAD_H

    # ── SECTION 1: HEADER ─────────────────────────────────────────────────────
    DC_BASE = HEAD_TOP - 65 * mm          # "DataCore" baseline

    c.setFillColor(WHITE)
    c.setFont(BOLD, 180)
    c.drawString(ML, DC_BASE - 180, "DataCore")

    c.setFillColor(CREAM)
    c.setFont(NORMAL, 40)
    c.drawString(ML, DC_BASE - 260, "AI-Powered SME Lending Engine")

    c.setFillColor(PURPLE)
    c.setFont(BOLD, 28)
    c.drawRightString(R, HEAD_TOP - 55 * mm, "Hackathon AMAD 2026")

    # ── SECTION 2: HERO SLOGAN ────────────────────────────────────────────────
    HCY = HERO_BOT + HERO_H * 0.54       # vertical center

    c.setFillColor(WHITE)
    c.setFont(BOLD, 140)
    c.drawString(ML, HCY + 85,       "See every business.")
    c.drawString(ML, HCY + 85 - 185, "Fund every future.")

    c.setFillColor(ORANGE)
    c.setFont(BOLD, 48)
    c.drawString(ML, HCY + 85 - 185 - 120,
                 "The lending engine banks have been missing.")

    # Bracket-dividers around benefits
    hline(c, LX + 25*mm, BENE_TOP, LX + LW - 25*mm, DIM_CREAM, 1.5)
    hline(c, LX + 25*mm, BENE_BOT, LX + LW - 25*mm, DIM_CREAM, 1.5)

    # ── SECTION 3: BENEFITS ───────────────────────────────────────────────────
    BENEFITS = [
        ("01", "Lend Like You Know Them",
         "Every SME is judged by how it actually operates — its real revenue, its real "
         "patterns, its real risk — not by the industry label it happens to fall under."),
        ("02", "Every SME, a Data Asset",
         "Each connected business becomes a live, verified view of its actual operations. "
         "Across a portfolio, this becomes a platform — banks can connect their SMEs to "
         "the right suppliers, partners, and opportunities worldwide, opening new revenue "
         "streams that go far beyond loan interest."),
        ("03", "SMEs Grow, Banks Grow With Them",
         "When SMEs get the right funding at the right time, they scale, hire, and expand "
         "— building lasting relationships with the banks that funded them. The healthier "
         "the SME sector becomes, the more the whole banking ecosystem benefits."),
    ]

    block_h = BENE_H / 3   # ≈ 367 mm each

    for idx, (num, headline, explanation) in enumerate(BENEFITS):
        b_bot = BENE_BOT + idx * block_h
        b_top = b_bot + block_h
        b_cy  = b_bot + block_h * 0.50

        if idx > 0:
            hline(c, LX + 25*mm, b_top, LX + LW - 25*mm, DIM_CREAM, 1.0)

        # Number tag
        NUM_X  = ML
        c.setFillColor(ORANGE)
        c.setFont(BOLD, 72)
        c.drawString(NUM_X, b_cy + 55, num)

        # Headline
        HEAD_X = ML + 110 * mm
        c.setFillColor(WHITE)
        c.setFont(BOLD, 90)
        c.drawString(HEAD_X, b_cy + 55, headline)

        # Explanation
        EXP_W = TW - 110 * mm
        wrap(c, explanation, HEAD_X, b_cy - 40, EXP_W, NORMAL, 40, CREAM, 1.45)

    # ── SECTION 4: FOOTER ─────────────────────────────────────────────────────
    F_CY = FOOT_TOP * 0.5 + BY * 0.5    # center of footer

    c.setFillColor(CREAM)
    c.setFont(BOLD, 48)
    c.drawString(ML, F_CY + 28, "Abdullah Ali Alanazi")

    c.setFillColor(PURPLE)
    c.setFont(NORMAL, 32)
    c.drawString(ML, F_CY - 22, "Solo Founder")

    c.setFillColor(ORANGE)
    c.setFont(BOLD, 48)
    c.drawRightString(R, F_CY + 10, "See every business. Fund every future.")

    c.save()
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  BANNER  -> {out_path}  ({size_kb} KB)")
    print(f"           Page: {PW/mm:.1f} mm x {PH/mm:.1f} mm  (incl. 3 mm bleed all sides)")
    print(f"           Live: {LW/mm:.0f} mm x {LH/mm:.0f} mm")


# ─────────────────────────────────────────────────────────────────────────────
# FILE 2 — A4 TRI-FOLD FLYER  297 mm × 210 mm × 2 pages
# ─────────────────────────────────────────────────────────────────────────────

def generate_flyer(out_path):
    LW = 297 * mm
    LH = 210 * mm
    PW = LW + 2 * BLEED
    PH = LH + 2 * BLEED

    PANEL = LW / 3        # 99 mm per panel
    PAD   = 6 * mm
    SAFE  = 5 * mm
    FOLD  = 3 * mm        # clearance at fold lines (no bleed there)

    c = canvas.Canvas(out_path, pagesize=(PW, PH))
    c.setTitle("DataCore Tri-Fold Flyer A4")

    # Panel x-coordinates (live area origin = BLEED)
    X0 = BLEED
    X1 = BLEED + PANEL
    X2 = BLEED + 2 * PANEL
    X3 = BLEED + LW
    BY = BLEED
    TY = BLEED + LH

    def panel_text_bounds(idx):
        """(xl, tw) — left text edge and text width for panel idx 0/1/2."""
        px_l = X0 + idx * PANEL
        px_r = px_l + PANEL
        xl = px_l + (SAFE + PAD if idx == 0 else FOLD + PAD)
        xr = px_r - (SAFE + PAD if idx == 2 else FOLD + PAD)
        return xl, xr - xl

    def panel_center_x(idx):
        return X0 + idx * PANEL + PANEL / 2

    PCY = (BY + TY) / 2   # vertical center of panels

    # ── PAGE 1 OUTSIDE: [A: Contact] | [B: Back] | [C: Front Cover] ──────────
    fill_background(c, PW, PH)
    vline(c, X1, BY, TY, DIM_CREAM, 0.4)
    vline(c, X2, BY, TY, DIM_CREAM, 0.4)

    # PANEL C — Front Cover (rightmost)
    pcx = panel_center_x(2)

    c.setFillColor(WHITE)
    c.setFont(BOLD, 68)
    dw = c.stringWidth("DataCore", BOLD, 68)
    c.drawString(pcx - dw / 2, PCY + 66, "DataCore")

    c.setStrokeColor(ORANGE)
    c.setLineWidth(2.5)
    c.line(pcx - 19*mm, PCY + 44, pcx + 19*mm, PCY + 44)

    c.setFillColor(CREAM)
    c.setFont(BOLD, 21)
    for txt, dy in [("See every business.", 20), ("Fund every future.", -4)]:
        tw2 = c.stringWidth(txt, BOLD, 21)
        c.drawString(pcx - tw2 / 2, PCY + dy, txt)

    c.setFillColor(PURPLE)
    c.setFont(BOLD, 10)
    lbl = "Hackathon AMAD 2026"
    lw = c.stringWidth(lbl, BOLD, 10)
    c.drawString(pcx - lw / 2, BY + SAFE + 3*mm, lbl)

    # PANEL B — Back Cover (center)
    bcx = panel_center_x(1)

    c.setFillColor(ORANGE)
    c.setFont(BOLD, 13)
    h1 = "AI-Powered SME Lending Engine"
    c.drawString(bcx - c.stringWidth(h1, BOLD, 13) / 2, PCY + 9, h1)

    c.setFillColor(CREAM)
    c.setFont(NORMAL, 11)
    h2 = "Live data. Real behavior. Fair decisions."
    c.drawString(bcx - c.stringWidth(h2, NORMAL, 11) / 2, PCY - 9, h2)

    # PANEL A — Contact (leftmost)
    xl, tw = panel_text_bounds(0)
    y = TY - SAFE - PAD - 16

    y = section_header(c, "Get in Touch", xl, y)

    for font, size, color, text in [
        (BOLD,   11, CREAM,  "Abdullah Ali Alanazi"),
        (NORMAL, 10, PURPLE, "Solo Founder — DataCore"),
        (NORMAL,  5, CREAM,  ""),
        (BOLD,   10, CREAM,  "Email:"),
        (NORMAL, 10, CREAM,  "abud2754@gmail.com"),
        (NORMAL,  5, CREAM,  ""),
        (BOLD,   10, CREAM,  "Phone:"),
        (NORMAL, 10, CREAM,  "________________________"),
        (NORMAL,  5, CREAM,  ""),
        (BOLD,   10, CREAM,  "LinkedIn:"),
        (NORMAL, 10, CREAM,  "________________________"),
    ]:
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(xl, y, text)
        y -= size * 1.65

    c.setFillColor(PURPLE)
    c.setFont(NORMAL, 9)
    c.drawString(xl, BY + SAFE + 12, "Prince Sultan University")
    c.drawString(xl, BY + SAFE + 1,  "Riyadh, Saudi Arabia")

    c.showPage()

    # ── PAGE 2 INSIDE: [D: Project] | [E: Benefits] | [F: Future] ────────────
    fill_background(c, PW, PH)
    vline(c, X1, BY, TY, DIM_CREAM, 0.4)
    vline(c, X2, BY, TY, DIM_CREAM, 0.4)

    # PANEL D — The Project
    xl, tw = panel_text_bounds(0)
    y = TY - SAFE - PAD - 16
    y = section_header(c, "The Project", xl, y)

    for para in [
        "Banks want to lend to small and medium businesses, but the tools available today "
        "rely on paperwork that no longer reflects reality by the time it reaches a "
        "decision-maker.",
        "DataCore replaces that paperwork with live data — reading each business's actual "
        "financial behavior in real time — so banks can lend confidently, fairly, and quickly.",
        "The system combines four AI models working together to understand any business, "
        "detect risk instantly, and open lending to markets banks previously couldn't safely reach.",
    ]:
        y = wrap(c, para, xl, y, tw, NORMAL, 11, CREAM, 1.45)
        y -= 8

    # PANEL E — For the Bank
    xl, tw = panel_text_bounds(1)
    y = TY - SAFE - PAD - 16
    y = section_header(c, "For the Bank", xl, y)

    for j, (num, bhead, bexp) in enumerate([
        ("01", "Lend Like You Know Them",
         "Every business judged by its actual behavior, not by a generic label."),
        ("02", "Every SME, a Data Asset",
         "Live transaction streams from every business — an asset that powers smarter "
         "lending, cross-selling, and market intelligence beyond just interest."),
        ("03", "SMEs Grow, Banks Grow With Them",
         "Healthy SMEs build lasting bank relationships — the ecosystem grows together."),
    ]):
        c.setFillColor(PURPLE)
        c.setFont(BOLD, 13)
        c.drawString(xl, y, num)

        c.setFillColor(WHITE)
        c.setFont(BOLD, 12)
        c.drawString(xl + 15, y, bhead)
        y -= 15

        y = wrap(c, bexp, xl, y, tw, NORMAL, 10, CREAM, 1.4)

        if j < 2:
            y -= 6
            hline(c, xl, y + 3, xl + tw, DIM_CREAM, 0.4)
            y -= 8

    # PANEL F — What's Next
    xl, tw = panel_text_bounds(2)
    y = TY - SAFE - PAD - 16
    y = section_header(c, "What's Next", xl, y)

    for is_subhead, text in [
        (False, "DataCore is ready to move from prototype to pilot."),
        (True,  "Next phase (Q3 2026):"),
        (False, "Deploy with one Saudi bank as a decision support layer, running alongside "
                "existing lending workflows."),
        (True,  "Following phase (Q4 2026 – Q1 2027):"),
        (False, "Expand to full portfolio-level monitoring, connect the SME marketplace "
                "layer, file patent with SAIP."),
        (True,  "Long-term (2027+):"),
        (False, "SAMA sandbox approval for automated decisioning, publish academic paper on "
                "the behavioral archetype classification methodology, open pathway for other "
                "Saudi banks to adopt the platform."),
    ]:
        font  = BOLD   if is_subhead else NORMAL
        color = WHITE  if is_subhead else CREAM
        y = wrap(c, text, xl, y, tw, font, 11, color, 1.45)
        y -= (7 if is_subhead else 4)

    c.setFillColor(ORANGE)
    c.setFont(BOLD, 10)
    c.drawString(xl, BY + SAFE + 3*mm, "Built for Vision 2030. Ready for the sector.")

    c.save()
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  FLYER   -> {out_path}  ({size_kb} KB)")
    print(f"           Page: {PW/mm:.1f} mm x {PH/mm:.1f} mm  (incl. 3 mm bleed all sides)")
    print(f"           Live: {LW/mm:.0f} mm x {LH/mm:.0f} mm  |  2 pages")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("marketing", exist_ok=True)
    print("\nGenerating DataCore print materials...\n")
    generate_banner("marketing/DataCore_Banner_85x200cm.pdf")
    generate_flyer("marketing/DataCore_Flyer_A4_Trifold.pdf")
    print("\nSafe-zone check (text >= 5 mm inside bleed edges): enforced via SAFE/FOLD constants.")
    print("CMYK colors: all brand values use DeviceCMYK - no RGB-only pigments.\n")
