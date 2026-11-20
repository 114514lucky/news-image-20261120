# news-image-20261120: draws one 1024x1024 PNG summing up the world news
# of Friday 20 November 2026. Python 3.13, standard library only, no
# network, no clock, no randomness: two runs write identical bytes.
# Layout: cream broadsheet, serif masthead, stat strip, UTC timeline,
# 4 illustrated lead stories, 12 illustrated grid cards, world map,
# 26 numbered briefs, date-check bar. All 42 stories happened or were
# first reported on 20 November 2026; 19 November stories are named
# only in the DATE CHECK box as left out. Single-source claims are
# marked CLAIM. No story is invented.
# Fonts are 2-bit bitmaps rasterized at build time from the system
# DejaVu fonts into fonts.bin (576 glyphs, 20,808 bytes); at run time
# only base64-free binary reading from the standard library is used.
import os, struct, zlib

W, H = 1024, 1024
PAPER = (247, 242, 230)
INK = (26, 26, 26)
RED = (163, 30, 34)
NAVY = (31, 58, 95)
SEA = (31, 58, 95)
LAND = (233, 221, 192)
GOLD = (138, 109, 47)
CREAM2 = (238, 231, 214)
GREY = (110, 110, 105)
DARK = (18, 22, 34)
REG = {"Europe": (47, 93, 138), "Asia": (122, 74, 138),
       "Americas": (163, 46, 46), "Mideast": (138, 109, 47),
       "Africa": (47, 122, 74), "Oceania": (90, 120, 130),
       "Global": (110, 110, 105), "Space": (60, 60, 70)}

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_fonts():
    raw = open(os.path.join(_HERE, "fonts.bin"), "rb").read()
    assert raw[:4] == b"FNT1"
    pos = 4
    nfonts = struct.unpack_from(">I", raw, pos)[0]
    pos += 4
    fonts = {}
    for _ in range(nfonts):
        nlen = raw[pos]
        pos += 1
        name = raw[pos:pos + nlen].decode()
        pos += nlen
        ng = struct.unpack_from(">H", raw, pos)[0]
        pos += 2
        glyphs = {}
        for _ in range(ng):
            cp, adv, w, h, dy = struct.unpack_from(">HBBBb", raw, pos)
            pos += 6
            nbytes = (w * h + 3) // 4
            data = raw[pos:pos + nbytes]
            pos += nbytes
            glyphs[cp] = (adv, w, h, dy, data)
        fonts[name] = glyphs
    return fonts


FONTS = _load_fonts()
buf = bytearray(bytearray(PAPER) * (W * H))


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        k = (y * W + x) * 3
        buf[k], buf[k + 1], buf[k + 2] = c


def rect(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        k = (yy * W + x0) * 3
        for xx in range(x0, x1):
            buf[k], buf[k + 1], buf[k + 2] = c
            k += 3


def hline(x0, x1, y, c):
    for x in range(max(0, x0), min(W, x1 + 1)):
        px(x, y, c)


def vline(x, y0, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        px(x, y, c)


def line(x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                px(xx, yy, c)


def ring(cx, cy, r, c):
    for a in range(360):
        import math
        px(cx + int(r * math.cos(a * 3.14159 / 180)),
           cy + int(r * math.sin(a * 3.14159 / 180)), c)


def poly(points, c):
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[i])), min(W, int(xs[i + 1]) + 1)):
                px(x, y, c)


def _glyph(font, ch):
    g = FONTS[font].get(ord(ch))
    if g is None:
        g = FONTS[font].get(ord("?"))
    return g


def _blit(font, ch, x, base_y, color):
    g = _glyph(font, ch)
    if g is None:
        return 0
    adv, w, h, dy, data = g
    if w == 0 or h == 0:
        return adv
    r0, g0, b0 = color
    top = base_y - dy
    for row in range(h):
        yy = top + row
        if yy < 0 or yy >= H:
            continue
        for col in range(w):
            i = row * w + col
            lv = (data[i >> 2] >> (6 - 2 * (i & 3))) & 3
            if lv == 0:
                continue
            xx = x + col
            if xx < 0 or xx >= W:
                continue
            k = (yy * W + xx) * 3
            if lv == 3:
                buf[k], buf[k + 1], buf[k + 2] = r0, g0, b0
            else:
                buf[k] = (r0 * lv + buf[k] * (3 - lv)) // 3
                buf[k + 1] = (g0 * lv + buf[k + 1] * (3 - lv)) // 3
                buf[k + 2] = (b0 * lv + buf[k + 2] * (3 - lv)) // 3
    return adv


def text(font, s, x, base_y, color):
    cx = x
    for ch in s:
        cx += _blit(font, ch, cx, base_y, color)
    return cx


def text_w(font, s):
    return sum((_glyph(font, ch) or (0, 0, 0, 0, b""))[0] for ch in s)


def centre(font, s, cx, base_y, color):
    text(font, s, cx - text_w(font, s) // 2, base_y, color)


def right(font, s, x, base_y, color):
    text(font, s, x - text_w(font, s), base_y, color)


def wrap(font, s, width):
    out = []
    for part in s.split("|"):
        out.extend(_wrap_part(font, part.strip(), width))
    return out


def _wrap_part(font, s, width):
    lines, cur = [], ""
    for word in s.split(" "):
        t = word if not cur else cur + " " + word
        if text_w(font, t) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            while text_w(font, word) > width and len(word) > 1:
                n = 1
                while n < len(word) and text_w(font, word[:n + 1]) <= width:
                    n += 1
                lines.append(word[:n])
                word = word[n:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _chunk(ctype, data):
    c = struct.pack(">I", len(data)) + ctype + data
    return c + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- layout
M = 22
COLW = 236
GUT = 12
COLX = [M, M + COLW + GUT, M + 2 * (COLW + GUT), M + 3 * (COLW + GUT)]


def caption_bar(x, y, w, label):
    rect(x, y, w, 11, NAVY)
    text("sansb10", label, x + 6, y + 9, (255, 255, 255))


def kicker_row(x, y, num, place, cat, region, tag):
    disc(x + 7, y - 4, 7, REG[region])
    t = str(num)
    tw = text_w("sansb10", t)
    text("sansb10", t, x + 7 - tw // 2, y - 1, (255, 255, 255))
    tx = x + 17
    tw2 = text_w("sansb10", tag)
    bx = x + COLW - tw2 - 8
    label = place + " - " + cat
    if text_w("sansb10", label) > bx - 3 - tx:
        label = place
    text("sansb10", label, tx, y, INK)
    rect(bx - 3, y - 10, tw2 + 6, 12, PAPER)
    for xx in range(bx - 3, bx + tw2 + 3):
        px(xx, y - 10, RED if tag in ("CLAIM", "FORECAST", "ESTIMATE") else GREY)
        px(xx, y + 1, RED if tag in ("CLAIM", "FORECAST", "ESTIMATE") else GREY)
    for yy in range(y - 10, y + 2):
        px(bx - 3, yy, RED if tag in ("CLAIM", "FORECAST", "ESTIMATE") else GREY)
        px(bx + tw2 + 2, yy, RED if tag in ("CLAIM", "FORECAST", "ESTIMATE") else GREY)
    text("sansb10", tag, bx, y, RED if tag in ("CLAIM", "FORECAST", "ESTIMATE") else GREY)


def headline_block(x, y, headline, deck, font, lh, max_lines, deck_lh=14):
    lines = wrap(font, headline, COLW)
    by = y
    for ln in lines[:max_lines]:
        text(font, ln, x, by, INK)
        by += lh
    dy = by + 2
    for ln in wrap("sans12", deck, COLW)[:2]:
        text("sans12", ln, x, dy, INK)
        dy += deck_lh
    return dy


# ---------------------------------------------------------------- data
# (num, place, category, region, tag, headline, deck, caption)
HEROES = [
    (1, "KYIV, UKRAINE", "WAR", "Europe", "CONFIRMED",
     "Russia fires wave|of missiles at Kyiv",
     "Eight killed, 28 hurt; three Dnipro bridges hit. (Reuters)",
     "KYIV - BRIDGES HIT, 8 KILLED"),
    (2, "ODISHA, INDIA", "CYCLONE", "Asia", "CONFIRMED",
     "Cyclone Akvan makes|landfall in eastern India",
     "Storm crosses near Gopalpur; 300,000 evacuated. (IMD, NDTV)",
     "GOPALPUR - LANDFALL 07:30 IST"),
    (3, "ANTALYA, TURKIYE", "CLIMATE", "Europe", "CONFIRMED",
     "COP31 reaches final|day with no deal|in sight",
     "Draft drops fossil-fuel phase-out; talks may overrun. (AFP)",
     "ANTALYA - FINAL DAY"),
    (4, "TOKYO", "MARKETS", "Asia", "CONFIRMED",
     "AI sell-off sinks|Asian shares; Nikkei|dives 4.8%",
     "S&P 500 falls 2%, a fifth straight loss; SoftBank -16%. (CNBC)",
     "TOKYO - NIKKEI -4.8%"),
]

GRID = [
    (5, "BRUSSELS", "EUROPE", "Europe", "FORECAST",
     "UK and EU set to|agree reset deal",
     "Youth mobility, food, carbon. (BBC)",
     "BRUSSELS - RESET TALKS"),
    (6, "MERCURY", "SPACE", "Space", "CONFIRMED",
     "BepiColombo reaches|Mercury after 8 years",
     "Second Mercury orbiter. (Guardian)",
     "MERCURY - ARRIVED"),
    (7, "WORLDWIDE", "GAMES", "Global", "ESTIMATE",
     "GTA VI sales top $2.3bn,|a launch record",
     "Biggest entertainment launch. (BBC)",
     "WORLDWIDE - $2.3BN"),
    (8, "WASHINGTON", "ENERGY", "Americas", "CONFIRMED",
     "US Senate passes energy|permitting overhaul 62-33",
     "Now to the House for a vote. (CNBC)",
     "WASHINGTON - 62-33"),
    (9, "SANTA CLARA", "TECH", "Americas", "CONFIRMED",
     "California opens probe|into Nvidia over China chips",
     "Interim chief Colette Kress. (BBC)",
     "SANTA CLARA - INQUIRY"),
    (10, "SAN SALVADOR", "POLITICS", "Americas", "CONFIRMED",
     "Bukele registers|for a third term",
     "Third six-year term. (Al Jazeera)",
     "SAN SALVADOR - THIRD TERM"),
    (11, "PORT-AU-PRINCE", "CONFLICT", "Americas", "CONFIRMED",
     "Haitian forces kill 34|suspected gang members",
     "Police retake Martissant. (Al Jazeera)",
     "PORT-AU-PRINCE - RAID"),
    (12, "CARACAS", "DIPLOMACY", "Americas", "CONFIRMED",
     "US and Venezuela sign|military cooperation deal",
     "Pact signed in Caracas. (BBC)",
     "CARACAS - PACT"),
    (13, "ULAANBAATAR", "POLITICS", "Asia", "CONFIRMED",
     "Mongolian president|resigns",
     "Vote due within four months. (AP)",
     "ULAANBAATAR - RESIGNS"),
    (14, "BRASILIA", "ECONOMY", "Americas", "CONFIRMED",
     "Brazil's central bank|sells $1bn to curb dollar",
     "Real -18% in a month. (MercoPress)",
     "BRASILIA - $1BN SALE"),
    (15, "TOKYO", "ECONOMY", "Asia", "CONFIRMED",
     "Japan core inflation|quickens to 2.2%",
     "BoJ still seen raising rates. (CNBC)",
     "TOKYO - CPI 2.2%"),
    (16, "NEW YORK", "MARKETS", "Americas", "CONFIRMED",
     "Gold falls 4.2% as|dollar and rates weigh",
     "10-year yield above 5%. (CNBC)",
     "NEW YORK - GOLD -4.2%"),
]

# (num, region, text) — one line each, <= 50 chars
BRIEFS = [
    (17, "Europe", "Poland: Russia violates airspace, Warsaw says"),
    (18, "Europe", "Estonia to shut Russia border for six months"),
    (19, "Americas", "Trump delays Iran war decision to new year"),
    (20, "Americas", "Senate blocks Iran war-powers curb, 51-48"),
    (21, "Mideast", "US war on Iran has cost $48.3bn: Pentagon"),
    (22, "Mideast", "Saudi intercepts Houthi missile, five drones"),
    (23, "Africa", "Sudan: drone strike kills 10 at gold mine"),
    (24, "Africa", "Senegal: dozens missing as migrant boat sinks"),
    (25, "Africa", "Strikes reported on Ethiopia-Eritrea border*"),
    (26, "Oceania", "Fiji, Tonga declare disasters as drought bites"),
    (27, "Asia", "IAEA: North Korea expanding uranium enrichment"),
    (28, "Americas", "Colombia: thousands march against tax plans"),
    (29, "Asia", "Pakistan: 22 militants killed in NW raids"),
    (30, "Asia", "Seoul: ex-PM Han faces retrial in martial-law case"),
    (31, "Europe", "Youth strike planned in 25+ European states"),
    (32, "Africa", "Somalia expels UAE ambassador"),
    (33, "Asia", "Philippines, Chile sign free-trade deal"),
    (34, "Africa", "Zimbabwe: 250,000 landmines destroyed"),
    (35, "Oceania", "Jepchirchir banned 3 years for doping"),
    (36, "Americas", "Trump pardons baseball star Pete Rose"),
    (37, "Americas", "White House fires cyber director"),
    (38, "Global", "UN chief race stalls after eight votes"),
    (39, "Asia", "Bangladesh: violence before Hasina's return"),
    (40, "Mideast", "Iraq orders militia out of Jurf al-Nasr"),
    (41, "Europe", "Denmark ratifies Greenland deal with US"),
    (42, "Global", "IMF: world debt nears 100% of GDP"),
]

STATS = [
    ("300,000+", "evacuated ahead of Akvan"),
    ("8", "killed as Kyiv bridges hit"),
    ("-4.8%", "Nikkei, Friday's close"),
    ("62-33", "Senate passes energy bill"),
    ("$2.3bn", "GTA VI sales, a record"),
    ("2.2%", "Japan core inflation"),
]

TIMELINE = [
    ("02:00 UTC", "Akvan crosses the coast near Gopalpur"),
    ("OVERNIGHT", "Russian missiles hit Kyiv's bridges"),
    ("MORNING", "COP31 enters its final day in Antalya"),
    ("06:00 UTC", "Nikkei closes down 4.8% in Tokyo"),
    ("MIDDAY", "UK and EU meet in Brussels on reset"),
    ("EVENING", "US Senate passes energy bill 62-33"),
]


# ---------------------------------------------------------------- scenes
def scene_kyiv(x, y, w, h):
    rect(x, y, w, h, DARK)
    for i in range(24):
        px(x + (i * 37) % w, y + (i * 13) % 34, (200, 200, 190))
    rect(x, y + h - 26, w, 26, (52, 68, 96))
    rect(x, y + h - 26, w, 2, (120, 140, 170))
    for bx, bw, bh in ((8, 26, 52), (42, 18, 38), (68, 30, 62),
                       (106, 20, 44), (134, 28, 58), (170, 18, 40),
                       (196, 24, 50)):
        rect(x + bx, y + h - 26 - bh, bw, bh, (24, 28, 44))
        for wy in range(0, bh - 6, 10):
            for wx in range(4, bw - 4, 8):
                px(x + bx + wx, y + h - 26 - bh + wy + 4, (240, 180, 60))
    for k in range(3):
        bx = x + 30 + k * 78
        line(bx, y + h - 26, bx + 46, y + h - 52, (150, 160, 180))
        line(bx + 46, y + h - 52, bx + 92, y + h - 26, (150, 160, 180))
        for j in range(4):
            vline(bx + 12 + j * 20, y + h - 50, y + h - 26, (120, 130, 150))
    line(x + 12, y + 14, x + 96, y + 62, (255, 120, 40))
    line(x + 150, y + 8, x + 210, y + 58, (255, 120, 40))
    disc(x + 96, y + 62, 5, (255, 170, 40))
    disc(x + 210, y + 58, 5, (255, 170, 40))
    poly([(x + 52, y + h - 26), (x + 58, y + h - 44), (x + 64, y + h - 26)],
         (255, 140, 30))
    poly([(x + 158, y + h - 26), (x + 164, y + h - 40), (x + 170, y + h - 26)],
         (255, 140, 30))


def scene_akvan(x, y, w, h):
    rect(x, y, w, h, (64, 120, 158))
    poly([(x, y), (x + 74, y), (x + 58, y + 44), (x, y + 58)], (214, 196, 150))
    rect(x, y + h - 18, w, 18, (30, 80, 120))
    cx, cy = x + 138, y + 52
    for r in (10, 20, 30, 40):
        import math
        for a in range(0, 300, 4):
            t = a * 3.14159 / 180
            rr = r * (0.55 + 0.45 * a / 300.0)
            px(cx + int(rr * math.cos(t)), cy + int(rr * math.sin(t)),
               (255, 255, 255))
    disc(cx, cy, 5, (163, 30, 34))
    for i in range(14):
        rx = x + 10 + (i * 53) % (w - 20)
        ry = y + 8 + (i * 29) % 26
        line(rx, ry, rx - 3, ry + 7, (200, 220, 235))
    line(x + 74, y + 30, x + 120, y + 48, (163, 30, 34))
    disc(x + 74, y + 30, 3, (163, 30, 34))
    right("sansb10", "BAY OF BENGAL", x + w - 6, y + h - 5, (255, 255, 255))


def scene_cop31(x, y, w, h):
    rect(x, y, w, h, (168, 208, 220))
    rect(x, y + h - 22, w, 22, (120, 160, 120))
    disc(x + 58, y + 48, 30, (64, 120, 158))
    poly([(x + 34, y + 30), (x + 52, y + 26), (x + 62, y + 40),
          (x + 48, y + 58), (x + 36, y + 52)], (90, 160, 90))
    poly([(x + 62, y + 40), (x + 80, y + 34), (x + 86, y + 50),
          (x + 74, y + 66), (x + 62, y + 54)], (90, 160, 90))
    rect(x + 108, y + 14, 14, 62, (240, 240, 235))
    rect(x + 111, y + 14, 8, 62, (163, 30, 34))
    disc(x + 115, y + 78, 9, (163, 30, 34))
    for i, c in enumerate(((31, 58, 95), (200, 200, 190), (163, 30, 34),
                           (47, 122, 74), (122, 74, 138))):
        rect(x + 138 + i * 18, y + 58, 14, 22, c)
        rect(x + 138 + i * 18, y + 58, 14, 3, (255, 255, 255))
    text("sansb10", "ANTALYA", x + 138, y + 94, INK)


def scene_selloff(x, y, w, h):
    rect(x, y, w, h, (16, 18, 28))
    for gy in range(3):
        yy = y + 18 + gy * 26
        for xx in range(x + 8, x + w - 8, 6):
            px(xx, yy, (50, 55, 70))
    pts = [(x + 10, y + 22), (x + 52, y + 34), (x + 92, y + 30),
           (x + 130, y + 52), (x + 168, y + 48), (x + 206, y + 74),
           (x + 226, y + 84)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             (220, 60, 60))
        line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1,
             (220, 60, 60))
    for p in pts:
        disc(p[0], p[1], 2, (255, 120, 90))
    text("sansb10", "NIKKEI -4.8%", x + 10, y + 20, (255, 255, 255))
    text("sansb10", "KOSPI -5.4%", x + 10, y + 40, (255, 120, 90))
    text("sansb10", "S&P -2.0%", x + 10, y + 60, (255, 120, 90))


HERO_SCENES = [scene_kyiv, scene_akvan, scene_cop31, scene_selloff]


def scene_flags(x, y, w, h):
    rect(x, y, w, h, (214, 196, 150))
    rect(x + 14, y + 6, 96, 32, (0, 51, 153))
    for i in range(12):
        import math
        a = i * 30 * 3.14159 / 180
        px(x + 62 + int(11 * math.cos(a)), y + 22 + int(9 * math.sin(a)),
           (255, 210, 0))
    rect(x + 126, y + 6, 96, 32, (200, 16, 46))
    rect(x + 126, y + 18, 96, 8, (255, 255, 255))
    rect(x + 166, y + 6, 8, 32, (255, 255, 255))
    rect(x + 14, y + 6, 96, 4, (255, 255, 255))
    rect(x + 126, y + 6, 96, 4, (255, 255, 255))


def scene_mercury(x, y, w, h):
    rect(x, y, w, h, (10, 10, 18))
    for i in range(20):
        px(x + (i * 41) % w, y + (i * 17) % 20, (220, 220, 210))
    disc(x + 170, y + 22, 16, (170, 160, 150))
    disc(x + 164, y + 17, 3, (130, 120, 110))
    disc(x + 176, y + 26, 4, (130, 120, 110))
    disc(x + 168, y + 30, 2, (130, 120, 110))
    rect(x + 40, y + 16, 18, 12, (200, 200, 190))
    rect(x + 22, y + 20, 18, 4, (90, 120, 200))
    rect(x + 58, y + 20, 18, 4, (90, 120, 200))
    line(x + 76, y + 22, x + 150, y + 22, (220, 220, 210))


def scene_gta(x, y, w, h):
    rect(x, y, w, h, (70, 40, 110))
    disc(x + 200, y + 10, 7, (255, 220, 120))
    for bx, bw, bh in ((10, 22, 26), (38, 16, 18), (60, 26, 32),
                       (92, 18, 22), (116, 24, 30)):
        rect(x + bx, y + h - bh, bw, bh, (30, 24, 52))
        px(x + bx + 4, y + h - bh + 4, (255, 200, 80))
    rect(x + 150, y + 24, 66, 14, (240, 240, 235))
    disc(x + 158, y + 31, 3, (70, 40, 110))
    disc(x + 168, y + 31, 3, (70, 40, 110))
    disc(x + 204, y + 31, 3, (163, 30, 34))
    disc(x + 194, y + 31, 3, (47, 93, 138))


def scene_capitol(x, y, w, h):
    rect(x, y, w, h, (214, 196, 150))
    rect(x, y + h - 8, w, 8, (120, 140, 90))
    for i in range(6):
        rect(x + 62 + i * 20, y + 18, 10, 20, (250, 248, 240))
    rect(x + 52, y + 14, 132, 4, (250, 248, 240))
    poly([(x + 88, y + 14), (x + 118, y - 2), (x + 148, y + 14)],
         (250, 248, 240))
    disc(x + 118, y + 2, 5, (250, 248, 240))
    rect(x + 20, y + 28, 24, 10, (250, 248, 240))
    rect(x + 192, y + 28, 24, 10, (250, 248, 240))


def scene_chip(x, y, w, h):
    rect(x, y, w, h, (16, 20, 26))
    rect(x + 96, y + 8, 44, 28, (40, 120, 60))
    rect(x + 106, y + 16, 24, 12, (20, 60, 30))
    for i in range(5):
        vline(x + 100 + i * 9, y + 4, y + 8, (120, 200, 140))
        vline(x + 100 + i * 9, y + 36, y + 40, (120, 200, 140))
        hline(x + 92, x + 96, y + 12 + i * 5, (120, 200, 140))
        hline(x + 140, x + 144, y + 12 + i * 5, (120, 200, 140))
    for i in range(12):
        import math
        a = i * 30 * 3.14159 / 180
        px(x + 40 + int(14 * math.cos(a)), y + 22 + int(14 * math.sin(a)),
           (200, 200, 190))
    line(x + 40, y + 22, x + 58, y + 38, (200, 200, 190))
    disc(x + 58, y + 38, 3, (200, 200, 190))


def scene_ballot(x, y, w, h):
    rect(x, y, w, h, (200, 210, 220))
    rect(x + 88, y + 16, 60, 22, (163, 30, 34))
    rect(x + 108, y + 12, 20, 4, (26, 26, 26))
    poly([(x + 98, y + 24), (x + 108, y + 32), (x + 126, y + 18)],
         (255, 255, 255))
    line(x + 40, y + 6, x + 40, y + 38, (26, 26, 26))
    line(x + 20, y + 38, x + 70, y + 38, (26, 26, 26))
    rect(x + 170, y + 10, 40, 26, (250, 248, 240))
    line(x + 176, y + 23, x + 184, y + 31, (163, 30, 34))
    line(x + 184, y + 31, x + 202, y + 15, (163, 30, 34))


def scene_street(x, y, w, h):
    rect(x, y, w, h, (190, 180, 160))
    rect(x + 10, y + 6, 60, 32, (150, 120, 90))
    rect(x + 78, y + 12, 54, 26, (170, 140, 110))
    rect(x + 140, y + 4, 70, 34, (130, 105, 80))
    for wx in range(4):
        rect(x + 18 + wx * 14, y + 14, 8, 10, (60, 50, 40))
    for i in range(5):
        rect(x + 30 + i * 36, y + 32, 30, 6, (220, 220, 210))
        rect(x + 30 + i * 36, y + 32, 30, 2, (163, 30, 34))


def scene_handshake(x, y, w, h):
    rect(x, y, w, h, (214, 196, 150))
    rect(x + 16, y + 8, 90, 28, (0, 51, 153))
    rect(x + 16, y + 18, 90, 8, (255, 255, 255))
    rect(x + 130, y + 8, 90, 28, (255, 204, 0))
    rect(x + 130, y + 8, 90, 9, (0, 51, 153))
    rect(x + 130, y + 27, 90, 9, (200, 16, 46))
    disc(x + 118, y + 22, 8, (255, 255, 255))
    disc(x + 118, y + 22, 5, (163, 30, 34))


def scene_parliament(x, y, w, h):
    rect(x, y, w, h, (168, 200, 220))
    rect(x, y + h - 10, w, 10, (90, 140, 90))
    for i in range(5):
        rect(x + 66 + i * 20, y + 18, 10, 20, (240, 235, 220))
    rect(x + 56, y + 14, 124, 4, (240, 235, 220))
    poly([(x + 92, y + 14), (x + 118, y + 2), (x + 144, y + 14)],
         (200, 60, 60))
    rect(x + 20, y + 26, 26, 12, (240, 235, 220))
    rect(x + 190, y + 26, 26, 12, (240, 235, 220))


def scene_real(x, y, w, h):
    rect(x, y, w, h, (240, 240, 235))
    for i, bh in enumerate((12, 18, 14, 24, 20, 30)):
        rect(x + 20 + i * 30, y + h - 6 - bh, 20, bh, (47, 122, 74))
    pts = [(x + 14, y + 10), (x + 60, y + 14), (x + 110, y + 12),
           (x + 160, y + 24), (x + 210, y + 30)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             (163, 30, 34))
    text("sansb10", "R$", x + 196, y + 12, (163, 30, 34))


def scene_tags(x, y, w, h):
    rect(x, y, w, h, (240, 240, 235))
    for i in range(3):
        tx = x + 24 + i * 68
        poly([(tx, y + 8), (tx + 44, y + 8), (tx + 44, y + 30),
              (tx + 34, y + 38), (tx, y + 30)], (255, 255, 255))
        line(tx + 22, y + 8, tx + 22, y + 38, (163, 30, 34))
        disc(tx + 8, y + 18, 2, (163, 30, 34))
        line(tx + 52, y + 10, tx + 66, y + 4, (163, 30, 34))
    line(x + 24, y + 40, x + 212, y + 40, (163, 30, 34))


def scene_gold(x, y, w, h):
    rect(x, y, w, h, (24, 24, 34))
    for i in range(3):
        rect(x + 30 + i * 34, y + 26, 28, 12, (200, 160, 40))
        rect(x + 30 + i * 34, y + 26, 28, 3, (240, 210, 90))
    rect(x + 47, y + 14, 28, 12, (200, 160, 40))
    rect(x + 81, y + 14, 28, 12, (200, 160, 40))
    pts = [(x + 150, y + 10), (x + 175, y + 16), (x + 195, y + 14),
           (x + 220, y + 28)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             (220, 60, 60))
    text("sansb10", "-4.2%", x + 196, y + 40, (255, 120, 90))


GRID_SCENES = [scene_flags, scene_mercury, scene_gta, scene_capitol,
               scene_chip, scene_ballot, scene_street, scene_handshake,
               scene_parliament, scene_real, scene_tags, scene_gold]


# ---------------------------------------------------------------- map
MAPX, MAPY, MAPW, MAPH = M, 792, 300, 128

CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 44), (-75, 35), (-80, 26),
     (-85, 20), (-95, 18), (-105, 22), (-115, 30), (-125, 40), (-125, 50),
     (-140, 60), (-160, 58)],
    [(-80, 10), (-70, 12), (-60, 5), (-50, 0), (-40, -5), (-35, -10),
     (-40, -20), (-48, -28), (-55, -35), (-65, -40), (-70, -50),
     (-73, -40), (-72, -30), (-75, -18), (-80, -5)],
    [(-10, 36), (-5, 44), (0, 48), (5, 55), (10, 58), (18, 60), (25, 65),
     (30, 70), (40, 68), (45, 60), (40, 50), (30, 45), (20, 42), (12, 44),
     (5, 42), (0, 38)],
    [(-18, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (40, 15), (48, 11), (51, 10), (48, 0), (40, -10),
     (35, -20), (30, -30), (20, -35), (15, -30), (12, -18), (8, -2),
     (9, 4), (-8, 5), (-15, 10)],
    [(45, 70), (60, 72), (75, 73), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (160, 55), (145, 45),
     (140, 40), (130, 35), (122, 30), (115, 22), (108, 12), (105, 5),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 10), (75, 8),
     (70, 20), (60, 25), (55, 28), (50, 30), (45, 40), (42, 45),
     (45, 60)],
    [(113, -22), (122, -14), (132, -12), (142, -11), (150, -22),
     (153, -28), (150, -37), (140, -38), (130, -32), (122, -34),
     (114, -30)],
    [(-45, 60), (-30, 68), (-20, 70), (-30, 76), (-55, 76), (-60, 70)],
]

# story num -> (lon, lat); 6 is Mercury (space badge), 7 is worldwide
PINS = {1: (30.5, 50.4), 2: (85.0, 19.3), 3: (30.7, 36.9),
        4: (139.7, 35.7), 5: (4.35, 50.85), 8: (-77.0, 38.9),
        9: (-122.0, 37.35), 10: (-89.2, 13.7), 11: (-72.3, 18.5),
        12: (-66.9, 10.5), 13: (106.9, 47.9), 14: (-47.9, -15.8),
        15: (139.7, 35.7), 16: (-74.0, 40.7)}


def _lonlat(lon, lat):
    return (MAPX + int((lon + 180.0) / 360.0 * MAPW),
            MAPY + int((75.0 - lat) / 130.0 * MAPH))


def draw_map():
    rect(MAPX, MAPY, MAPW, MAPH, SEA)
    for cont in CONTINENTS:
        poly([_lonlat(lon, lat) for lon, lat in cont], LAND)
    rect(MAPX, MAPY + MAPH - 16, MAPW, 16, NAVY)
    text("sansb10", "6 SPACE - MERCURY", MAPX + 6, MAPY + MAPH - 4,
         (255, 255, 255))
    for num, (lon, lat) in PINS.items():
        x, y = _lonlat(lon, lat)
        if num == 15:
            x += 9
            y -= 8
        disc(x, y, 7, RED)
        t = str(num)
        text("sansb10", t, x - text_w("sansb10", t) // 2, y + 3,
             (255, 255, 255))


# ---------------------------------------------------------------- build
def build():
    rect(0, 0, W, H, PAPER)
    text("sansb11", "THE WORLD IN ONE DAY", M, 18, RED)
    right("sansb11", "42 STORIES - 6 CONTINENTS - ALL FROM FRIDAY 20 NOVEMBER 2026",
          W - M, 18, INK)
    text("serif44", "FRIDAY 20 NOVEMBER 2026", M, 72, INK)
    rect(M, 82, W - 2 * M, 2, INK)
    rect(M, 86, W - 2 * M, 1, INK)
    cellw = (W - 2 * M) // 6
    for i, (big, label) in enumerate(STATS):
        cx = M + i * cellw
        if i:
            vline(cx, 94, 126, (200, 192, 172))
        text("serif20", big, cx + 8, 114, RED)
        text("sansb10", label, cx + 8, 127, INK)
    rect(M, 134, 132, 44, RED)
    centre("sansb11", "THE DAY", M + 66, 152, (255, 255, 255))
    centre("sansb11", "IN UTC", M + 66, 167, (255, 255, 255))
    slotw = (W - 2 * M - 132 - 12) // 6
    for i, (lab, desc) in enumerate(TIMELINE):
        sx = M + 132 + 12 + i * slotw
        text("sansb11", lab, sx, 150, RED)
        dy = 164
        for ln in wrap("sans12", desc, slotw - 6)[:2]:
            text("sans12", ln, sx, dy, INK)
            dy += 13
    for i, st in enumerate(HEROES):
        num, place, cat, region, tag, head, deck, cap = st
        x = COLX[i]
        y = 186
        HERO_SCENES[i](x, y, COLW, 96)
        caption_bar(x, y + 96, COLW, cap)
        kicker_row(x, y + 122, num, place, cat, region, tag)
        headline_block(x, y + 144, head, deck, "serif20", 22, 3)
    for r in range(3):
        for c in range(4):
            st = GRID[r * 4 + c]
            num, place, cat, region, tag, head, deck, cap = st
            x = COLX[c]
            y = 420 + r * 116
            GRID_SCENES[r * 4 + c](x, y, COLW, 40)
            caption_bar(x, y + 40, COLW, cap)
            kicker_row(x, y + 64, num, place, cat, region, tag)
            lines = wrap("serif15", head, COLW)
            by = y + 82
            for ln in lines[:2]:
                text("serif15", ln, x, by, INK)
                by += 17
            text("sans12", deck, x, y + 113, INK)
    text("sansb11", "WHERE IT HAPPENED", M, 788, RED)
    text("sansb11", "ALSO ON FRIDAY 20 NOVEMBER - 26 MORE STORIES", 334, 788, RED)
    draw_map()
    text("sansb10", "Pins 1-16: drawn stories (6 Mercury, 7 worldwide).",
         M, 934, INK)
    for i, (num, region, s) in enumerate(BRIEFS):
        col = i // 13
        row = i % 13
        bx = 334 + col * 340
        by = 802 + row * 11
        disc(bx + 6, by - 3, 6, REG[region])
        t = str(num)
        text("sansb10", t, bx + 6 - text_w("sansb10", t) // 2, by, (255, 255, 255))
        text("sans12", s, bx + 16, by, INK)
    rect(M, 944, W - 2 * M, 32, PAPER)
    for xx in range(M, W - M):
        px(xx, 944, RED)
        px(xx, 975, RED)
    for yy in range(944, 976):
        px(M, yy, RED)
        px(W - M - 1, yy, RED)
    rect(M, 944, 86, 32, RED)
    centre("sansb11", "DATE", M + 43, 958, (255, 255, 255))
    centre("sansb11", "CHECK", M + 43, 971, (255, 255, 255))
    dc = ("Left out as Thursday 19 Nov news: Shenzhen summit; ICJ Rohingya "
          "ruling; Anthropic debut; Riyadh tower strike; GTA VI launch "
          "(only its $2.3bn sales figure is new today). Not yet: COP31 final deal.")
    dy = 958
    for ln in wrap("sans12", dc, W - 2 * M - 86 - 24)[:2]:
        text("sans12", ln, M + 86 + 12, dy, INK)
        dy += 13
    text("sans12", "Every story here happened, or was first reported, on Friday "
         "20 November 2026 in at least one time zone. * = single-source claim.",
         M, 992, INK)
    text("sans12", "Sources: Reuters, AP, AFP, BBC, CNBC, NDTV, IMD, Japan "
         "Times, Al Jazeera, MercoPress, and others. Original drawings.",
         M, 1006, GREY)


def main():
    build()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    n = write_png(os.path.join(outdir, "entry.png"))
    print("wrote entry.png", n, "bytes")


if __name__ == "__main__":
    main()




