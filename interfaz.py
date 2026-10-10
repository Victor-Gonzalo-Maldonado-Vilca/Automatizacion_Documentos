"""Abre la interfaz gráfica en el navegador.

Uso:
    python interfaz.py              # http://127.0.0.1:5000
    python interfaz.py --puerto 8000 --sin-navegador
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from web.servidor import crear_app  # noqa: E402


def puerto_libre(preferido: int) -> int:
    for puerto in range(preferido, preferido + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", puerto)) != 0:
                return puerto
    return preferido


def main() -> None:
    p = argparse.ArgumentParser(description="Interfaz gráfica del generador de documentos.")
    p.add_argument("--puerto", type=int, default=5000)
    p.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador automáticamente")
    a = p.parse_args()

    puerto = puerto_libre(a.puerto)
    url = f"http://127.0.0.1:{puerto}"
    print(f"Interfaz disponible en {url}  (Ctrl+C para cerrar)")
    if not a.sin_navegador:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    # Solo escucha en esta PC (127.0.0.1): no es accesible desde la red.
    crear_app().run(host="127.0.0.1", port=puerto, debug=False, threaded=True)


if __name__ == "__main__":
    main()
