"""User-driven TheMealDB lookups. No recipe writes and no bulk collection."""
import base64
import json
import os
import re
from urllib.parse import urlencode, urlsplit

from . import photos
from .recipe_advice import plain, normalized_tags
from .safe_fetch import ImportProblem, fetch_html, fetch_image, validate_url

HOST = 'www.themealdb.com'
ALIASES = {
    'poulet au curry': 'chicken curry', 'curry de poulet': 'chicken curry',
    'poulet roti': 'roast chicken', 'poulet': 'chicken',
    'boeuf bourguignon': 'bourguignon', 'bœuf bourguignon': 'bourguignon',
    'pates carbonara': 'carbonara', 'pates a la carbonara': 'carbonara',
    'lasagnes': 'lasagne', 'lasagnes a la bolognaise': 'lasagne',
    'soupe de tomates': 'tomato soup', 'soupe aux tomates': 'tomato soup',
    'soupe de legumes': 'vegetable soup', 'quiche lorraine': 'quiche',
    'poisson pane': 'fish', 'boeuf': 'beef', 'bœuf': 'beef',
    'gateau au chocolat': 'chocolate cake', 'mousse au chocolat': 'chocolate mousse',
    'tarte aux pommes': 'apple tart', 'riz au lait': 'rice pudding',
    'crepes': 'pancakes', 'omelette': 'omelette', 'lentilles': 'lentil',
}
CATEGORIES = {'Beef': 'Bœuf', 'Chicken': 'Poulet', 'Dessert': 'Dessert', 'Lamb': 'Agneau',
              'Pasta': 'Pâtes', 'Pork': 'Porc', 'Seafood': 'Poisson et fruits de mer',
              'Side': 'Accompagnement', 'Starter': 'Entrée', 'Breakfast': 'Petit-déjeuner', 'Goat': 'Chèvre'}
AREAS = {'French': 'française', 'France': 'française', 'Italian': 'italienne', 'Italy': 'italienne',
         'Indian': 'indienne', 'India': 'indienne', 'Japanese': 'japonaise', 'Japan': 'japonaise',
         'Chinese': 'chinoise', 'China': 'chinoise', 'Mexican': 'mexicaine', 'Mexico': 'mexicaine',
         'British': 'britannique', 'United Kingdom': 'britannique', 'Thai': 'thaïlandaise', 'Thailand': 'thaïlandaise',
         'Spanish': 'espagnole', 'Spain': 'espagnole', 'Moroccan': 'marocaine', 'Morocco': 'marocaine',
         'Greek': 'grecque', 'Greece': 'grecque', 'American': 'américaine', 'United States': 'américaine',
         'Turkish': 'turque', 'Turkey': 'turque', 'Vietnamese': 'vietnamienne', 'Vietnam': 'vietnamienne'}
LABELS = {'MainMeal': 'Plat principal', 'Main': 'Plat principal', 'Dinner': 'Dîner', 'Lunch': 'Déjeuner',
          'Bake': 'Au four', 'Baking': 'Au four', 'Stew': 'Mijoté', 'BBQ': 'Barbecue',
          'Pasta': 'Pâtes', 'Curry': 'Curry', 'Soup': 'Soupe', 'Breakfast': 'Petit-déjeuner',
          'Cake': 'Gâteau', 'Pudding': 'Dessert', 'SideDish': 'Accompagnement', 'Starter': 'Entrée',
          'Spicy': 'Épicé', 'Brunch': 'Brunch', 'Snack': 'En-cas', 'Pie': 'Tarte'}


def api_url(endpoint, parameters):
    key = os.getenv('MIJOTE_THEMEALDB_KEY', '1')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', key):
        raise ImportProblem('La configuration TheMealDB est invalide.')
    return f'https://{HOST}/api/json/v1/{key}/{endpoint}.php?' + urlencode(parameters)


def request(endpoint, parameters):
    raw, final = fetch_html(api_url(endpoint, parameters))
    parsed = urlsplit(final)
    if parsed.scheme != 'https' or parsed.hostname != HOST:
        raise ImportProblem('TheMealDB a renvoyé une adresse inattendue.')
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        raise ImportProblem('TheMealDB a renvoyé une réponse illisible.') from None
    if not isinstance(payload, dict) or 'meals' not in payload:
        raise ImportProblem('Réponse TheMealDB invalide.')
    meals = payload['meals']
    if meals is not None and (not isinstance(meals, list) or any(not isinstance(m, dict) for m in meals)):
        raise ImportProblem('Réponse TheMealDB invalide.')
    return (meals or [])[:100]


def image_url(value):
    if not isinstance(value, str) or not value:
        return ''
    try:
        target = validate_url(value)
    except ImportProblem:
        return ''
    parsed = urlsplit(target.url)
    if target.scheme != 'https' or target.host != HOST or parsed.query or not re.fullmatch(r'/images/media/meals/[A-Za-z0-9_-]+\.(?:jpe?g|png|webp)(?:/(?:small|medium|large))?', parsed.path):
        return ''
    return target.url


def source_url(value):
    try:
        return validate_url(value).url if isinstance(value, str) and value else ''
    except ImportProblem:
        return ''


def text(value, maximum=120):
    return ' '.join(value.split())[:maximum] if isinstance(value, str) else ''


def result(meal):
    ident, name = str(meal.get('idMeal') or ''), text(meal.get('strMeal'))
    if not re.fullmatch(r'[1-9][0-9]{0,11}', ident) or not name:
        return None
    category, area = text(meal.get('strCategory'), 50), text(meal.get('strArea') or meal.get('strCountry'), 50)
    tags = [CATEGORIES[category]] if category in CATEGORIES else []
    if area in AREAS:
        tags.append('Cuisine ' + AREAS[area])
    for label in text(meal.get('strTags'), 500).split(','):
        if label.strip() in LABELS:
            tags.append(LABELS[label.strip()])
    return {'id': ident, 'title': name, 'image_url': image_url(meal.get('strMealThumb')),
            'category': category, 'area': area, 'tags': normalized_tags(tags)[:20],
            'source_url': source_url(meal.get('strSource')), 'provider': 'TheMealDB',
            'provider_url': 'https://www.themealdb.com/meal.php?' + urlencode({'c': ident}),
            'attribution': 'TheMealDB · ' + name,
            'image_origin': source_url(meal.get('strImageSource'))}


def search(query):
    query = ' '.join(query.split())
    if not query or len(query) > 120:
        raise ImportProblem('Saisissez un nom de plat entre 1 et 120 caractères.')
    used = ALIASES.get(plain(query), query)
    meals = request('search', {'s': used})
    items, seen = [], set()
    for meal in meals:
        item = result(meal)
        if item and item['id'] not in seen:
            seen.add(item['id']); items.append(item)
        if len(items) == 6:
            break
    return {'items': items, 'query_used': used, 'adapted': used != query,
            'message': 'Titres originaux TheMealDB, souvent en anglais. Choisissez chaque élément à conserver.' if items else 'Aucun résultat. Essayez un nom plus court ou en anglais ; votre recette reste inchangée.'}


def preview_photo(ident):
    if not re.fullmatch(r'[1-9][0-9]{0,11}', ident):
        raise ImportProblem('Identifiant TheMealDB invalide.')
    meals = request('lookup', {'i': ident})
    meal = next((m for m in meals if str(m.get('idMeal')) == ident), None)
    item = result(meal) if meal else None
    if not item or not item['image_url']:
        raise ImportProblem('Aucune photo compatible pour ce résultat TheMealDB.')
    raw, final = fetch_image(item['image_url'])
    if not image_url(final):
        raise ImportProblem('La photo TheMealDB a changé de source.')
    image = photos.normalize(raw)
    attribution = item['attribution']
    if item['image_origin']:
        attribution = (attribution + ' · ' + item['image_origin'])[:300]
    return {'data_base64': base64.b64encode(image['data']).decode('ascii'), 'source_url': final,
            'attribution': attribution, 'width': image['width'], 'height': image['height']}
