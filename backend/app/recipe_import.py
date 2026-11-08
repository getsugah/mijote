"""Conservative recipe extraction. Returned suggestions never write to the database."""
import html
import json
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html.parser import HTMLParser

from .safe_fetch import ImportProblem, fetch_html, validate_url
from urllib.parse import urljoin


@dataclass
class Node:
    tag: str
    attrs: dict
    children: list = field(default_factory=list)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', {})
        self.stack = [self.root]
        self.count = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.count += 1
        if self.count > 50000 or len(self.stack) > 80:
            raise ImportProblem('Page trop complexe. Utiliser le collage de texte.')
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def nodes(node):
    todo = [node]
    while todo:
        current = todo.pop()
        if isinstance(current, Node):
            yield current
            todo.extend(reversed(current.children))


def text(node, raw=False):
    output, todo = [], [node]
    while todo:
        current = todo.pop()
        if isinstance(current, str):
            output.append(current)
        elif raw or current.tag not in ('script', 'style', 'noscript', 'svg'):
            if not raw and current.tag in ('p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'h4'):
                output.append('\n')
            elif not raw and current.tag in ('span', 'strong', 'em', 'b', 'a', 'label'):
                output.append(' ')
            todo.extend(reversed(current.children))
    if raw:
        return ''.join(output).strip()
    value = html.unescape(''.join(output))
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    return '\n'.join(re.sub(r'\s+', ' ', line).strip() for line in value.splitlines() if line.strip())


def clean(value):
    if not isinstance(value, (str, int, float)):
        return ''
    return text(Page(str(value)).root) if '<' in str(value) else html.unescape(str(value)).strip()


def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def json_nodes(value):
    todo = [value]
    count = 0
    while todo:
        count += 1
        if count > 12000:
            raise ImportProblem('Données structurées trop complexes.')
        item = todo.pop()
        if isinstance(item, dict):
            yield item
            todo.extend(item.values())
        elif isinstance(item, list):
            todo.extend(reversed(item))


def instructions(value, depth=0):
    if depth > 12:
        return []
    if isinstance(value, list):
        return [line for item in value for line in instructions(item, depth + 1)]
    if isinstance(value, dict):
        if 'itemListElement' in value:
            return ([clean(value.get('name'))] if value.get('name') else []) + instructions(value['itemListElement'], depth + 1)
        if 'item' in value:
            return instructions(value['item'], depth + 1)
        return instructions(value.get('text') or value.get('description') or value.get('name', ''), depth + 1)
    return [clean(value)] if clean(value) else []


def ingredient_texts(value, depth=0):
    if depth > 10:
        return []
    if isinstance(value, list):
        return [line for item in value for line in ingredient_texts(item, depth + 1)]
    if isinstance(value, dict):
        if 'itemListElement' in value:
            return ingredient_texts(value['itemListElement'], depth + 1)
        if 'item' in value:
            return ingredient_texts(value['item'], depth + 1)
        name = clean(value.get('name') or value.get('text'))
        amount = clean(value.get('value'))
        unit = clean(value.get('unitText') or value.get('unitCode'))
        unit = {'GRM': 'g', 'KGM': 'kg', 'MLT': 'ml', 'LTR': 'l', 'H87': 'pièce', 'PCE': 'pièce'}.get(unit, unit)
        return [' '.join(x for x in (amount, unit, name) if x)] if name else []
    return [line.strip() for line in clean(value).splitlines() if line.strip()]


def author_text(value, depth=0):
    if depth > 12:
        return ''
    if isinstance(value, list):
        return ', '.join(filter(None, (author_text(x, depth + 1) for x in value)))
    if isinstance(value, dict):
        return clean(value.get('name'))
    return clean(value)


def portions(value, depth=0):
    if depth > 12:
        return None
    if isinstance(value, list):
        # Prefer an explicitly expressed serving count to an unlabeled item count.
        chosen = next((x for x in value if re.search(r'person|portion|serv', str(x), re.I)), value[0] if value else '')
        return portions(chosen, depth + 1)
    if isinstance(value, dict):
        return portions(value.get('value', ''), depth + 1)
    value = clean(value)
    if re.search(r'\d\s*(?:-|à|to)\s*\d|\b(?:makes?|cookies?|pancakes?|crepes?|crêpes?|pieces?|pièces?)\b', value, re.I):
        return None
    numbers = re.findall(r'\d+', value)
    if len(numbers) == 1 and 1 <= int(numbers[0]) <= 30:
        return int(numbers[0])
    return None


def duration(value):
    value = clean(value)
    compact = re.fullmatch(r'(\d+)\s*h\s*(\d{1,2})?', value, re.I)
    if compact:
        hours, minutes = int(compact.group(1)), int(compact.group(2) or 0)
        return hours * 60 + minutes if minutes < 60 and hours * 60 + minutes <= 1440 else None
    match = re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?', value, re.I)
    if match and any(match.groups()):
        d, h, m, sec = [int(x or 0) for x in match.groups()]
        total = d * 1440 + h * 60 + m + (1 if sec else 0)
        return total if total <= 1440 else None
    h = re.search(r'(\d+)\s*(?:h\b|heures?\b|hours?\b)', value, re.I)
    m = re.search(r'(\d+)\s*(?:min(?:utes?)?\b)', value, re.I)
    if h or m:
        result = int(h.group(1)) * 60 if h else 0
        result += int(m.group(1)) if m else 0
        return result if result <= 1440 else None
    return None


def parse_ingredient(raw):
    raw = re.sub(r'^\s*(?:[•*]\s*|-\s+)', '', clean(raw)).strip()[:500]
    result = {'raw': raw, 'name': raw[:120], 'quantity': None, 'unit': None, 'needs_review': True}
    value = re.sub(r'(?<=\d)([¼½¾⅓⅔⅛⅜⅝⅞])', r' \1', raw)
    value = unicodedata.normalize('NFKC', value).replace('⁄', '/')
    approximate = bool(re.match(r'^(?:environ\b|env\.|about\b|approx\.?|≈)', value, re.I))
    value = re.sub(r'^(?:environ\s+|env\.\s*|about\s+|approx\.?\s*|≈\s*)', '', value, flags=re.I)
    match = re.match(r'^(\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:[.,]\d+)?)\s*(.*)$', value)
    if not match:
        return result
    number, rest = match.groups()
    if re.match(r'^(?:à|to|[-–])\s*\d', rest, re.I):
        return result
    try:
        if '/' in number:
            mixed = re.fullmatch(r'(\d+)\s+(\d+)\s*/\s*(\d+)', number)
            if mixed:
                whole, numerator, denominator = mixed.groups()
                q = Decimal(whole) + Decimal(numerator) / Decimal(denominator)
            else:
                numerator, denominator = number.replace(' ', '').split('/')
                q = Decimal(numerator) / Decimal(denominator)
        else:
            q = Decimal(number.replace(',', '.'))
    except (InvalidOperation, ZeroDivisionError):
        return result
    unit_match = re.match(r'^(kilogrammes?|kilograms?|kg|grammes?|grams?|gr|g|millilitres?|milliliters?|ml|centilitres?|cl|décilitres?|decilitres?|dl|litres?|liters?|l|pièces?|pieces?|unités?|unites?)\b\s*(.*)$', rest, re.I)
    if unit_match:
        unit_text, name = unit_match.groups()
        key = folded(unit_text)
        if key.startswith(('kilogram', 'kg')):
            unit = 'kg'
        elif key.startswith(('gram', 'gr')) or key == 'g':
            unit = 'g'
        elif key.startswith(('millil', 'ml')):
            unit = 'ml'
        elif key.startswith(('centil', 'cl')):
            unit, q = 'ml', q * 10
        elif key.startswith(('decil', 'dl')):
            unit, q = 'ml', q * 100
        elif key.startswith(('lit', 'l')):
            unit = 'l'
        else:
            unit = 'piece'
        name = re.sub(r'^(?:de\s+|d[’\x27]\s*)', '', name, flags=re.I)
    elif re.match(r'^(?:(?:gros|grosse|grosses|petits?|petites?|large|medium|small)\s+)?(?:œufs?|oeufs?|eggs?|oignons?|onions?|tomates?|tomatoes|carottes?|carrots?|courgettes?|aubergines?|citrons?|lemons?|gousses?|filets?|pommes?\b|poireaux?|poivrons?|bananes?|bananas?)\b', rest, re.I):
        unit, name = 'piece', rest
    else:
        return result
    if q <= 0 or q >= Decimal('1000000000'):
        return result
    rounded = q.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    if not name or q <= 0 or rounded <= 0 or rounded >= Decimal('1000000000'):
        return result
    result.update(name=clean(name)[:120], quantity=float(rounded), unit=unit,
                  needs_review=approximate or q != rounded)
    return result


def property_nodes(root, key):
    return [n for n in nodes(root) if key in (n.attrs.get('itemprop') or '').split()]


def by_heading(root, wanted):
    for parent in nodes(root):
        siblings = parent.children
        for index, heading in enumerate(siblings):
            if not isinstance(heading, Node) or heading.tag not in ('h2', 'h3', 'h4'):
                continue
            if not re.search(wanted, folded(text(heading))):
                continue
            found = []
            for sibling in siblings[index + 1:]:
                if isinstance(sibling, Node) and sibling.tag in ('h1', 'h2', 'h3', 'h4'):
                    break
                if not isinstance(sibling, Node):
                    continue
                leaves = [n for n in nodes(sibling) if n.tag == 'li']
                if not leaves:
                    leaves = [n for n in nodes(sibling) if n.tag == 'p']
                if leaves:
                    found.extend(text(n) for n in leaves)
                elif text(sibling):
                    found.extend(text(sibling).splitlines())
            if found:
                return found
    return []


def generic(page):
    root = next((n for n in nodes(page.root) if '/Recipe' in n.attrs.get('itemtype', '')), None)
    root = root or next((n for n in nodes(page.root) if n.tag == 'main'), page.root)
    title_nodes = property_nodes(root, 'name')
    headings = [n for n in nodes(root) if n.tag == 'h1']
    name = text(title_nodes[0]) if title_nodes else text(headings[0]) if headings else ''
    ingredients = [text(n) for n in property_nodes(root, 'recipeIngredient')]
    if not ingredients:
        for node in nodes(root):
            marker = folded((node.attrs.get('class') or '') + ' ' + (node.attrs.get('id') or ''))
            if 'ingredient' in marker:
                lines = [n for n in nodes(node) if n.tag == 'li']
                if lines:
                    ingredients = [text(n) for n in lines]
                    break
        ingredients = ingredients or by_heading(root, r'ingredients?')
    steps = [text(n) for n in property_nodes(root, 'recipeInstructions')]
    if not steps:
        for node in nodes(root):
            marker = folded((node.attrs.get('class') or '') + ' ' + (node.attrs.get('id') or ''))
            if re.search(r'instructions?|recipe-steps|preparation|method', marker):
                lines = [n for n in nodes(node) if n.tag in ('li', 'p')]
                if lines:
                    steps = [text(n) for n in lines]
                    break
        steps = steps or by_heading(root, r'preparation|instructions?|method|etapes')
    metadata = {n.attrs.get('property') or n.attrs.get('name'): n.attrs.get('content', '') for n in nodes(page.root) if n.tag == 'meta'}
    yields = property_nodes(root, 'recipeYield')
    total = property_nodes(root, 'totalTime')
    return {'name': name or metadata.get('og:title', ''), 'recipeIngredient': ingredients,
            'recipeInstructions': steps, 'recipeYield': text(yields[0]) if yields else '',
            'totalTime': (total[0].attrs.get('datetime') or text(total[0])) if total else '',
            'author': metadata.get('author', ''),
            'image': metadata.get('og:image') or metadata.get('twitter:image', '')}


def image_info(value, source_url, depth=0):
    if depth > 8:
        return '', ''
    if isinstance(value, list):
        for item in value[:20]:
            url, credit = image_info(item, source_url, depth + 1)
            if url:
                return url, credit
        return '', ''
    if isinstance(value, dict):
        url, _ = image_info(value.get('contentUrl') or value.get('url', ''), source_url, depth + 1)
        credit = author_text(value.get('author') or value.get('copyrightHolder')) or clean(value.get('creditText') or value.get('copyrightNotice'))
        return url, credit[:300]
    if isinstance(value, str) and value.strip() and source_url:
        try:
            return validate_url(urljoin(source_url, value.strip())).url, ''
        except ImportProblem:
            pass
    return '', ''


def finalize(recipe, source_url, method, extra_warnings=()):
    warnings = list(extra_warnings)
    original_lines = ingredient_texts(recipe.get('recipeIngredient') or recipe.get('ingredients', []))
    steps = '\n\n'.join(instructions(recipe.get('recipeInstructions', '')))
    name = clean(recipe.get('name'))
    if not name and not original_lines and not steps:
        raise ImportProblem('Aucune recette exploitable détectée. Coller le texte puis vérifier les champs.')
    if not original_lines and not steps:
        raise ImportProblem('La page ne contient pas de recette lisible. Elle peut être protégée ; utiliser le collage de texte.')
    if len(original_lines) > 100:
        warnings.append('Seules les 100 premières lignes d’ingrédients sont proposées.')
    lines = [parse_ingredient(line) for line in original_lines[:100] if line.strip()]
    if any(line['needs_review'] for line in lines):
        warnings.append('Certaines quantités ou unités ne sont pas reconnues. Elles restent dans le texte d’origine ; vérifier avant de les inclure dans les besoins.')
    servings = portions(recipe.get('recipeYield', ''))
    if servings is None:
        warnings.append('Le nombre de portions doit être vérifié et renseigné.')
    minutes = duration(recipe.get('totalTime', ''))
    if minutes is None:
        prep, cook = duration(recipe.get('prepTime', '')), duration(recipe.get('cookTime', ''))
        minutes = (prep or 0) + (cook or 0) if prep is not None or cook is not None else None
        if minutes is not None and minutes > 1440:
            minutes = None
    if minutes is None:
        warnings.append('Durée non reconnue ; saisir 0 si elle n’est pas connue.')
    if not steps:
        warnings.append('Étapes non reconnues : les compléter dans la prévisualisation.')
    if len(name) > 120 or len(steps) > 20000 or len('\n'.join(original_lines)) > 12000:
        warnings.append('Certains textes ont été raccourcis aux limites du formulaire.')
    image_url, image_author = image_info(recipe.get('image'), source_url)
    return {'name': name[:120], 'portions': servings, 'yield_text': clean(recipe.get('recipeYield', ''))[:200],
            'minutes': minutes, 'steps': steps[:20000], 'source_url': source_url,
            'source_author': author_text(recipe.get('author', ''))[:300],
            'ingredient_notes': '\n'.join(original_lines)[:12000], 'ingredients': lines,
            'warnings': warnings, 'method': method, 'image_url': image_url,
            'image_author': image_author or author_text(recipe.get('author', ''))[:300]}


def parse_html(source, source_url):
    page = Page(source)
    candidates = []
    for script in [n for n in nodes(page.root) if n.tag == 'script' and (n.attrs.get('type') or '').lower().split(';')[0] == 'application/ld+json'][:64]:
        raw = text(script, raw=True)
        try:
            value = json.loads(raw)
        except (ValueError, RecursionError):
            continue
        for item in json_nodes(value):
            kind = item.get('@type', [])
            types = kind if isinstance(kind, list) else [kind]
            if any(isinstance(t, str) and t.rstrip('/').rsplit('/', 1)[-1].rsplit('#', 1)[-1].casefold() == 'recipe' for t in types):
                if item.get('recipeIngredient') or item.get('recipeInstructions'):
                    candidates.append(item)
    if candidates:
        chosen = max(candidates, key=lambda item: len(ingredient_texts(item.get('recipeIngredient', []))) + len(instructions(item.get('recipeInstructions', []))))
        warning = ['Plusieurs recettes ont été détectées : vérifier le titre et le contenu proposés.'] if len(candidates) > 1 else []
        if not chosen.get('image'):
            metadata = {n.attrs.get('property'): n.attrs.get('content', '') for n in nodes(page.root) if n.tag == 'meta'}
            chosen = {**chosen, 'image': metadata.get('og:image', '')}
        return finalize(chosen, source_url, 'jsonld', warning)
    stripped = source.lstrip('\ufeff \r\n\t')
    if stripped.startswith(('{', '[')):
        try:
            for item in json_nodes(json.loads(stripped)):
                if item.get('@type') == 'Recipe':
                    return finalize(item, source_url, 'jsonld')
        except (ValueError, RecursionError):
            pass
    return finalize(generic(page), source_url, 'html', ['Extraction HTML générique : vérifier chaque champ.'])


def parse_text(source, source_url=''):
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines:
        raise ImportProblem('Coller le texte de la recette.')
    begins_with_section = bool(re.fullmatch(r'ingredients?\s*:?', folded(lines[0])))
    title, ingredients, steps, section, yield_text = '' if begins_with_section else lines[0], [], [], '', ''
    for line in lines if begins_with_section else lines[1:]:
        value = folded(line).strip(' :')
        if re.fullmatch(r'ingredients?(?:\s+.*)?', value):
            section = 'ingredients'
        elif re.fullmatch(r'(?:preparation|instructions?|etapes|method)(?:\s+.*)?', value):
            section = 'steps'
        elif re.match(r'^(?:pour\s+)?\d+\s+(?:personnes?|portions?|servings?)\b', value):
            yield_text = line
        elif section == 'ingredients':
            ingredients.append(line)
        else:
            steps.append(line)
    return finalize({'name': title, 'recipeIngredient': ingredients, 'recipeInstructions': steps,
                     'recipeYield': yield_text}, source_url, 'text', ['Texte collé : vérifier les champs et les portions.'])


def preview(mode, url='', source=''):
    if mode == 'text':
        return parse_text(source, url)
    body, final_url = fetch_html(url)
    return parse_html(body, final_url)
