import csv
import os
from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

MODEL_FILE = {
    'apps': {
        'users': {'User': 'user.csv'},
        'recipes': {
            'MeasurementUnit': 'measurement_units.csv',
            'Ingredient': 'ingredients.csv',
            'Tag': 'tags.csv',
            'IngredientUnit': 'ingredient_unit.csv',
            'Recipe': 'recipe.csv',
            'RecipeIngredientAmount': 'recipeingredientamount.csv',
            'Recipe_tags': 'recipe_tags.csv',
        }
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
                except Exception:
                    self.stdout.write(
                        f'{row} - Ошибка добавления', ending='\n\n'
                    )
            self.stdout.write(f'{model} loading  is complete', ending='\n\n')

    def handle(self, *args, **options):
        for app_name, data in MODEL_FILE['apps'].items():
            for model_name, csv_file in data.items():
                model = apps.get_model(app_name, model_name)
                file_path = os.path.join(CSV_DATA_PATH, csv_file)
                self._load_csv(file_path, model)
            self.stdout.write('The db prepopulation is complete.')

        commands = StringIO()
        for app in apps.get_app_configs():
            call_command(
                'sqlsequencereset', app.label, stdout=commands, no_color=True
            )
        with connection.cursor() as cursor:
            cursor.execute(commands.getvalue())
