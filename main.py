import array
import asyncio
import io
import json
import math
import os
import random
import sys
import time
import wave
import flet as ft

try:
    import flet_audio as fta
except Exception:
    fta = None

W, H = 360, 600
BALL = 14
PH = 12
PY = H - 70
BW, BH, GAP = 39, 18, 4
MAXB = 8
NPART = 14
UNLOCK_ALL = False

THEMES = [
    {"nome": "Notte", "g": ("#0b0b2b", "#1f1147"), "bg": "#06061a",
     "paddle": "#eeeeee", "ball": "#ffffff", "glow": "#80ffffff",
     "acc": "#7c4dff", "pc": "#ffffff", "pd": 1, "ps": 1.0,
     "b": {1: "#4fc3f7", 2: "#ffb74d", 3: "#e57373"}},
    {"nome": "Oceano", "g": ("#032b44", "#06607a"), "bg": "#021a2a",
     "paddle": "#e0f7fa", "ball": "#ffffff", "glow": "#80b2ebf2",
     "acc": "#00acc1", "pc": "#b2ebf2", "pd": -1, "ps": 0.8,
     "b": {1: "#80deea", 2: "#4db6ac", 3: "#ffd54f"}},
    {"nome": "Neon", "g": ("#000000", "#2a0040"), "bg": "#000000",
     "paddle": "#39ff14", "ball": "#ffffff", "glow": "#9939ff14",
     "acc": "#ff2bd6", "pc": "#ff2bd6", "pd": 1, "ps": 2.2,
     "b": {1: "#39ff14", 2: "#ff2bd6", 3: "#00e5ff"}},
    {"nome": "Tramonto", "g": ("#2b0a3d", "#b5415a"), "bg": "#1a0626",
     "paddle": "#fff3e0", "ball": "#ffffff", "glow": "#99ffe082",
     "acc": "#ff7043", "pc": "#ffe082", "pd": -1, "ps": 0.6,
     "b": {1: "#ffd54f", 2: "#ff8a65", 3: "#f06292"}},
]
# X = fisso, H = fisso che si muove, M = palle extra, P = bonus, E = esplosivo
SPECIAL = {"X": "#78909c", "H": "#b0bec5", "M": "#ba68c8",
           "P": "#fff176", "E": "#ff7043"}
LABEL = {"X": "", "H": "<>", "M": "+", "P": "?", "E": "*"}
CAPS = {"L": ("#4caf50", "L"), "S": ("#29b6f6", "S"), "V": ("#ef5350", "+1")}

LEVELS = [
    ["11111111", "11P11P11", "11111111"],
    ["11111111", "12222221", "122P2221", "11111111"],
    ["1.1.1.1.", ".2.2.2.2", "1.1M1.1.", ".2.2.2.2", "33333333"],
    ["X......X", "11111111", "1P2222P1", "11111111", "X......X"],
    ["22222222", "2E2222E2", "22222222", "11111111", "1111E111"],
    ["...11...", "..1221..", ".12M221.", "12233221", "3333E333"],
    ["1X1X1X1X", ".1.1.1.1", "22222222", "2P2M2P22", "33333333"],
    ["33333333", "3XXXXXX3", "3M2222M3", "32E22E23", "33333333"],
    ["E3E3E3E3", "33333333", "3P3M3P33", "X3X3X3X3", "22222222", "11111111"],
    ["33333333", "3E3MM3E3", "3P3XX3P3", "32222223", "3XM33MX3", "22222222"],
    ["3P3MM3P3", ".XXXXXXX", "E......E", "XXXXXXX.", "2......2",
     ".XXXXXXX", "3......3", "XXX..XXX", "11111111"],
    # --- nuovi livelli (12-20): blocchi mobili e labirinti ---
    ["33333333", "3E3MM3E3", "22222222", "H.......", "22222222",
     "H.......", "11P11P11"],
    ["3P3MM3P3", "XXXX..XX", "E......E", "XX..XXXX", "2......2",
     "XXXX..XX", "3......3", "XX..XXXX", "11111111"],
    ["X333333X", "X3MPPM3X", "X333333X", "H.......", "22222222",
     "22222222", "1111E111"],
    ["1X1X1X1X", ".2.2.2.2", "1X1X1X1X", ".2.2.2.2", "1X1X1X1X",
     ".2.2.2.2", "33333333"],
    ["33333333", "3......3", "3.XXXX.3", "3.X33X.3", "3.X33X.3",
     "3.XX.X.3", "3......3", "33333333"],
    ["X.X.X.X.", "3.3.3.3.", "X.X.X.X.", "3.3.3.3.", "X.X.X.X.",
     "3.3.3.3.", "H.......", "22222222", "1M1PP1M1"],
    ["XXXXXXX.", "3333333.", "3EMMME3.", ".XXXXXXX", ".3333333",
     ".3PPP3E3", "XXXXXXX.", "H.......", "11111111"],
    ["3X3X3X3X", "3X3X3X3X", "3X3X3X3X", "33333333", "H.......",
     "H.......", "22222222", "2E2EE2E2", "11111111"],
    # FINALE: varchi stretti ai lati e blocco mobile
    ["33333333", "XXXXXXX.", "3......3", ".XXXXXXX", "3......3",
     "XXXX.XXX", "3......3", "XXX.XXXX", "H......."],
]


def save_path():
    d = os.environ.get("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
    return os.path.join(d, "arkanoid_save.json")


def load_save():
    try:
        with open(save_path()) as f:
            return json.load(f)
    except Exception:
        return {}


def write_save(d):
    try:
        os.makedirs(os.path.dirname(save_path()), exist_ok=True)
        with open(save_path(), "w") as f:
            json.dump(d, f)
    except Exception:
        pass


# ---------------------------------------------------------------- audio
R = 16000
KEYS = (9, 7, 4, 2, 5, 0, 11, 10, 8, 3)
# accordi: (spostamento della radice, terza: 3 = minore, 4 = maggiore)
PROGS = (
    ((0, 3), (-4, 4), (3, 4), (-2, 4)),
    ((0, 3), (3, 4), (-4, 4), (-2, 4)),
    ((0, 3), (-5, 3), (-4, 4), (-2, 4)),
    ((0, 3), (-4, 4), (-2, 4), (-2, 4)),
    ((0, 3), (5, 3), (-4, 4), (-2, 4)),
    ((0, 3), (-2, 4), (-4, 4), (-2, 4)),
)
PAT = (0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 2, 3, 1, 2)
RHY = (
    ((0, 2), (2, 2), (4, 4), (8, 2), (10, 2), (12, 4)),
    ((0, 3), (3, 1), (4, 4), (8, 3), (11, 1), (12, 4)),
    ((0, 2), (2, 2), (4, 2), (6, 2), (8, 4), (12, 2), (14, 2)),
    ((0, 4), (4, 2), (6, 2), (8, 4), (12, 4)),
    ((0, 1), (1, 1), (2, 2), (4, 4), (8, 2), (10, 2), (12, 2), (14, 2)),
)
KICKS = ((0, 4, 8, 12), (0, 4, 8, 11, 12), (0, 6, 8, 14), (0, 4, 8, 12, 14))
BASSP = ((0, 3, 6, 8, 11, 14), (0, 2, 4, 6, 8, 10, 12, 14),
         (0, 6, 8, 14), (0, 3, 8, 11))
LEADS = (("sq", 0.5), ("sq", 0.25), ("saw", 0.5), ("sq", 0.125))


def _mf(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def _wav(samples):
    pcm = array.array(
        "h", [int(max(-1.0, min(1.0, x)) * 30000) for x in samples])
    if sys.byteorder == "big":
        pcm.byteswap()
    b = io.BytesIO()
    w = wave.open(b, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(R)
    w.writeframes(pcm.tobytes())
    w.close()
    return b.getvalue()


def _tone(f0, dur, vol=0.5, kind="sq", decay=5.0, slide=0.0, duty=0.5):
    n = int(dur * R)
    out = []
    ph = 0.0
    for i in range(n):
        ph += (f0 + slide * i / R) / R
        p = ph % 1.0
        if kind == "sq":
            v = 1.0 if p < duty else -1.0
        elif kind == "saw":
            v = 2.0 * p - 1.0
        else:
            v = math.sin(6.283185307 * p)
        env = math.exp(-decay * i / n) * min(1.0, i / 60.0)
        out.append(v * vol * env)
    return out


def _noise(rng, dur, vol, decay, hp=False):
    n = int(dur * R)
    out = []
    prev = 0.0
    for i in range(n):
        x = rng.uniform(-1.0, 1.0)
        v = (x - prev) * 0.5 if hp else x
        prev = x
        out.append(v * vol * math.exp(-decay * i / n))
    return out


def _kick():
    n = int(0.2 * R)
    out = []
    ph = 0.0
    for i in range(n):
        t = i / R
        ph += (42.0 + 130.0 * math.exp(-t * 38.0)) / R
        out.append(math.sin(6.283185307 * ph) * math.exp(-t * 16.0))
    return out


def _snare(rng):
    a = _noise(rng, 0.14, 0.7, 7.0)
    b = _tone(190, 0.14, 0.4, "sin", 9.0)
    return [x + y for x, y in zip(a, b)]


def _concat(parts):
    out = []
    for p in parts:
        out += p
    return out


def _melody(rng, key):
    pent = (0, 3, 5, 7, 10)
    base = 66 + key
    notes = []
    for o in (0, 12):
        for p in pent:
            m = base + o + p
            while m > 88:
                m -= 12
            notes.append(m)
    notes = sorted(set(notes))
    idx = rng.randint(2, len(notes) - 4)
    bars = []
    for _ in range(4):
        pat = RHY[rng.randrange(len(RHY))]
        bar = []
        for (st, ln) in pat:
            idx = max(0, min(len(notes) - 1,
                             idx + rng.choice((-2, -1, -1, 0, 1, 1, 2))))
            bar.append((st, notes[idx], ln))
        bars.append(bar)
    for b in range(4):
        bars.append([(st, notes[min(len(notes) - 1, notes.index(m) + 2)], ln)
                     for (st, m, ln) in bars[b]])
    return bars


def build_track(level):
    """Una musica diversa per ogni livello: tempo, tonalita', accordi,
    batteria, suono e melodia cambiano con il numero del livello."""
    rng = random.Random(900 + level * 37)
    bpm = 126 + level * 2
    key = KEYS[level % len(KEYS)]
    prog = PROGS[(level * 5 + level // 3) % len(PROGS)]
    kicks = KICKS[level % 4]
    snares = (4, 12, 15) if level % 4 == 3 else (4, 12)
    bassp = BASSP[(level // 2) % len(BASSP)]
    lkind, lduty = LEADS[level % len(LEADS)]
    aduty = (0.25, 0.125, 0.5)[level % 3]
    hatmode = level % 2
    mel = _melody(rng, key)

    spb = R * 60.0 / bpm / 4.0
    steps = 128
    n = int(round(steps * spb))
    buf = [0.0] * n
    kick = _kick()
    snare = _snare(rng)
    hat = _noise(rng, 0.04, 0.5, 6.0, True)
    cache = {}

    def note(m, ln, kind, vol, decay, duty=0.5):
        k2 = (m, ln, kind, duty)
        if k2 not in cache:
            cache[k2] = _tone(_mf(m), ln * spb / R, vol, kind, decay,
                              0.0, duty)
        return cache[k2]

    def mix(pos, smp, g):
        for j, v in enumerate(smp):
            buf[(pos + j) % n] += v * g

    for st in range(steps):
        pos = int(st * spb)
        bar = st // 16
        k = st % 16
        off, third = prog[bar % 4]
        pc = (key + off) % 12
        if k in kicks:
            mix(pos, kick, 0.9)
        if k in snares:
            mix(pos, snare, 0.5)
        if hatmode == 0:
            if k % 4 == 2:
                mix(pos, hat, 0.5)
            elif k % 2 == 1:
                mix(pos, hat, 0.18)
        else:
            mix(pos, hat, 0.45 if k % 4 == 2 else 0.2)
        if k in bassp:
            mix(pos, note(33 + pc, 2, "saw", 0.5, 3.0), 0.55)
        r = 57 + pc
        tones = (r, r + third, r + 7, r + 12)
        mix(pos, note(tones[PAT[k]], 1, "sq", 0.4, 4.0, aduty), 0.28)
        for (sk, m, ln) in mel[bar]:
            if sk == k:
                mix(pos, note(m, ln, lkind, 0.4, 1.6, lduty),
                    0.3 if lkind == "sq" else 0.2)
    return _wav([math.tanh(x * 1.2) for x in buf])


def build_sfx():
    rng = random.Random(7)
    sfx = {
        "wall": _tone(200, 0.05, 0.40, "sq", 6.0, -300.0),
        "paddle": _tone(300, 0.07, 0.45, "sq", 5.0, 400.0),
        "b1": _tone(660, 0.06, 0.40, "sq", 5.0, 0.0, 0.25),
        "b2": _tone(880, 0.06, 0.40, "sq", 5.0, 0.0, 0.25),
        "boom": [x + y for x, y in zip(_noise(rng, 0.4, 0.8, 5.0),
                                       _tone(70, 0.4, 0.7, "sin", 5.0, -40.0))],
        "pow": _concat([_tone(f, 0.05, 0.4, "sq", 2.0, 0.0, 0.25)
                        for f in (523, 659, 784, 1047)]),
        "lose": _tone(420, 0.55, 0.45, "saw", 3.0, -700.0),
        "win": _concat([_tone(f, 0.09, 0.4, "sq", 2.0, 0.0, 0.25)
                        for f in (523, 659, 784, 1047, 1319)]),
    }
    return {k: _wav(v) for k, v in sfx.items()}


# --------------------------------------------------------------- grafica
def sfondo(c, g, flat):
    c.bgcolor = flat
    try:
        c.gradient = ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            colors=[g[0], g[1]])
    except Exception:
        pass


def glow(col):
    try:
        return ft.BoxShadow(blur_radius=14, spread_radius=1, color=col)
    except Exception:
        return None


def main(page: ft.Page):
    page.title = "Arkanoid"
    page.padding = 0
    save = load_save()
    try:
        unl = int(save.get("unlocked", 1))
        tem = int(save.get("theme", 0))
        ver = int(save.get("v", 1))
    except Exception:
        unl, tem, ver = 1, 0, 1
    if ver < 2 and unl >= 11:
        unl = 12  # chi aveva finito i 11 livelli parte dal 12
    mus_on = bool(save.get("music", True))
    sfx_on = bool(save.get("sfx", True))
    nlev = len(LEVELS)
    s = {"state": "menu", "level": 0, "score": 0, "lives": 3,
         "px": (W - 76) / 2, "pw": 76, "left": 0, "wide": 0.0, "slow": 0.0,
         "unlocked": nlev if UNLOCK_ALL else max(1, min(unl, nlev)),
         "theme": tem % len(THEMES), "music": mus_on, "sfx": sfx_on}
    audio = {"music": None, "sfx": {}, "last": {}, "alt": 0,
             "want": 0, "track": None}

    def salva():
        write_save({"v": 2, "unlocked": s["unlocked"], "theme": s["theme"],
                    "music": s["music"], "sfx": s["sfx"]})

    def snd(name):
        if not s["sfx"] or name not in audio["sfx"]:
            return
        now = time.time()
        if now - audio["last"].get(name, 0.0) < 0.05:
            return
        audio["last"][name] = now
        try:
            page.run_task(audio["sfx"][name].play)
        except Exception:
            pass

    parts = []
    for _ in range(NPART):
        sz = random.choice([2, 3, 4])
        c = ft.Container(width=sz, height=sz, border_radius=sz / 2,
                         bgcolor="#ffffff", opacity=0.55, left=0, top=0)
        parts.append({"c": c, "x": random.uniform(0, W),
                      "y": random.uniform(0, H), "v": random.uniform(15, 45)})

    pool = []
    for _ in range(72):
        t = ft.Text("", size=11, color="#000000", width=BW,
                    text_align=ft.TextAlign.CENTER)
        c = ft.Container(content=t, width=BW, height=BH, border_radius=3,
                         bgcolor="#ffffff", left=0, top=0, visible=False)
        pool.append({"c": c, "t": t, "hits": 0, "x": 0, "y": 0, "vx": 0.0,
                     "type": ".", "r": 0, "col": 0})

    balls = []
    for _ in range(MAXB):
        c = ft.Container(width=BALL, height=BALL, border_radius=BALL / 2,
                         bgcolor="#ffffff", left=0, top=0, visible=False)
        balls.append({"c": c, "alive": False, "x": 0.0, "y": 0.0,
                      "vx": 0.0, "vy": 0.0})

    caps = []
    for _ in range(4):
        t = ft.Text("", size=11, color="#ffffff", width=28,
                    text_align=ft.TextAlign.CENTER)
        c = ft.Container(content=t, width=28, height=16, border_radius=8,
                         bgcolor="#4caf50", left=0, top=0, visible=False)
        caps.append({"c": c, "t": t, "alive": False, "x": 0.0, "y": 0.0,
                     "k": "L"})

    fondo = ft.Container(width=W, height=H, bgcolor="#1a1a2e")
    paddle = ft.Container(width=76, height=PH, border_radius=6,
                          bgcolor="#eeeeee", left=s["px"], top=PY)
    hud = ft.Text("", size=14, color="#ffffff", left=10, top=12)
    msg = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color="#ffffff",
                  width=W, text_align=ft.TextAlign.CENTER,
                  left=0, top=H / 2 + 60)
    st_txt = ft.Text("", size=11, color="#ffffff", opacity=0.75,
                     width=W - 16, left=8, top=H - 24)
    menu_btn = ft.Container(
        content=ft.Text("MENU", size=13, color="#ffffff", width=60,
                        text_align=ft.TextAlign.CENTER),
        width=60, height=24, border_radius=6, bgcolor="#55555555",
        left=W - 70, top=8)

    menu_bg = ft.Container(width=W, height=H, left=0, top=0,
                           bgcolor="#1a1a2e")
    menu_titolo = ft.Text("ARKANOID", size=34, weight=ft.FontWeight.BOLD,
                          color="#ffffff", width=W,
                          text_align=ft.TextAlign.CENTER, left=0, top=70)
    menu_sub = ft.Text("Scegli il livello", size=15, color="#ffffff",
                       width=W, text_align=ft.TextAlign.CENTER,
                       left=0, top=120)
    lvl_txt = []
    lvl_btns = []
    for i in range(nlev):
        t = ft.Text(str(i + 1), size=20, weight=ft.FontWeight.BOLD,
                    color="#ffffff", width=56, text_align=ft.TextAlign.CENTER)
        c = ft.Container(content=t, width=56, height=40, border_radius=8,
                         bgcolor="#7c4dff", left=16 + (i % 5) * 68,
                         top=160 + (i // 5) * 52,
                         on_click=lambda e, i=i: scegli(i))
        lvl_txt.append(t)
        lvl_btns.append(c)
    ty = 160 + ((nlev + 4) // 5) * 52 + 8
    tema_txt = ft.Text("", size=16, color="#ffffff", width=200,
                       text_align=ft.TextAlign.CENTER)
    tema_btn = ft.Container(content=tema_txt, width=200, height=34,
                            border_radius=8, bgcolor="#7c4dff",
                            left=80, top=ty, on_click=lambda e: cambia_tema())
    mus_txt = ft.Text("", size=14, color="#ffffff", width=160,
                      text_align=ft.TextAlign.CENTER)
    mus_btn = ft.Container(content=mus_txt, width=160, height=34,
                           border_radius=8, bgcolor="#7c4dff", left=16,
                           top=ty + 44, on_click=lambda e: toggle_music())
    sfx_txt = ft.Text("", size=14, color="#ffffff", width=160,
                      text_align=ft.TextAlign.CENTER)
    sfx_btn = ft.Container(content=sfx_txt, width=160, height=34,
                           border_radius=8, bgcolor="#7c4dff", left=184,
                           top=ty + 44, on_click=lambda e: toggle_sfx())
    aiuto = ft.Text(
        "Trascina il dito per muovere la barra, tocca per lanciare\n"
        "+ palle extra   ? bonus   * esplode\n"
        "Grigio = indistruttibile   <> = blocco mobile",
        size=12, color="#ffffff", width=W, text_align=ft.TextAlign.CENTER,
        left=0, top=ty + 92)
    menu_all = ([menu_bg, menu_titolo, menu_sub] + lvl_btns
                + [tema_btn, mus_btn, sfx_btn, aiuto])

    def speed():
        return min(300 + 12 * s["level"], 540)

    def pw0():
        return max(52, 76 - 2 * max(0, s["level"] - 9))

    def stato(t):
        st_txt.value = t

    def brick_color(b):
        if b["type"] in SPECIAL:
            return SPECIAL[b["type"]]
        th = THEMES[s["theme"]]
        return th["b"].get(max(1, min(3, b["hits"])), "#ffffff")

    def refresh_menu():
        th = THEMES[s["theme"]]
        last = nlev - 1
        for i in range(nlev):
            if i < s["unlocked"]:
                lvl_btns[i].bgcolor = "#d50000" if i == last else th["acc"]
                lvl_txt[i].value = str(i + 1)
            else:
                lvl_btns[i].bgcolor = "#37474f"
                lvl_txt[i].value = "🔒"
        tema_btn.bgcolor = th["acc"]
        tema_txt.value = "Tema: " + th["nome"]
        mus_btn.bgcolor = th["acc"] if s["music"] else "#37474f"
        mus_txt.value = "Musica: " + ("ON" if s["music"] else "OFF")
        sfx_btn.bgcolor = th["acc"] if s["sfx"] else "#37474f"
        sfx_txt.value = "Suoni: " + ("ON" if s["sfx"] else "OFF")

    def apply_theme():
        th = THEMES[s["theme"]]
        page.bgcolor = th["bg"]
        sfondo(fondo, th["g"], th["g"][0])
        sfondo(menu_bg, th["g"], th["g"][0])
        paddle.bgcolor = th["paddle"]
        paddle.shadow = glow(th["glow"])
        for bl in balls:
            bl["c"].bgcolor = th["ball"]
            bl["c"].shadow = glow(th["glow"])
        for p in parts:
            p["c"].bgcolor = th["pc"]
        for b in pool:
            if b["hits"] > 0:
                b["c"].bgcolor = brick_color(b)
        refresh_menu()

    def cambia_tema():
        s["theme"] = (s["theme"] + 1) % len(THEMES)
        apply_theme()
        salva()

    def apply_music():
        m = audio["music"]
        if m is not None:
            try:
                m.volume = 0.45 if s["music"] else 0.0
            except Exception:
                pass

    def toggle_music():
        s["music"] = not s["music"]
        apply_music()
        refresh_menu()
        salva()

    def toggle_sfx():
        s["sfx"] = not s["sfx"]
        refresh_menu()
        salva()

    def desc(e):
        txt = str(e)
        return type(e).__name__ + (": " + txt[:50] if txt else "")

    async def audio_task():
        if fta is None:
            stato("Audio: libreria flet-audio non trovata")
            return
        try:
            stato("Audio: preparo i suoni...")
            sfx = await asyncio.to_thread(build_sfx)
            svc = getattr(page, "services", None)
            if svc is None:
                svc = page.overlay
            for name, wav in sfx.items():
                a = fta.Audio(src=wav, release_mode=fta.ReleaseMode.STOP,
                              volume=0.8)
                audio["sfx"][name] = a
                svc.append(a)
            page.update()
            stato("Audio: suoni pronti")
        except Exception as e:
            stato("Audio errore: " + desc(e))
            return
        while True:
            await asyncio.sleep(0.5)
            lv = audio["want"]
            if lv is None or lv == audio["track"]:
                continue
            try:
                stato("Musica liv " + str(lv + 1) + ": preparo...")
                wav = await asyncio.to_thread(build_track, lv)
                m = fta.Audio(src=wav, autoplay=True,
                              release_mode=fta.ReleaseMode.LOOP,
                              volume=0.45 if s["music"] else 0.0)
                svc.append(m)
                old = audio["music"]
                audio["music"] = m
                audio["track"] = lv
                page.update()
                if old is not None:
                    try:
                        old.volume = 0.0
                        svc.remove(old)
                        page.update()
                    except Exception:
                        pass
                stato("Musica liv " + str(lv + 1) + ": ok")
            except Exception as e:
                audio["track"] = lv
                stato("Musica errore: " + desc(e))

    def show_menu(flag):
        if flag:
            s["state"] = "menu"
            refresh_menu()
        for c in menu_all:
            c.visible = flag

    def pronto_txt():
        if s["level"] == nlev - 1:
            return "FINALE! Tocca per lanciare"
        return "Tocca per lanciare"

    def ready_ball():
        for bl in balls:
            bl["alive"] = False
        balls[0]["alive"] = True
        balls[0]["vx"] = 0.0
        balls[0]["vy"] = 0.0

    def load_level():
        rows = LEVELS[s["level"]]
        hs = min(150, 70 + 8 * max(0, s["level"] - 10))
        i = 0
        n = 0
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == ".":
                    continue
                b = pool[i]
                i += 1
                b["type"] = ch
                b["vx"] = 0.0
                if ch in "123":
                    b["hits"] = int(ch)
                elif ch in "XH":
                    b["hits"] = 99
                else:
                    b["hits"] = 1
                if ch == "H":
                    b["vx"] = hs if c < 4 else -hs
                b["x"] = 10 + c * (BW + GAP)
                b["y"] = 60 + r * (BH + GAP)
                b["r"] = r
                b["col"] = c
                b["c"].left = b["x"]
                b["c"].top = b["y"]
                b["t"].value = LABEL.get(ch, "")
                b["c"].bgcolor = brick_color(b)
                b["c"].visible = True
                if ch not in "XH":
                    n += 1
        for b in pool[i:]:
            b["hits"] = 0
            b["type"] = "."
            b["c"].visible = False
        s["left"] = n
        ready_ball()
        s["state"] = "ready"
        msg.value = pronto_txt()

    def start_level(i):
        s["level"] = i
        s["lives"] = 3
        s["wide"] = 0.0
        s["slow"] = 0.0
        for cp in caps:
            cp["alive"] = False
        audio["want"] = i
        load_level()
        show_menu(False)

    def scegli(i):
        if s["state"] == "menu" and i < s["unlocked"]:
            s["score"] = 0
            start_level(i)

    def torna_menu(e=None):
        show_menu(True)

    def multi():
        src = None
        for bl in balls:
            if bl["alive"]:
                src = bl
                break
        if src is None:
            return
        for da in (-25, 25):
            for bl in balls:
                if not bl["alive"]:
                    a = math.radians(da)
                    bl["alive"] = True
                    bl["x"] = src["x"]
                    bl["y"] = src["y"]
                    bl["vx"] = src["vx"] * math.cos(a) - src["vy"] * math.sin(a)
                    bl["vy"] = src["vx"] * math.sin(a) + src["vy"] * math.cos(a)
                    break

    def capsula(cx, cy):
        for cp in caps:
            if not cp["alive"]:
                k = random.choice(["L", "L", "S", "V"])
                cp["alive"] = True
                cp["k"] = k
                cp["x"] = cx - 14
                cp["y"] = cy
                cp["c"].bgcolor = CAPS[k][0]
                cp["t"].value = CAPS[k][1]
                break

    def distruggi(b):
        b["hits"] = 0
        b["c"].visible = False
        s["left"] -= 1
        s["score"] += 10
        t = b["type"]
        if t == "E":
            snd("boom")
        elif t == "M":
            snd("pow")
        else:
            audio["alt"] += 1
            snd("b1" if audio["alt"] % 2 else "b2")
        if t == "M":
            multi()
        elif t == "P":
            capsula(b["x"] + BW / 2, b["y"] + BH / 2)
        elif t == "E":
            for o in pool:
                if (o["hits"] > 0 and o["type"] not in ("X", "H")
                        and abs(o["r"] - b["r"]) <= 1
                        and abs(o["col"] - b["col"]) <= 1):
                    distruggi(o)

    def colpisci(b):
        if b["type"] in ("X", "H"):
            snd("wall")
            return
        b["hits"] -= 1
        if b["hits"] <= 0:
            distruggi(b)
        else:
            snd("wall")
            b["c"].bgcolor = brick_color(b)

    def launch(e=None):
        st = s["state"]
        if st == "ready":
            a = math.radians(random.uniform(-25, 25))
            balls[0]["vx"] = speed() * math.sin(a)
            balls[0]["vy"] = -speed() * math.cos(a)
            s["state"] = "play"
            msg.value = ""
        elif st == "clear":
            start_level(s["level"] + 1)
        elif st == "over":
            s["score"] = 0
            start_level(s["level"])
        elif st == "won":
            show_menu(True)

    def muovi(e):
        try:
            x = getattr(e, "local_x", None)
            if x is None:
                p = getattr(e, "local_position", None)
                x = getattr(p, "x", None)
            if x is None:
                d = getattr(e, "delta_x", None)
                if d is None:
                    d = e.local_delta.x
                x = s["px"] + s["pw"] / 2 + d
            s["px"] = max(0, min(W - s["pw"], x - s["pw"] / 2))
        except Exception:
            pass

    def jit(bl):
        # piccola variazione casuale: evita che la pallina resti
        # intrappolata in un giro che si ripete all'infinito
        a = random.uniform(-0.07, 0.07)
        c, sn = math.cos(a), math.sin(a)
        bl["vx"], bl["vy"] = (bl["vx"] * c - bl["vy"] * sn,
                              bl["vx"] * sn + bl["vy"] * c)

    def step_ball(bl, dt):
        bl["x"] += bl["vx"] * dt
        bl["y"] += bl["vy"] * dt
        if bl["x"] <= 0:
            bl["x"] = 0
            bl["vx"] = abs(bl["vx"])
            snd("wall")
        elif bl["x"] >= W - BALL:
            bl["x"] = W - BALL
            bl["vx"] = -abs(bl["vx"])
            snd("wall")
        if bl["y"] <= 0:
            bl["y"] = 0
            bl["vy"] = abs(bl["vy"])
            snd("wall")
        pw = s["pw"]
        if (bl["vy"] > 0 and PY - BALL <= bl["y"] <= PY + PH
                and bl["x"] + BALL >= s["px"] and bl["x"] <= s["px"] + pw):
            hit = (bl["x"] + BALL / 2 - (s["px"] + pw / 2)) / (pw / 2)
            hit = max(-1, min(1, hit))
            a = math.radians(hit * 60)
            bl["vx"] = speed() * math.sin(a)
            bl["vy"] = -speed() * math.cos(a)
            bl["y"] = PY - BALL
            snd("paddle")
        for b in pool:
            if b["hits"] <= 0:
                continue
            ox = min(bl["x"] + BALL, b["x"] + BW) - max(bl["x"], b["x"])
            oy = min(bl["y"] + BALL, b["y"] + BH) - max(bl["y"], b["y"])
            if ox > 0 and oy > 0:
                cx = bl["x"] + BALL / 2
                cy = bl["y"] + BALL / 2
                if ox < oy:
                    if cx < b["x"] + BW / 2:
                        bl["x"] -= ox
                        bl["vx"] = -abs(bl["vx"])
                    else:
                        bl["x"] += ox
                        bl["vx"] = abs(bl["vx"])
                else:
                    if cy < b["y"] + BH / 2:
                        bl["y"] -= oy
                        bl["vy"] = -abs(bl["vy"])
                    else:
                        bl["y"] += oy
                        bl["vy"] = abs(bl["vy"])
                colpisci(b)
                jit(bl)
                break
        mn = 0.25 * speed()
        if abs(bl["vy"]) < mn:
            bl["vy"] = mn if bl["vy"] >= 0 else -mn
        if bl["y"] > H:
            bl["alive"] = False

    def step_cap(cp, dt):
        cp["y"] += 150 * dt
        if (cp["y"] + 16 >= PY and cp["y"] <= PY + PH
                and cp["x"] + 28 >= s["px"]
                and cp["x"] <= s["px"] + s["pw"]):
            cp["alive"] = False
            k = cp["k"]
            if k == "L":
                s["wide"] = time.time() + 12
            elif k == "S":
                s["slow"] = time.time() + 10
            elif k == "V":
                s["lives"] = min(5, s["lives"] + 1)
            s["score"] += 20
            snd("pow")
        elif cp["y"] > H:
            cp["alive"] = False

    def muovi_blocchi(dt):
        for b in pool:
            if b["type"] == "H":
                b["x"] += b["vx"] * dt
                if b["x"] <= 10:
                    b["x"] = 10
                    b["vx"] = abs(b["vx"])
                elif b["x"] >= W - 10 - BW:
                    b["x"] = W - 10 - BW
                    b["vx"] = -abs(b["vx"])
                b["c"].left = b["x"]

    def step(dt):
        now = time.time()
        base = pw0()
        s["pw"] = base + 34 if now < s["wide"] else base
        s["px"] = max(0, min(W - s["pw"], s["px"]))
        if s["state"] == "ready":
            bl = balls[0]
            bl["x"] = s["px"] + s["pw"] / 2 - BALL / 2
            bl["y"] = PY - BALL
            return
        if s["state"] != "play":
            return
        k = 0.7 if now < s["slow"] else 1.0
        muovi_blocchi(dt * k)
        for bl in balls:
            if bl["alive"]:
                step_ball(bl, dt * k)
        for cp in caps:
            if cp["alive"]:
                step_cap(cp, dt)
        if s["left"] <= 0:
            for cp in caps:
                cp["alive"] = False
            for bl in balls:
                bl["alive"] = False
            if s["level"] + 1 >= nlev:
                s["state"] = "won"
                msg.value = "Hai battuto il finale! Tocca"
            else:
                s["state"] = "clear"
                msg.value = "Livello superato! Tocca"
            s["unlocked"] = max(s["unlocked"], min(s["level"] + 2, nlev))
            salva()
            snd("win")
            return
        if not any(bl["alive"] for bl in balls):
            snd("lose")
            s["lives"] -= 1
            for cp in caps:
                cp["alive"] = False
            if s["lives"] <= 0:
                s["state"] = "over"
                msg.value = "Game over! Tocca"
            else:
                ready_ball()
                s["state"] = "ready"
                msg.value = pronto_txt()

    def muovi_particelle(dt):
        th = THEMES[s["theme"]]
        for p in parts:
            p["y"] += p["v"] * th["ps"] * th["pd"] * dt
            if p["y"] > H:
                p["y"] = -4
                p["x"] = random.uniform(0, W)
            elif p["y"] < -4:
                p["y"] = H
                p["x"] = random.uniform(0, W)
            p["c"].left = p["x"]
            p["c"].top = p["y"]

    def draw():
        paddle.left = s["px"]
        paddle.width = s["pw"]
        for bl in balls:
            bl["c"].visible = bl["alive"]
            bl["c"].left = bl["x"]
            bl["c"].top = bl["y"]
        for cp in caps:
            cp["c"].visible = cp["alive"]
            cp["c"].left = cp["x"]
            cp["c"].top = cp["y"]
        if s["level"] == nlev - 1:
            liv = "FINALE"
        else:
            liv = "Liv " + str(s["level"] + 1)
        hud.value = (liv + "  Punti " + str(s["score"])
                     + "  Vite " + str(s["lives"]))

    async def loop():
        last = time.time()
        while True:
            await asyncio.sleep(0.03)
            now = time.time()
            dt = min(now - last, 0.05)
            last = now
            step(dt / 2)
            step(dt / 2)
            muovi_particelle(dt)
            draw()
            page.update()

    menu_btn.on_click = torna_menu
    campo = ft.Stack(
        width=W, height=H,
        controls=([fondo] + [p["c"] for p in parts] + [hud, msg]
                  + [b["c"] for b in pool] + [cp["c"] for cp in caps]
                  + [paddle] + [bl["c"] for bl in balls] + [menu_btn]
                  + menu_all + [st_txt]),
    )
    gioco = ft.GestureDetector(content=campo, on_pan_update=muovi,
                               on_tap=launch)

    apply_theme()
    show_menu(True)
    page.add(
        ft.SafeArea(
            ft.Column(
                [ft.Row([gioco], alignment=ft.MainAxisAlignment.CENTER)]
            )
        )
    )
    page.run_task(loop)
    page.run_task(audio_task)


if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(main)
