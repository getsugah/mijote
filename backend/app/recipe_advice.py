"""Deterministic, reviewable recipe labels. Preview never writes or fetches URLs."""
import re
import unicodedata


def name_key(value):
    return unicodedata.normalize('NFKC', value).casefold()


def normalized_tags(values):
    result, seen = [], set()
    for value in values:
        value = ' '.join(unicodedata.normalize('NFKC', value).split())
        if not value or len(value) > 50:
            raise ValueError('Un tag doit contenir entre 1 et 50 caractères.')
        key = name_key(value)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def save_tags(db, recipe_id, values):
    db.execute('DELETE FROM recipe_tags WHERE recipe_id=?', (recipe_id,))
    for value in values:
        db.execute('INSERT OR IGNORE INTO tags(name,name_key) VALUES (?,?)', (value, name_key(value)))
        ident = db.execute('SELECT id FROM tags WHERE name_key=?', (name_key(value),)).fetchone()['id']
        db.execute('INSERT INTO recipe_tags(recipe_id,tag_id) VALUES (?,?)', (recipe_id, ident))


def tags_by_recipe(db):
    result = {}
    for row in db.execute('SELECT rt.recipe_id,t.name FROM recipe_tags rt JOIN tags t ON t.id=rt.tag_id ORDER BY t.name COLLATE NOCASE'):
        result.setdefault(row['recipe_id'], []).append(row['name'])
    return result


def plain(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


RULES = [
    ('Poulet', r'\b(?:poulet|poulets|poulette|volaille)\b'),
    ('Bœuf', r'\b(?:boeuf|bœuf|steak|bourguignon)\b'),
    ('Porc', r'\b(?:porc|lardon|lardons|jambon)\b'),
    ('Poisson', r'\b(?:poisson|saumon|thon|cabillaud|truite)\b'),
    ('Œufs', r'\b(?:oeuf|oeufs|œuf|œufs|omelette)\b'),
    ('Légumineuses', r'\b(?:lentilles?|pois chiches?|haricots secs?)\b'),
    ('Riz', r'\b(?:riz|risotto)\b'),
    ('Pâtes', r'\b(?:pates|spaghettis?|tagliatelles?|lasagnes?|penne|macaronis?)\b'),
    ('Pommes de terre', r'\bpommes? de terre\b'),
    ('Courgettes', r'\bcourgettes?\b'),
    ('Tomates', r'\btomates?\b'),
    ('Soupe', r'\b(?:soupe|potage|veloute)\b'),
    ('Salade', r'\bsalade\b'),
    ('Gratin', r'\bgratin\b'),
    ('Tarte', r'\b(?:tarte|quiche)\b'),
    ('Pizza', r'\bpizza\b'),
    ('Dessert', r'\b(?:dessert|gateau|cookies?|mousse au chocolat|crepes?|tiramisu|clafoutis|compote)\b'),
]


def propose(data):
    title = ' '.join(data.name.split())
    if title:
        title = title[0].upper() + (title[1:].lower() if title.isupper() else title[1:])
        title_reason = 'Présentation du titre saisi, à vérifier.'
    elif data.ingredients:
        title = 'Recette : ' + ', '.join(data.ingredients[:2])
        title_reason = 'Intitulé descriptif à partir des ingrédients fournis.'
    else:
        title = ''
        title_reason = 'Saisissez un titre ou des ingrédients pour obtenir une proposition.'
    text = plain(' '.join([data.name, *data.ingredients]))
    tags = [{'name': label, 'reason': 'Mot repéré dans le titre ou les ingrédients.'} for label, pattern in RULES if re.search(pattern, text)]
    if 0 < data.minutes <= 30:
        tags.append({'name': 'Rapide', 'reason': 'Temps renseigné inférieur ou égal à 30 minutes.'})
    return {'title': title[:120], 'title_reason': title_reason, 'tags': tags[:20],
            'message': 'Propositions à vérifier. Aucune garantie sur les allergènes ou les régimes alimentaires.'}
