from pathlib import Path
import json
import logging
from bs4 import BeautifulSoup

import requests

from recipe import parse_recipe, get_filepath
from utils import make_request

HOST = 'https://calorizator.ru'


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('backoff').addHandler(logging.StreamHandler())

    categories = {
        'для вегетерианцев': 'https://calorizator.ru/recipes/dietary/vegetarian',
        'сытные блюда': 'https://calorizator.ru/recipes/dietary/240',
        'простые блюда': 'https://calorizator.ru/recipes/dietary/fast'
    }

    dest_folder = '.'

    saved_recipes_count = 0

    full_dump_data = []
    pk_recipe = 1
    pk_recipe_ingredient = 1
    pk_ingredient = 0
    lookup_ingredient_titles = {}  # title:pk
    pk_preference = 0

    # Create forlder for images if not exists
    Path("media/recipes").mkdir(parents=True, exist_ok=True)

    for pref_title, cat_url in categories.items():
        pk_preference += 1
        preference = {
            "model": "recipes.preference",
            "pk": pk_preference,
            "fields": {
                "title": pref_title,
            }
        }
        full_dump_data += [preference]

        logging.info(f'Загружаем {pref_title}...')

        recipies_url_paths = get_recipies_url_paths(cat_url)
        for recipe_url_path in recipies_url_paths:
            try:
                url = f'{HOST}{recipe_url_path}/'
                recipe_page_html = make_request(url).text
                preferences = [pk_preference]

                dump_data, pk_recipe, pk_recipe_ingredient, pk_ingredient \
                    = parse_recipe(
                        recipe_page_html, pk_recipe, pk_recipe_ingredient,
                        pk_ingredient, lookup_ingredient_titles,
                        preferences)
                full_dump_data += dump_data
                logging.info(f'{url} dumped.')

                print(pk_recipe, pk_recipe_ingredient, pk_ingredient)

                saved_recipes_count += 1
            except requests.HTTPError as e:
                logging.error(f'Recipe {recipe_url_path} is not saved: {e}')
            except Exception as e:
                logging.error(f'Recipe {recipe_url_path} is not saved: {e}')
                print(e)

        recipes_db = get_filepath('dump.json', dest_folder)
        with open(recipes_db, 'w') as recipes:
            json.dump(full_dump_data, recipes, indent=2, ensure_ascii=False)
        logging.info(f'{pref_title} is loaded! {saved_recipes_count} saved.')


def get_recipies_url_paths(category_base_url: str):
    page_html = make_request(category_base_url)
    soup = BeautifulSoup(page_html.text, 'lxml')
    content = soup.select_one('div#main-content')

    recipies_link_tags = content.select(
        '.view-content table.views-table td.views-field.views-field-title.active>a')
    recipies_url_paths = [link['href'] for link in recipies_link_tags]
    return recipies_url_paths


if __name__ == '__main__':
    main()
