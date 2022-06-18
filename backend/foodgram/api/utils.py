import io
from typing import TextIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def convert_pdf(data: list, title: str) -> TextIO:
    """Конвертирует данные в pdf-файл при помощи ReportLab."""

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    pdfmetrics.registerFont(TTFont('Raleway Bold', './fonts/Raleway-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Raleway', './fonts/Raleway-Regular.ttf'))

    p.setFont('Raleway Bold', 18)
    height = 800
    p.drawString(50, height, f'{title}')
    height -= 30

    p.setFont('Raleway', 14)
    string_number = 1
    for i in data:
        p.drawString(
            15, height,
            f'{string_number}. {i[0].capitalize()} ({i[1]}) - {i[2]}'
        )
        height -= 20
        string_number += 1

    p.drawString(50, height, "Удачного похода в магазин!")
    p.showPage()
    p.save()
    buffer.seek(0)

    return buffer
