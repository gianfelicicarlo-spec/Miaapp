import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Ciao Android!"))

if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(main)
