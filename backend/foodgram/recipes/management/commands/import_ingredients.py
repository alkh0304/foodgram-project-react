import csv

from django.core.management.base import BaseCommand

from ...models import Ingredient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        ingredient_count = Ingredient.objects.count()
        reader = csv.DictReader(
                open(options['file_path']),
                fieldnames=['name', 'measurement_unit']
        )

        Ingredient.objects.bulk_create([Ingredient(**data) for data in reader])
        if (Ingredient.objects.count() > ingredient_count):
            self.stdout.write(self.style.SUCCESS('Successfully loaded'))
        else:
            self.stdout.write(self.style.ERROR('NOT loaded'))
