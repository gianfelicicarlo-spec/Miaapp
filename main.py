import flet as ft

def main(page: ft.Page):
    page.add(
        ft.SafeArea(
            ft.Column(
                [ft.Text("Ciao Android!", size=32)],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
    )

if hasattr(ft, "run"):
    ft.run(main)
else:
    ft.app(main)
