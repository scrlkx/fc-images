"""Nautilus context menu extension for fc-images."""

import locale
import shlex
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Nautilus", "4.1")
gi.require_version("GObject", "2.0")
from gi.repository import GObject, Nautilus

# resolve() follows the symlink from the nautilus extensions dir back to the real file
_PROJECT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _PROJECT_DIR / ".venv" / "bin" / "python"
_SCRIPT = _PROJECT_DIR / "convert_images.py"

_STRINGS = {
    "pt": {
        "prepare":          "Preparar Imagens",
        "prepare_tip":      "Converte formatos e remove fundos usando IA",
        "convert":          "Converter Formatos",
        "convert_tip":      "Converte WebP/AVIF/JPEG para PNG, sem remover fundos",
        "remove_bg":        "Remover Fundos",
        "remove_bg_tip":    "Remove fundos dos PNGs existentes usando IA",
        "done":             "Concluído",
        "press_enter":      "Pressione Enter para fechar...",
    },
    "en": {
        "prepare":          "Prepare Images",
        "prepare_tip":      "Convert formats and remove backgrounds using AI",
        "convert":          "Convert Formats",
        "convert_tip":      "Convert WebP/AVIF/JPEG to PNG, keeping backgrounds",
        "remove_bg":        "Remove Backgrounds",
        "remove_bg_tip":    "Remove backgrounds from existing PNGs using AI",
        "done":             "Done",
        "press_enter":      "Press Enter to close...",
    },
}


def _detect_lang() -> str:
    lang = locale.getlocale()[0] or ""
    return "pt" if lang.lower().startswith("pt") else "en"


_T = _STRINGS[_detect_lang()]


def _uri_to_path(uri: str) -> str:
    return unquote(urlparse(uri).path)


def _detect_terminal():
    """Return a callable (title, bash_cmd) -> argv, or None if nothing is found."""
    candidates = [
        ("ptyxis",         lambda t, c: ["ptyxis", "--new-window", "-T", t, "--", "bash", "-c", c]),
        ("gnome-terminal", lambda t, c: ["gnome-terminal", "--title", t, "--", "bash", "-c", c]),
        ("xfce4-terminal", lambda t, c: ["xfce4-terminal", "--title", t, "-x", "bash", "-c", c]),
        ("konsole",        lambda _t, c: ["konsole", "-e", "bash", "-c", c]),
        ("xterm",          lambda t, c: ["xterm", "-T", t, "-e", "bash", "-c", c]),
    ]
    for name, fn in candidates:
        if shutil.which(name):
            return fn
    return None


_terminal_fn = _detect_terminal()


def _run_in_terminal(directory: str, flag: str | None, title: str) -> None:
    if _terminal_fn is None:
        return

    args = [str(_VENV_PYTHON), str(_SCRIPT), directory]
    if flag:
        args.append(flag)

    cmd = " ".join(shlex.quote(a) for a in args)
    bash_cmd = (
        f"{cmd}; "
        f'echo ""; '
        f'echo "--- {_T["done"]} ($?) ---"; '
        f'echo "{_T["press_enter"]}"; '
        f"read"
    )

    subprocess.Popen(_terminal_fn(title, bash_cmd), start_new_session=True)


class FcImagesMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files: list) -> list | None:
        if len(files) != 1 or not files[0].is_directory():
            return None

        directory = _uri_to_path(files[0].get_uri())

        items = [
            ("FcImages::prepare",   _T["prepare"],   _T["prepare_tip"],   None,                directory),
            ("FcImages::convert",   _T["convert"],   _T["convert_tip"],   "--keep-background", directory),
            ("FcImages::remove_bg", _T["remove_bg"], _T["remove_bg_tip"], "--backgrounds-only", directory),
        ]

        menu_items = []
        for name, label, tip, flag, d in items:
            item = Nautilus.MenuItem(name=name, label=label, tip=tip)
            item.connect("activate", lambda _, f, t, path: _run_in_terminal(path, f, t), flag, label, d)
            menu_items.append(item)

        return menu_items
