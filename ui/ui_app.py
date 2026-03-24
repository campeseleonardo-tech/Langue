# ui/app_ui.py
import flet as ft
from core_loader import load_word_db
from core_engine import GameEngine


# ---- Theme (monocolore) ----
PRIMARY = ft.Colors.GREEN_600          # Duolingo-like green
PRIMARY_DARK = ft.Colors.GREEN_700
BG = ft.Colors.WHITE
MUTED = ft.Colors.GREY_600
BORDER = ft.Colors.GREY_200


def main(page: ft.Page):
    page.title = "LinguApp"
    page.bgcolor = BG
    page.padding = 18

    # “Font simile a Duolingo”: Flet non garantisce lo stesso font su ogni OS.
    # Usiamo un look pulito con pesi e dimensioni coerenti.
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(primary=PRIMARY),
        font_family="Arial"  # scelta safe cross-platform; se vuoi proviamo "Nunito" o "Inter"
    )

    word_db = load_word_db()
    engine = GameEngine(word_db, lang="it", rounds=10)

    state = {
        "lang": "it",
        "game": "articles",      # per ora uno solo
        "screen": "setup",       # setup | game | summary
        "locked": False,         # blocca input dopo risposta sbagliata (per mostrare feedback)
        "last_result": None,     # dict: {ok, corretta, next, done, score...}
        "current": None,
    }

    # ---- UI building blocks ----
    title = ft.Text("LinguApp", size=26, weight=ft.FontWeight.W_800, color=PRIMARY_DARK)
    subtitle = ft.Text("Scegli lingua e gioco. Poi vai veloce.", size=13, color=MUTED)

    content = ft.Column(spacing=14, expand=True)

    def chip(text: str, active: bool, on_click):
        return ft.Container(
            content=ft.Text(text, size=12, weight=ft.FontWeight.W_700, color=(ft.Colors.WHITE if active else PRIMARY_DARK)),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor=(PRIMARY if active else ft.Colors.GREEN_50),
            border_radius=999,
            border=ft.border.all(1, (PRIMARY if active else ft.Colors.GREEN_100)),
            on_click=on_click,
        )

    def primary_button(text: str, on_click, disabled: bool = False):
        return ft.ElevatedButton(
            text,
            on_click=on_click,
            disabled=disabled,
            style=ft.ButtonStyle(
                bgcolor=PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=14),
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
            ),
            height=46,
        )

    def option_button(text: str, on_click, disabled: bool = False):
        # Bottoni opzioni grandi, pochi elementi, stessa tinta
        return ft.ElevatedButton(
            text,
            on_click=on_click,
            disabled=disabled,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_50,
                color=PRIMARY_DARK,
                shape=ft.RoundedRectangleBorder(radius=14),
                side=ft.BorderSide(1, ft.Colors.GREEN_200),
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
            ),
            height=46,
        )

    def card(child):
        return ft.Container(
            content=child,
            padding=ft.padding.all(16),
            border_radius=16,
            border=ft.border.all(1, BORDER),
            bgcolor=ft.Colors.WHITE,
        )

    # ---- Screen renders ----
    def render():
        content.controls.clear()

        # Header minimal
        content.controls.append(title)

        if state["screen"] == "setup":
            content.controls.append(subtitle)

            # Language selection (chips = meno pulsanti e più “leggero”)
            content.controls.append(ft.Text("Lingua", size=14, weight=ft.FontWeight.W_700, color=PRIMARY_DARK))
            lang_row = ft.Row(
                [
                    chip("IT", state["lang"] == "it", lambda e: set_lang("it")),
                    chip("DE", state["lang"] == "de", lambda e: set_lang("de")),
                    chip("FR", state["lang"] == "fr", lambda e: set_lang("fr")),
                    chip("EN", state["lang"] == "en", lambda e: set_lang("en")),
                    chip("ES", state["lang"] == "es", lambda e: set_lang("es")),
                ],
                spacing=8,
                wrap=True,
            )
            content.controls.append(lang_row)

            # Game selection (1 game now, but structure ready)
            content.controls.append(ft.Text("Gioco", size=14, weight=ft.FontWeight.W_700, color=PRIMARY_DARK))
            content.controls.append(
                card(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.BOLT, color=PRIMARY),
                            ft.Column(
                                [
                                    ft.Text("Articoli", size=16, weight=ft.FontWeight.W_800, color=PRIMARY_DARK),
                                    ft.Text("Scegli l’articolo corretto.", size=12, color=MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    )
                )
            )

            content.controls.append(primary_button("Inizia", lambda e: start_game()))

        elif state["screen"] == "game":
            q = state["current"]
            if q is None:
                state["screen"] = "summary"
                render()
                return

            # Progress line minimal
            content.controls.append(
                ft.Row(
                    [
                        ft.Text(f"{engine.score}/{len(engine.session)}", size=12, color=MUTED, weight=ft.FontWeight.W_700),
                        ft.Container(expand=True),
                        ft.Text(state["lang"].upper(), size=12, color=MUTED, weight=ft.FontWeight.W_700),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

            # Word card
            content.controls.append(
                card(
                    ft.Column(
                        [
                            ft.Text("Scegli l’articolo", size=12, color=MUTED),
                            ft.Container(height=4),
                            ft.Text(q["parola"], size=38, weight=ft.FontWeight.W_800, color=PRIMARY_DARK, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    )
                )
            )

            # Options
            opts = list(q.get("opts", []))
            # nessuna randomizzazione aggressiva qui: semplice (se vuoi la rimetto)
            btns = ft.Column(spacing=10)
            for opt in opts:
                btns.controls.append(option_button(opt, lambda e, c=opt: answer(c), disabled=state["locked"]))
            content.controls.append(btns)

            # Feedback area: mostrato solo dopo risposta sbagliata
            if state["last_result"] is not None and state["last_result"].get("ok") is False:
                correct = state["last_result"].get("corretta")
                content.controls.append(
                    ft.Container(
                        padding=ft.padding.all(12),
                        border_radius=14,
                        bgcolor=ft.Colors.RED_50,
                        border=ft.border.all(1, ft.Colors.RED_200),
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO, color=ft.Colors.RED_700),
                                ft.Text(f"Era: {correct}", color=ft.Colors.RED_700, weight=ft.FontWeight.W_700),
                                ft.Container(expand=True),
                                ft.TextButton("Continua", on_click=lambda e: next_question(), style=ft.ButtonStyle(color=PRIMARY_DARK)),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )

            # Exit minimal
            content.controls.append(
                ft.Row(
                    [
                        ft.TextButton("Esci", on_click=lambda e: go_setup(), style=ft.ButtonStyle(color=MUTED)),
                    ]
                )
            )

        else:  # summary
            content.controls.append(ft.Text("Riepilogo", size=18, weight=ft.FontWeight.W_800, color=PRIMARY_DARK))
            content.controls.append(ft.Text(f"Punteggio: {engine.score} / {len(engine.session)}", size=14, color=MUTED))

            # History minimal (solo righe)
            hist = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
            for i, h in enumerate(engine.history, 1):
                ok = h.get("ok")
                color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
                hist.controls.append(
                    ft.Text(
                        f"{i}. {h.get('parola')} | tua: {h.get('scelta')} | ok: {h.get('corretta')}",
                        size=12,
                        color=color,
                    )
                )

            content.controls.append(card(hist))
            content.controls.append(primary_button("Ricomincia", lambda e: start_game()))
            content.controls.append(ft.TextButton("Torna al setup", on_click=lambda e: go_setup(), style=ft.ButtonStyle(color=MUTED)))

        page.update()

    # ---- Actions ----
    def set_lang(lang: str):
        state["lang"] = lang
        engine.lang = lang
        render()

    def go_setup():
        state["screen"] = "setup"
        state["locked"] = False
        state["last_result"] = None
        state["current"] = None
        render()

    def start_game():
        # reset stato gioco
        engine.start(lang=state["lang"], rounds=10)
        state["screen"] = "game"
        state["locked"] = False
        state["last_result"] = None
        state["current"] = engine.current_question()
        render()

    def answer(choice: str):
        if state["locked"]:
            return

        res = engine.submit(choice)
        state["last_result"] = res

        if res.get("ok") is True:
            # Richiesta tua: se corretto, vai subito alla prossima domanda
            state["locked"] = False
            state["last_result"] = None
            state["current"] = engine.current_question()
            if state["current"] is None:
                state["screen"] = "summary"
            render()
            return

        # se sbagliato: mostra “Era: …” e richiede “Continua”
        state["locked"] = True
        state["current"] = engine.current_question()  # engine è già avanzato
        if res.get("done"):
            # anche se finito, facciamo comunque vedere feedback e poi summary su Continua
            pass
        render()

    def next_question():
        # Sblocca e vai avanti (dopo errore)
        state["locked"] = False
        state["last_result"] = None
        state["current"] = engine.current_question()
        if state["current"] is None:
            state["screen"] = "summary"
        render()

    # ---- Mount ----
    page.add(content)
    render()


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)