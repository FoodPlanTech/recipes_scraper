import re
import logging

from bs4 import BeautifulSoup

from utils import make_request, get_filepath, get_filename_from_url


def download_image(url: str, folder: str):
    """Save an image from `url` to the given `folder`."""
    image_filename = get_filename_from_url(url)
    image_path = get_filepath(image_filename, folder)

    if image_path.is_file():  # image already exists
        return image_path

    resp = make_request(url)
    with open(image_path, 'wb') as image:
        image.write(resp.content)
    return image_path


def parse_recipe(page_html: str,
                 pk_recipe,
                 pk_recipe_ingredient,
                 pk_ingredient,
                 lookup_ingredient_titles,
                 preferences,
                 ) -> dict:
    soup = BeautifulSoup(page_html, 'lxml')
    content = soup.select_one('div#main-content')

    recipe_title = content.select_one('#page-title').text

    ing_tag = content.select('#recipes-col1 .field-items ul li')

    dump_data = []

    for ing in ing_tag:
        raw_title, raw_weight = ing.text.split(' - ')
        title = re.sub(r'\(.*\)', '', raw_title).strip()

        ing_amount = 0
        try:  # TODO: durty!
            ing_amount = int(raw_weight.split(' ')[0].split(',')[0])
        except:
            ...

        # Ingredient record
        ing_pk = lookup_ingredient_titles.get(title)
        if not ing_pk:
            pk_ingredient += 1
            ing_pk = pk_ingredient
            lookup_ingredient_titles[title] = ing_pk

        ingredient = {
            "model": "recipes.ingredient",
            "pk": ing_pk,
            "fields": {
                "title": title,
                "price_currency": "RUB",
                "price": "0.00",
                "calories": None
            }
        }
        dump_data.append(ingredient)

        # Recipe-Ingredient record
        recipe_ingredient = {
            "model": "recipes.recipeingredients",
            "pk": pk_recipe_ingredient,
            "fields": {
                "ingredient": ing_pk,
                "recipe": pk_recipe,
                "amount": ing_amount,
                "units": "GRAMS"  # TODO: always grams for now
            }
        }
        dump_data.append(recipe_ingredient)
        pk_recipe_ingredient += 1

    instructions = content.select_one(
        'div[itemprop="recipeInstructions"]').text.strip()

    img_url = content.select_one('img[itemprop="image"]')['src']
    img_media_relative_path = img_url
    try:
        saved_img = download_image(img_url, f'media/recipes')
        logging.info(f'Cover saved to {saved_img}.')
        img_media_relative_path = str(saved_img).lstrip('media/')
    except Exception as img_e:
        logging.error(f'Failed saving images: {img_e}')

    recipe = {
        "model": "recipes.recipe",
        "pk": pk_recipe,
        "fields": {
            "title": recipe_title,
            "image": img_media_relative_path,
            "guide": instructions,
            "is_teaser": False,
            "likes": [],
            "dislikes": [],
            "preferences": preferences,
        }
    }
    dump_data.append(recipe)
    pk_recipe += 1

    return dump_data, pk_recipe, pk_recipe_ingredient, pk_ingredient
