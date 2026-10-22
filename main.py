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
SPECIAL = {"X": "#78909c", "M": "#ba68c8", "P": "#fff176", "E": "#ff7043"}
LABEL = {"X": "", "M": "+", "P": "?", "E": "*"}
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
    # FINALE: labirinto di blocchi fissi, la pallina deve zigzagare
    ["3P3MM3P3", ".XXXXXXX", "E......E", "XXXXXXX.", "2......2",
     ".XXXXXXX", "3......3", "XXX..XXX", "11111111"],
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


R = 16000
BASS = (45, 41, 48, 43)
ARP = ((69, 72, 76, 81), (65, 69, 72, 77), (72, 76, 79, 84), (67, 71, 74, 79))
PAT = (0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 2, 3, 1, 2)
MEL = [
    ((0, 76, 2), (2, 79, 2), (4, 81, 4), (8, 79, 2), (10, 76, 2), (12, 74, 4)),
    ((0, 72, 2), (2, 76, 2), (4, 77, 4), (8, 76, 2), (10, 72, 2), (12, 69, 4)),
    ((0, 79, 2), (2, 84, 2), (4, 83, 2), (6, 79, 2), (8, 76, 4), (12, 79, 4)),
    ((0, 74, 2), (2, 79, 2), (4, 83, 4), (8, 81, 2), (10, 79, 2), (12, 74, 4)),
    ((0, 81, 2), (2, 84, 2), (4, 88, 4), (8, 84, 2), (10, 81, 2), (12, 79, 2), (14, 76, 2)),
    ((0, 77, 2), (2, 81, 2), (4, 84, 4), (8, 81, 2), (10, 77, 2), (12, 76, 2), (14, 72, 2)),
    ((0, 84, 2), (2, 88, 2), (4, 91, 4), (8, 88, 2), (10, 84, 2), (12, 79, 2), (14, 84, 2)),
    ((0, 83, 2), (2, 86, 2), (4, 79, 4), (8, 86, 2), (10, 83, 2), (12, 79, 2), (14, 74, 2)),
]


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


def _music(rng):
    spb = R * 60.0 / 140.0 / 4.0
    steps = 128
    n = int(round(steps * spb))
    buf = [0.0] * n
    kick = _kick()
    snare = _snare(rng)
    hat = _noise(rng, 0.04, 0.5, 6.0, True)
    cache = {}

    def note(m, ln, kind, vol, decay, duty=0.5):
        key = (m, ln, kind, duty)
        if key not in cache:
            cache[key] = _tone(_mf(m), ln * spb / R, vol, kind, decay,
                               0.0, duty)
        return cache[key]

    def mix(pos, smp, g):
        for j, v in enumerate(smp):
            buf[(pos + j) % n] += v * g

    for st in range(steps):
        pos = int(st * spb)
        bar = st // 16
        k = st % 16
        c = bar % 4
        if k % 4 == 0:
            mix(pos, kick, 0.9)
        if k in (4, 12):
            mix(pos, snare, 0.5)
        if k % 4 == 2:
            mix(pos, hat, 0.5)
        elif k % 2 == 1:
            mix(pos, hat, 0.18)
        if k in (0, 3, 6, 8, 11, 14):
            mix(pos, note(BASS[c], 2, "saw", 0.5, 3.0), 0.55)
        mix(pos, note(ARP[c][PAT[k]], 1, "sq", 0.4, 4.0, 0.25), 0.28)
        for (sk, m, ln) in MEL[bar]:
            if sk == k:
                mix(pos, note(m, ln, "sq", 0.4, 1.6, 0.5), 0.3)
    return [math.tanh(x * 1.2) for x in buf]


def build_audio():
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
    return {"sfx": {k: _wav(v) for k, v in sfx.items()},
            "music": _wav(_music(rng))}


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
    except Exception:
        unl, tem = 1, 0
    mus_on = bool(save.get("music", True))
    sfx_on = bool(save.get("sfx", True))
    s = {"state": "menu", "level": 0, "score": 0, "lives": 3,
         "px": (W - 76) / 2, "pw": 76, "left": 0, "wide": 0.0, "slow": 0.0,
         "unlocked": len(LEVELS) if UNLOCK_ALL else max(1, min(unl, len(LEVELS))),
         "theme": tem % len(THEMES), "music": mus_on, "sfx": sfx_on}
    audio = {"music": None, "sfx": {}, "last": {}, "alt": 0}

    def salva():
        write_save({"unlocked": s["unlocked"], "theme": s["theme"],
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
        pool.append({"c": c, "t": t, "hits": 0, "x": 0, "y": 0,
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
    for i in range(len(LEVELS)):
        t = ft.Text(str(i + 1), size=20, weight=ft.FontWeight.BOLD,
                    color="#ffffff", width=56, text_align=ft.TextAlign.CENTER)
        c = ft.Container(content=t, width=56, height=40, border_radius=8,
                         bgcolor="#7c4dff", left=16 + (i % 5) * 68,
                         top=160 + (i // 5) * 54,
                         on_click=lambda e, i=i: scegli(i))
        lvl_txt.append(t)
        lvl_btns.append(c)
    tema_txt = ft.Text("", size=16, color="#ffffff", width=200,
                       text_align=ft.TextAlign.CENTER)
    tema_btn = ft.Container(content=tema_txt, width=200, height=34,
                            border_radius=8, bgcolor="#7c4dff",
                            left=80, top=340, on_click=lambda e: cambia_tema())
    mus_txt = ft.Text("", size=14, color="#ffffff", width=160,
                      text_align=ft.TextAlign.CENTER)
    mus_btn = ft.Container(content=mus_txt, width=160, height=34,
                           border_radius=8, bgcolor="#7c4dff", left=16,
                           top=384, on_click=lambda e: toggle_music())
    sfx_txt = ft.Text("", size=14, color="#ffffff", width=160,
                      text_align=ft.TextAlign.CENTER)
    sfx_btn = ft.Container(content=sfx_txt, width=160, height=34,
                           border_radius=8, bgcolor="#7c4dff", left=184,
                           top=384, on_click=lambda e: toggle_sfx())
    aiuto = ft.Text(
        "Trascina il dito per muovere la barra\n"
        "Tocca per lanciare la pallina\n\n"
        "+ palle extra    ? bonus    * esplode\n"
        "Grigio = indistruttibile",
        size=13, color="#ffffff", width=W, text_align=ft.TextAlign.CENTER,
        left=0, top=440)
    menu_all = ([menu_bg, menu_titolo, menu_sub] + lvl_btns
                + [tema_btn, mus_btn, sfx_btn, aiuto])

    def speed():
        return min(300 + 25 * s["level"], 460)

    def brick_color(b):
        if b["type"] in SPECIAL:
            return SPECIAL[b["type"]]
        th = THEMES[s["theme"]]
        return th["b"].get(max(1, min(3, b["hits"])), "#ffffff")

    def refresh_menu():
        th = THEMES[s["theme"]]
        last = len(LEVELS) - 1
        for i in range(len(LEVELS)):
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
        if audio["music"] is not None:
            audio["music"].volume = 0.45 if s["music"] else 0.0
            try:
                audio["music"].update()
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

    async def init_audio():
        if fta is None:
            return
        try:
            data = await asyncio.to_thread(build_audio)
            svc = getattr(page, "services", None)
            if svc is None:
                svc = page.overlay
            for name, wav in data["sfx"].items():
                a = fta.Audio(src=wav, release_mode=fta.ReleaseMode.STOP,
                              volume=0.8)
                audio["sfx"][name] = a
                svc.append(a)
            m = fta.Audio(src=data["music"], autoplay=True,
                          release_mode=fta.ReleaseMode.LOOP,
                          volume=0.45 if s["music"] else 0.0)
            audio["music"] = m
            svc.append(m)
            page.update()
        except Exception:
            import traceback
            traceback.print_exc()

    def show_menu(flag):
        if flag:
            s["state"] = "menu"
            refresh_menu()
        for c in menu_all:
            c.visible = flag

    def pronto_txt():
        if s["level"] == len(LEVELS) - 1:
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
        i = 0
        n = 0
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == ".":
                    continue
                b = pool[i]
                i += 1
                b["type"] = ch
                if ch in "123":
                    b["hits"] = int(ch)
                elif ch == "X":
                    b["hits"] = 99
                else:
                    b["hits"] = 1
                b["x"] = 10 + c * (BW + GAP)
                b["y"] = 60 + r * (BH + GAP)
                b["r"] = r
                b["col"] = c
                b["c"].left = b["x"]
                b["c"].top = b["y"]
                b["t"].value = LABEL.get(ch, "")
                b["c"].bgcolor = brick_color(b)
                b["c"].visible = True
                if ch != "X":
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
            capsula(b["x"] + BW / 2, b["y"] + BH 
