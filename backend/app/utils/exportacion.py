"""Exportación CSV / PDF de reportes (Stage 9)."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _celda(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, Decimal):
        return f"{valor:.2f}"
    if isinstance(valor, float):
        return f"{valor:.2f}"
    return str(valor)


def generar_csv(
    columnas: Sequence[str],
    filas: Sequence[dict[str, Any]],
    *,
    encabezados: Sequence[str] | None = None,
) -> bytes:
    """Genera CSV UTF-8 con BOM (Excel-friendly) a partir de filas dict."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    headers = list(encabezados) if encabezados is not None else list(columnas)
    writer.writerow(headers)
    for fila in filas:
        writer.writerow([_celda(fila.get(col)) for col in columnas])
    # BOM UTF-8 para Excel
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def generar_pdf(
    titulo: str,
    columnas: Sequence[str],
    filas: Sequence[dict[str, Any]],
    *,
    encabezados: Sequence[str] | None = None,
    notas: str | None = None,
) -> bytes:
    """Genera PDF tabular simple con ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    story: list = []
    story.append(Paragraph(f"<b>SubliManager — {titulo}</b>", styles["Title"]))
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Generado: {generado}", styles["Normal"]))
    if notas:
        story.append(Paragraph(notas, styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    headers = list(encabezados) if encabezados is not None else list(columnas)
    data = [headers]
    for fila in filas:
        data.append([_celda(fila.get(col)) for col in columnas])
    if len(data) == 1:
        data.append(["—"] * len(headers))

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F5F7FA")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
