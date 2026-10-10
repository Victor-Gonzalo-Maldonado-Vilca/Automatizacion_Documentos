"""Conversión a PDF con Microsoft Office (PowerPoint/Word) o LibreOffice."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from datos import ErrorDatos

# Abre el archivo sin ventana, lo exporta y cierra la aplicación solo si no
# estaba ya abierta por el usuario (para no cerrarle sus otros archivos).
_PS_POWERPOINT = r"""
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject PowerPoint.Application
$previas = $app.Presentations.Count
$p = $app.Presentations.Open($args[0], $true, $false, $false)
try { $p.SaveAs($args[1], 32) } finally { $p.Close() }
if ($previas -eq 0) { $app.Quit() }
"""

_PS_WORD = r"""
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$d = $app.Documents.Open($args[0], $false, $true)
try { $d.SaveAs([ref]$args[1], [ref]17) } finally { $d.Close([ref]0) }
if ($app.Documents.Count -eq 0) { $app.Quit() }
"""


def _ps(ruta: Path) -> str:
    return str(ruta).replace("'", "''")


def _con_office(script: str, origen: Path, destino: Path) -> bool:
    if sys.platform != "win32":
        return False
    proceso = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         f"& {{{script}}} '{_ps(origen)}' '{_ps(destino)}'"],
        capture_output=True, text=True, timeout=300,
    )
    return proceso.returncode == 0 and destino.exists()


def _con_libreoffice(origen: Path, destino: Path) -> bool:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return False
    subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", str(destino.parent), str(origen)],
                   capture_output=True, timeout=300)
    generado = destino.parent / (origen.stem + ".pdf")
    if generado.exists() and generado != destino:
        generado.replace(destino)
    return destino.exists()


def a_pdf(origen: Path, destino: Path) -> Path:
    """Convierte un .pptx o .docx a PDF."""
    destino = destino.resolve()
    if destino.exists():
        try:
            destino.unlink()
        except PermissionError as e:
            raise ErrorDatos(f"No se pudo reemplazar {destino.name}: ciérralo y vuelve a intentar.") from e
    script = _PS_POWERPOINT if origen.suffix.lower() == ".pptx" else _PS_WORD
    if _con_office(script, origen.resolve(), destino) or _con_libreoffice(origen.resolve(), destino):
        return destino
    app = "PowerPoint" if origen.suffix.lower() == ".pptx" else "Word"
    raise ErrorDatos(f"No se pudo convertir {origen.name} a PDF: se necesita Microsoft {app} o LibreOffice.")


_PS_ACTUALIZAR = r"""
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$d = $app.Documents.Open($args[0], $false, $false)
try {
  $d.Fields.Update() | Out-Null
  foreach ($t in $d.TablesOfContents) { $t.Update() }
  foreach ($t in $d.TablesOfFigures) { $t.Update() }
  $d.Save()
} finally { $d.Close([ref]0) }
if ($app.Documents.Count -eq 0) { $app.Quit() }
"""


def actualizar_campos(docx: Path) -> bool:
    """Actualiza índices y campos (TOC, SEQ, PAGE) de un .docx con Word.

    Devuelve False si Word no está disponible (no es un error).
    """
    if sys.platform != "win32":
        return False
    try:
        proceso = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             f"& {{{_PS_ACTUALIZAR}}} '{_ps(docx.resolve())}'"],
            capture_output=True, text=True, timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proceso.returncode == 0
