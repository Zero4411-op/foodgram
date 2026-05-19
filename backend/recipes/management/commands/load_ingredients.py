import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из файлов data/'

    def handle(self, *args, **kwargs):
        file_path = '../data/ingredients.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            ingredients = json.load(f)
            for item in ingredients:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
        self.stdout.write(self.style.SUCCESS(
            f'Загружено {len(ingredients)} ингредиентов'
        ))
