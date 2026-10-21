import asyncio
import math
import random
import time
import flet as ft

W, H = 360, 600
BALL = 14
PW, PH = 76, 12
PY = H - 70
BW, BH, GAP = 39, 18, 4
COLORS = {1: "#4fc3f7", 2: "#ffb74d", 3: "#e57373"}

LEVELS = [
    ["11111111", "11111111", "11111111"],
    ["11111111", "12222221", "12222221", "11111111"],
    ["1.1.1.1.", ".2.2.2.2", "1.1.1.1.", ".2.2.2.2", "33333333"],
    ["...11...", "..1221..", ".122221.", "12233221", "33333333"],
    ["33333333", "3.3.3.3.", "22222222", ".1.1.1.1", "11111111"],
]


def main(page: ft.Page):
    page.title = "Arkanoid"
    page.bgcolor = "#101018"
    page.padding = 0

    s = {"state": "ready", "level": 0, "score": 0, "lives": 3,
         "px": (W - PW) / 2, "bx": 0.0, "by": 0.0,
         "vx": 0.0, "vy": 0.0, "left": 0}

    pool = []
    for _ in range(56):
        c = ft.Container(width=BW, height=BH, border_radius=3,
                         bgcolor="#ffffff", left=0, top=0, visible=False)
        pool.append({"c": c, "hits": 0, "x": 0, "y": 0})

    fondo = ft.Container(width=W, height=H, bgcolor="#1a1a2e")
    paddle = ft.Container(width=PW, height=PH, border_radius=6,
                          bgcolor="#eeeeee", left=s["px"], top=PY)
    ball = ft.Container(width=BALL, height=BALL, border_radius=BALL / 2,
                        bgcolor="#ffffff", left=0, top=0)
    hud = ft.Text("", size=14, color="#ffffff", left=10, top=12)
    msg = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color="#ffffff",
                  width=W, text_align=ft.TextAlign.CENTER,
                  left=0, top=H / 2 + 40)

    def speed():
        return min(300 + 25 * s["level"], 460)

    def load_level():
        rows = LEVELS[s["level"]]
        i = 0
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch in "123":
                    b = pool[i]
                    i += 1
                    b["hits"] = int(ch)
                    b["x"] = 10 + c * (BW + GAP)
                    b["y"] = 60 + r * (BH + GAP)
                    b["c"].left = b["x"]
                    b["c"].top = b["y"]
                    b["c"].bgcolor = COLORS[b["hits"]]
                    b["c"].visible = True
        for b in pool[i:]:
            b["hits"] = 0
            b["c"].visible = False
        s["left"] = i
        s["state"] = "ready"
        msg.value = "Tocca per lanciare"

    def new_game():
        s["level"] = 0
        s["score"] = 0
        s["lives"] = 3
        load_level()

    def launch(e=None):
        st = s["state"]
        if st == "ready":
            a = math.radians(random.uniform(-25, 25))
            s["vx"] = speed() * math.sin(a)
            s["vy"] = -speed() * math.cos(a)
            s["state"] = "play"
            msg.value = ""
        elif st == "clear":
            s["level"] += 1
            load_level()
        elif st in ("over", "won"):
            new_game()

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
                x = s["px"] + PW / 2 + d
            s["px"] = max(0, min(W - PW, x - PW / 2))
        except Exception:
            pass

    def step(dt):
        if s["state"] == "ready":
            s["bx"] = s["px"] + PW / 2 - BALL / 2
            s["by"] = PY - BALL
            return
        if s["state"] != "play":
            return
        s["bx"] += s["vx"] * dt
        s["by"] += s["vy"] * dt
        if s["bx"] <= 0:
            s["bx"] = 0
            s["vx"] = abs(s["vx"])
        elif s["bx"] >= W - BALL:
            s["bx"] = W - BALL
            s["vx"] = -abs(s["vx"])
        if s["by"] <= 0:
            s["by"] = 0
            s["vy"] = abs(s["vy"])
        if (s["vy"] > 0 and PY - BALL <= s["by"] <= PY + PH
                and s["bx"] + BALL >= s["px"]
                and s["bx"] <= s["px"] + PW):
            hit = (s["bx"] + BALL / 2 - (s["px"] + PW / 2)) / (PW / 2)
            hit = max(-1, min(1, hit))
            a = math.radians(hit * 60)
            s["vx"] = speed() * math.sin(a)
            s["vy"] = -speed() * math.cos(a)
            s["by"] = PY - BALL
        for b in pool:
            if b["hits"] <= 0:
                continue
            ox = min(s["bx"] + BALL, b["x"] + BW) - max(s["bx"], b["x"])
            oy = min(s["by"] + BALL, b["y"] + BH) - max(s["by"], b["y"])
            if ox > 0 and oy > 0:
                cx = s["bx"] + BALL / 2
                cy = s["by"] + BALL / 2
                if ox < oy:
                    if cx < b["x"] + BW / 2:
                        s["bx"] -= ox
                        s["vx"] = -abs(s["vx"])
                    else:
                        s["bx"] += ox
                        s["vx"] = abs(s["vx"])
                else:
                    if cy < b["y"] + BH / 2:
                        s["by"] -= oy
                        s["vy"] = -abs(s["vy"])
                    else:
                        s["by"] += oy
                        s["vy"] = abs(s["vy"])
                b["hits"] -= 1
                s["score"] += 10
                if b["hits"] <= 0:
                    b["c"].visible = False
                    s["left"] -= 1
                else:
                    b["c"].bgcolor = COLORS[b["hits"]]
                break
        if s["left"] <= 0:
            if s["level"] + 1 >= len(LEVELS):
                s["state"] = "won"
                msg.value = "Hai vinto! Tocca"
            else:
                s["state"] = "clear"
                msg.value = "Livello superato! Tocca"
            return
        if s["by"] > H:
            s["lives"] -= 1
            if s["lives"] <= 0:
                s["state"] = "over"
                msg.value = "Game over! Tocca"
            else:
                s["state"] = "ready"
                msg.value = "Tocca per lanciare"

    def draw():
        paddle.left = s["px"]
        ball.left = s["bx"]
        ball.top = s["by"]
        hud.value = ("Livello " + str(s["level"] + 1)
                     + "   Punti " + str(s["score"])
                     + "   Vite " + str(s["lives"]))

    async def loop():
        last = time.time()
        while True:
            await asyncio.sleep(0.03)
            now = time.time()
            dt = min(now - last, 0.05)
            last = now
            step(dt / 2)
            step(dt / 2)
            draw()
            page.update()

    campo = ft.Stack(
        width=W, height=H,
        controls=[fondo, hud, msg] + [b["c"] for b in pool] + [paddle, ball],
    )
    gioco = ft.GestureDetector(content=campo, on_pan_update=muovi, on_tap=launch)

    page.add(
        ft.SafeArea(
            ft.Column(
                [ft.Row([gioco], alignment=ft.MainAxisAlignment.CENTER)]
            )
        )
    )
    new_game()
    page.run_task(loop)


if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(main)
