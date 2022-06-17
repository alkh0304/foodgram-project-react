import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Load data from csv file into the database'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.csv', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(
                os.path.join(DATA_ROOT, options['filename']),
                newline='',
                encoding='utf8'
            ) as csv_file:
                data = csv.reader(csv_file)
                for row in data:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
        except FileNotFoundError:
            raise CommandError('Добавьте файл ingredients в директорию data')
