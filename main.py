import asyncio
import json
import math
import os
import random
import time
import flet as ft

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
    s = {"state": "menu", "level": 0, "score": 0, "lives": 3,
         "px": (W - 76) / 2, "pw": 76, "left": 0, "wide": 0.0, "slow": 0.0,
         "unlocked": len(LEVELS) if UNLOCK_ALL else max(1, min(unl, len(LEVELS))),
         "theme": tem % len(THEMES)}

    def salva():
        write_save({"unlocked": s["unlocked"], "theme": s["theme"]})

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
    aiuto = ft.Text(
        "Trascina il dito per muovere la barra\n"
        "Tocca per lanciare la pallina\n\n"
        "+ palle extra    ? bonus    * esplode\n"
        "Grigio = indistruttibile",
        size=13, color="#ffffff", width=W, text_align=ft.TextAlign.CENTER,
        left=0, top=400)
    menu_all = [menu_bg, menu_titolo, menu_sub] + lvl_btns + [tema_btn, aiuto]

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
        if t == "M":
            multi()
        elif t == "P":
            capsula(b["x"] + BW / 2, b["y"] + BH / 2)
        elif t == "E":
            for o in pool:
                if (o["hits"] > 0 and o["type"] != "X"
                        and abs(o["r"] - b["r"]) <= 1
                        and abs(o["col"] - b["col"]) <= 1):
                    distruggi(o)

    def colpisci(b):
        if b["type"] == "X":
            return
        b["hits"] -= 1
        if b["hits"] <= 0:
            distruggi(b)
        else:
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

    def step_ball(bl, dt):
        bl["x"] += bl["vx"] * dt
        bl["y"] += bl["vy"] * dt
        if bl["x"] <= 0:
            bl["x"] = 0
            bl["vx"] = abs(bl["vx"])
        elif bl["x"] >= W - BALL:
            bl["x"] = W - BALL
            bl["vx"] = -abs(bl["vx"])
        if bl["y"] <= 0:
            bl["y"] = 0
            bl["vy"] = abs(bl["vy"])
        pw = s["pw"]
        if (bl["vy"] > 0 and PY - BALL <= bl["y"] <= PY + PH
                and bl["x"] + BALL >= s["px"] and bl["x"] <= s["px"] + pw):
            hit = (bl["x"] + BALL / 2 - (s["px"] + pw / 2)) / (pw / 2)
            hit = max(-1, min(1, hit))
            a = math.radians(hit * 60)
            bl["vx"] = speed() * math.sin(a)
            bl["vy"] = -speed() * math.cos(a)
            bl["y"] = PY - BALL
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
        elif cp["y"] > H:
            cp["alive"] = False

    def step(dt):
        now = time.time()
        s["pw"] = 110 if now < s["wide"] else 76
        s["px"] = max(0, min(W - s["pw"], s["px"]))
        if s["state"] == "ready":
            bl = balls[0]
            bl["x"] = s["px"] + s["pw"] / 2 - BALL / 2
            bl["y"] = PY - BALL
            return
        if s["state"] != "play":
            return
        k = 0.7 if now < s["slow"] else 1.0
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
            if s["level"] + 1 >= len(LEVELS):
                s["state"] = "won"
                msg.value = "Hai battuto il finale! Tocca"
            else:
                s["state"] = "clear"
                msg.value = "Livello superato! Tocca"
            s["unlocked"] = max(s["unlocked"],
                                min(s["level"] + 2, len(LEVELS)))
            salva()
            return
        if not any(bl["alive"] for bl in balls):
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
        if s["level"] == len(LEVELS) - 1:
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
                  + menu_all),
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


if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(main)
