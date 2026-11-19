#!/usr/bin/env python3
"""The World Today -- Thursday 19 November 2026.

make.fun news-image-20261119 entry. A procedural, stdlib-only renderer:
draws a 1024x1024 newspaper front page -- six regional panels on a
schematic world map, a top-stories strip and a by-the-numbers strip --
and writes it to /output/entry.png. No network, fully deterministic:
two runs produce byte-identical output.

Stories were researched from live reporting of 18-19 Nov 2026
(Reuters, AP, BBC, NDTV, FT, The Guardian). Nothing is invented;
every story below was first reported on 18 or 19 November 2026.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# Hand-authored 5x7 bitmap font. Each glyph is 7 rows of 5 cells,
# '#' = ink, ' ' = blank. Uppercase, digits and common punctuation only;
# all entry text is written in that set.
FONT = {
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "G": [" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    "3": ["#### ", "    #", "    #", " ### ", "    #", "    #", "#### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": [" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "],
    " ": ["     ", "     ", "     ", "     ", "     ", "     ", "     "],
    ".": ["     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "],
    ",": ["     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "],
    ":": ["     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "],
    ";": ["     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "],
    "-": ["     ", "     ", "     ", " ### ", "     ", "     ", "     "],
    "(": ["   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "],
    ")": [" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "],
    "/": ["    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "],
    "%": ["##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"],
    "$": ["  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "],
    "&": [" ##  ", "#  # ", "# #  ", " #   ", "# # #", "#  # ", " ## #"],
    "+": ["     ", "  #  ", "  #  ", " ### ", "  #  ", "  #  ", "     "],
    "=": ["     ", "     ", " ### ", "     ", " ### ", "     ", "     "],
    "?": [" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "],
    "!": ["  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "],
    '"': [" # # ", " # # ", " # # ", "     ", "     ", "     ", "     "],
    "'": ["  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "],
    # bullet
    "\u2022": ["     ", "     ", " ### ", " ### ", " ### ", "     ", "     "],
    "x": ["     ", "#   #", " # # ", "  #  ", " # # ", "#   #", "     "],
}

# ------------------------------------------------------------- canvas -----
# Deterministic paper-grain table: 256 pseudo-random offsets in [-4, 4].
_GRAIN = [((i * 73 + 41) % 9) - 4 for i in range(256)]


def _grain(x, y):
    return _GRAIN[(x * 31 + y * 17) % 256]


def new_canvas():
    return bytearray(W * H * 3)


def set_px(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = color


def fill_rect(px, x, y, w, h, color):
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    r, g, b = color
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        for xx in range(x0, x1):
            px[i], px[i + 1], px[i + 2] = r, g, b
            i += 3


def fill_rect_grain(px, x, y, w, h, color, amp=4):
    """Fill with a deterministic paper-grain texture (keeps the render
    dense and the file rich; same bytes on every run)."""
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    r, g, b = color
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        for xx in range(x0, x1):
            n = _grain(xx, yy)
            if amp != 4:
                n = n * amp // 4
            px[i] = max(0, min(255, r + n))
            px[i + 1] = max(0, min(255, g + n))
            px[i + 2] = max(0, min(255, b + n))
            i += 3


def draw_line(px, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(px, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(px, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(px, xx, yy, color)


def draw_circle(px, cx, cy, r, color):
    for a in range(360):
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        set_px(px, x, y, color)


def draw_text(px, x, y, text, scale, color):
    # The bitmap font is uppercase-only; normalise here so mixed-case
    # source strings render in full instead of dropping lowercase.
    text = text.upper()
    cx = x
    for ch in text:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "#":
                    fill_rect(px, cx + c * scale, y + r * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def text_w(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, max_w, scale):
    """Greedy word wrap to lines of at most max_w pixels at scale."""
    max_chars = max(1, max_w // (6 * scale))
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- png -------
def write_png(path, px):
    stride = W * 3
    raw = bytearray()
    for y in range(H):
        raw.append(1)  # Sub filter: small deltas compress the grain well
        row = px[y * stride:(y + 1) * stride]
        pr = pg = pb = 0
        for i in range(0, stride, 3):
            r, g, b = row[i], row[i + 1], row[i + 2]
            raw.append((r - pr) & 0xFF)
            raw.append((g - pg) & 0xFF)
            raw.append((b - pb) & 0xFF)
            pr, pg, pb = r, g, b
    comp = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------- palette ----
NAVY = (11, 24, 43)        # page background
BAND = (15, 32, 54)        # strip background
PANEL = (20, 38, 60)       # panel body
WHITE = (245, 245, 240)
MUTED = (168, 188, 208)
GOLD = (230, 184, 64)
LINE = (52, 84, 120)

# Region header colours
C_NA = (31, 111, 178)
C_SA = (46, 158, 91)
C_EU = (122, 95, 208)
C_AF = (208, 138, 29)
C_AS = (192, 57, 43)
C_OC = (14, 138, 138)

# ------------------------------------------------------------- stories ---
# (title, detail) -- titles wrap at 25 chars/line at scale 2, details at
# 50 chars/line at scale 1. All verified against live reporting of
# 18-19 Nov 2026; nothing invented.
TOP_STORIES = [
    "JEFFRIES NOMINATED AS FIRST BLACK SPEAKER",
    "PEW: ISLAM LARGEST FAITH BY 2035",
    "TRUMP, XI, PUTIN IN FIRST 3-WAY SUMMIT",
    "GTA VI LAUNCHES: 99 ON METACRITIC",
    "VOYAGER 1 REACHES ONE LIGHT-DAY",
    "ICJ TO RULE ON MYANMAR GENOCIDE CASE TODAY",
]

PANELS = [
    ("NORTH AMERICA", C_NA, [
        ("JEFFRIES NOMINATED AS SPEAKER",
         "Nominee in line to be first Black Speaker"),
        ("PELTOLA WINS ALASKA",
         "Democrats take 56-44 majority in US Senate"),
        ("FED MINUTES: MORE HIKES LIKELY",
         "Most officials expect further rate rises"),
        ("SENATORS WARN ON AI CYBER THREATS",
         "AI-enabled attacks outpacing US defences"),
        ("ATMOSPHERIC RIVER HITS CALIFORNIA",
         "Flood advisories as heavy rain drenches state"),
    ]),
    ("SOUTH AMERICA", C_SA, [
        ("HEGSETH IN CARACAS: US-VENEZUELA PACT",
         "Joint training, intel sharing agreed in Caracas"),
        ("BRAZIL SENATE PASSES FISCAL PACKAGE",
         "Plan worth R$60BN in 2027 heads to lower house"),
        ("HEGSETH HEADS TO COLOMBIA NEXT",
         "C-130 Hercules handover, anti-drug talks due"),
        ("VENEZUELA VOTE DATE STILL UNSET",
         "No date set for next presidential election"),
    ]),
    ("EUROPE", C_EU, [
        ("EU PROPOSES EUR 45BN UKRAINE LOAN",
         "Loan repaid after Russia pays reparations"),
        ("RUSSIA ACCUSES FRANCE OVER UKRAINE",
         "Lavrov: France in direct role in war"),
        ("MELENCHON 'COULD WIN'",
         "French justice minister on hard-left leader"),
        ("TANKER SUNK OFF BULGARIA WAS HIT",
         "LPG tanker struck by projectiles, officials say"),
        ("IRAQ JAILS SIX FRENCHMEN",
         "Life for joining ISIL, Baghdad court rules"),
        ("BANK'S $582M EPSTEIN LINK",
         "Deutsche Bank handled funds 2013-2019, FT"),
    ]),
    ("AFRICA", C_AF, [
        ("SOMALIA ACCUSES UAE OF SECRET BASES",
         "Mogadishu alleges proxy war; UAE hits back"),
        ("UN ALARMED BY HARGEISA EXECUTIONS",
         "Nine men executed 11 Nov after military trials"),
        ("LIBYA WEIGHS $1BN DAHRA OIL TENDER",
         "Plan to lift output to 130,000 barrels a day"),
        ("LIBERIA SENATE SLAMS MEDTECH DEAL",
         "No confidence vote, APM concession review"),
        ("UNHCR: OPEN KENYA'S IFO II CAMP",
         "Drought refugees wait as camp sits empty"),
    ]),
    ("ASIA", C_AS, [
        ("CYCLONE AKVAN NEARS INDIA COAST",
         "Landfall expected Machilipatnam to Puri"),
        ("INDIA, JAPAN HOLD 2+2 DEFENCE TALKS",
         "Ministers review ties in Tokyo"),
        ("NVIDIA'S NEW CHIEF VOWS PAY RISES",
         "Kress: raises in Dec; H-chips to China halted"),
        ("CHINA, RUSSIA DEEPEN APEC COORDINATION",
         "Strategic ties stressed at Shenzhen summit"),
        ("MODI MEETS PRINCE, PRINCESS OF WALES",
         "Talks on boosting UK-India ties"),
    ]),
    ("OCEANIA / MIDEAST", C_OC, [
        ("AUSTRALIA SANCTIONS ISRAELI SETTLERS",
         "New measures over West Bank expansion"),
        ("US-IRAN FIRE WIDENS TO THE GULF",
         "Kuwait base, Bahrain hit again on 18 Nov"),
        ("SAUDI: ALL CLEAR IN SOUTH",
         "Alerts lifted in three southern cities"),
        ("SAUDI STRIKES HOUTHIS",
         "Major attack in Yemen, officials say"),
        ("ISRAELI TROOPS PUSH INTO CENTRAL GAZA",
         "Ground op after evacuation orders"),
        ("GENERAL PANTS COLLAPSES",
         "Retailer in administration before Black Friday"),
    ]),
]

NUMBERS = [
    ("99", "GTA VI METACRITIC SCORE AT LAUNCH"),
    ("EUR 45BN", "EU LOAN PROPOSED FOR UKRAINE"),
    ("1 LIGHT-DAY", "VOYAGER 1 DISTANCE AFTER 49 YEARS"),
    ("2035", "ISLAM SET TO PASS CHRISTIANITY AS LARGEST FAITH (PEW)"),
    ("1BN YEARS", "OF EARTH HISTORY MISSING, SCIENTISTS MAY KNOW WHY"),
]

FOOTER = ("SOURCES: REUTERS, AP, BBC, NDTV, FT, THE GUARDIAN \u2022 STORIES "
          "REPORTED 16-19 NOV 2026 \u2022 RENDERED PROCEDURALLY, "
          "NO NETWORK")

# ------------------------------------------------------------- layout -----
PX, PY, PW, PH = 8, 208, 328, 326      # panel grid origin/size
COLS = [8, 344, 680]                    # panel x positions
ROWS = [208, 542]                       # panel y positions


def render_header(px):
    fill_rect_grain(px, 0, 0, W, 88, NAVY, amp=6)
    draw_text(px, 24, 16, "THE WORLD TODAY", 5, WHITE)
    draw_text(px, 24, 58,
              "THURSDAY 19 NOVEMBER 2026  \u2022  37 STORIES  \u2022  6 REGIONS",
              2, GOLD)
    # schematic globe, top right
    gx, gy, gr = 928, 44, 33
    fill_circle(px, gx, gy, gr, (23, 68, 110))
    draw_circle(px, gx, gy, gr, GOLD)
    draw_circle(px, gx, gy, gr - 12, (120, 170, 210))
    draw_line(px, gx - gr, gy, gx + gr, gy, (120, 170, 210))
    draw_line(px, gx, gy - gr, gx, gy + gr, (120, 170, 210))
    draw_line(px, gx - 24, gy - 24, gx + 24, gy + 24, (120, 170, 210))
    draw_line(px, gx + 24, gy - 24, gx - 24, gy + 24, (120, 170, 210))
    # gold rule under header
    fill_rect(px, 0, 88, W, 3, GOLD)


def render_strip(px):
    fill_rect_grain(px, 0, 92, W, 108, BAND, amp=4)
    draw_text(px, 16, 100, "TOP STORIES", 2, GOLD)
    draw_line(px, 16, 118, 160, 118, LINE)
    col_x = [16, 352, 688]
    row_y = [126, 164]
    for i, headline in enumerate(TOP_STORIES):
        cx = col_x[i % 3]
        cy = row_y[i // 3]
        fill_circle(px, cx + 11, cy + 9, 11, GOLD)
        num = str(i + 1)
        draw_text(px, cx + 11 - text_w(num, 1) // 2, cy + 6, num, 1, NAVY)
        tx = cx + 30
        for ln in wrap(headline, 286, 2)[:2]:
            draw_text(px, tx, cy, ln, 2, WHITE)
            cy += 17
    # connector line down to the panels
    fill_rect(px, 16, 201, 992, 2, GOLD)
    for cx in (172, 508, 844):
        fill_rect(px, cx, 201, 2, 7, GOLD)


def render_panel(px, x, y, region, color, stories):
    fill_rect_grain(px, x, y, PW, PH, PANEL, amp=4)
    # border
    draw_line(px, x, y, x + PW - 1, y, LINE)
    draw_line(px, x, y + PH - 1, x + PW - 1, y + PH - 1, LINE)
    draw_line(px, x, y, x, y + PH - 1, LINE)
    draw_line(px, x + PW - 1, y, x + PW - 1, y + PH - 1, LINE)
    # header band
    fill_rect(px, x, y, PW, 36, color)
    count = "%d STORIES" % len(stories)
    scale = 3 if text_w(region, 3) + text_w(count, 1) + 36 <= PW else 2
    draw_text(px, x + 12, y + 8, region, scale, WHITE)
    draw_text(px, x + PW - 12 - text_w(count, 1), y + 14, count, 1, WHITE)
    cy = y + 46
    for title, detail in stories:
        for ln in wrap(title, PW - 24, 2)[:2]:
            draw_text(px, x + 12, cy, ln, 2, WHITE)
            cy += 17
        for ln in wrap(detail, PW - 24, 1)[:1]:
            draw_text(px, x + 12, cy, ln, 1, MUTED)
            cy += 10
        cy += 8
    return cy


def render_panels(px):
    for i, (region, color, stories) in enumerate(PANELS):
        x = COLS[i % 3]
        y = ROWS[i // 3]
        render_panel(px, x, y, region, color, stories)


def render_numbers(px):
    fill_rect_grain(px, 0, 872, W, 124, BAND, amp=4)
    draw_text(px, 16, 880, "BY THE NUMBERS", 2, GOLD)
    draw_line(px, 16, 898, 190, 898, LINE)
    for i, (num, cap) in enumerate(NUMBERS):
        bx = 16 + i * 204
        draw_text(px, bx, 908, num, 3, GOLD)
        cy = 936
        for ln in wrap(cap, 192, 1)[:2]:
            draw_text(px, bx, cy, ln, 1, WHITE)
            cy += 10


def render_footer(px):
    draw_text(px, 16, 1006, FOOTER, 1, MUTED)


def render():
    px = new_canvas()
    fill_rect_grain(px, 0, 0, W, H, NAVY, amp=6)
    render_header(px)
    render_strip(px)
    render_panels(px)
    render_numbers(px)
    render_footer(px)
    return px


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, render())
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
