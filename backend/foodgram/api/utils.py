import io
from typing import TextIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import RecipeIngredient, Recipe


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
    for i, (name, info) in enumerate(data.items(), 1):
        p.drawString(75, height, (f'{i}. {name} - {info["amount"]} '
                                  f'{info["measurement_unit"]}'))
        height -= 20

    p.drawString(50, height, "Удачного похода в магазин!")
    p.showPage()
    p.save()
    buffer.seek(0)

    return buffer


def bulk_create_ingredients(recipe: Recipe, ingredients: dict) -> None:
    RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(ingredient_id=ingredient['ingredient']['id'],
                              amount=ingredient['amount'], recipe=recipe)
                for ingredient in ingredients])
