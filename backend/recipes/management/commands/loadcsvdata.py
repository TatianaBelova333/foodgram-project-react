import csv
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Color, Ingredient, MeasurementUnit, Tag

MODEL_FILE = {
    'reviews': {
        MeasurementUnit: 'measurement_units.csv',
        Ingredient: 'ingredients.csv',
        Color: 'colors.csv',
        Tag: 'tags.csv',
    }
}

CSV_DATA_PATH = settings.CSV_DATA_PATH


class Command(BaseCommand):
    help = 'Prepolutes db from csv files.'

    def _load_csv(self, file_path, model, delimiter=','):
        """Load data from a csv file into a db table."""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = csv.DictReader(file, delimiter=delimiter)
            self.stdout.write(f'Loading {model}')
            for row in data:
                try:
                    model_instance = model(**row)
                    model_instance.save()
                except Exception as er:
                    self.stdout.write(f'{row} - {er}', ending='\n\n')
            self.stdout.write(f'{model} loading  is complete', ending='\n\n')

    def handle(self, *args, **options):
        for model, csv_file in MODEL_FILE['reviews'].items():
            file_path = os.path.join(CSV_DATA_PATH, csv_file)
            self._load_csv(file_path, model)
        self.stdout.write('The db prepopulation is complete.')
