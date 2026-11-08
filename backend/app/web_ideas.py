"""Ephemeral links from a public recipe index; no recipe or photo downloads."""
import re
import json
from collections import OrderedDict
import secrets
import threading
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from .recipe_import import Page, nodes, text, clean, json_nodes
from .safe_fetch import ImportProblem, fetch_html, validate_url

SOURCE = 'Journal des Femmes Cuisine'
INDEX_URL = 'https://cuisine.journaldesfemmes.fr/derniererecette/'
HOST = 'cuisine.journaldesfemmes.fr'
CACHE_SECONDS = 900
_lock = threading.Lock()
_cached: tuple[dict, ...] = ()
_expires = 0.0
_custom_cache: OrderedDict = OrderedDict()
MAX_SOURCES = 20


def recipe_link(value: str) -> str | None:
    try:
        target = validate_url(value)
    except ImportProblem:
        return None
    parsed = urlsplit(target.url)
    if target.scheme != 'https' or target.host != HOST or not re.fullmatch(r'/recette/[0-9]+-[^/]+/?', parsed.path):
        return None
    return urlunsplit(('https', HOST, parsed.path.rstrip('/'), '', ''))


def parse_index(html: str, final_url: str) -> tuple[dict, ...]:
    target = validate_url(final_url)
    if target.scheme != 'https' or target.host != HOST:
        raise ImportProblem('La source de découvertes a changé d’adresse. Réessayer plus tard.')
    found = {}
    for node in nodes(Page(html).root):
        if node.tag != 'a':
            continue
        url = recipe_link(urljoin(target.url, node.attrs.get('href', '')))
        if not url or url in found:
            continue
        name = ' '.join(text(node).split())
        if not name or len(name) > 300:
            continue
        found[url] = {'name': name, 'url': url, 'source': SOURCE}
        if len(found) >= 100:
            break
    if not found:
        raise ImportProblem('Aucune idée web disponible actuellement. Votre carnet reste accessible.')
    return tuple(found.values())


def normalized_link(value: str) -> str | None:
    try:
        target = validate_url(value)
    except ImportProblem:
        return None
    parsed = urlsplit(target.url)
    # Keep meaningful queries, but discard fragments and common tracking fields.
    from urllib.parse import parse_qsl, urlencode
    query = urlencode([(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                       if not k.lower().startswith('utm_') and k.lower() not in ('fbclid', 'gclid')])
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip('/') or '/', query, ''))


def parse_source(html: str, final_url: str) -> tuple[dict, ...]:
    target = validate_url(final_url)
    page = Page(html)
    found = {}

    def add(name, value):
        if not isinstance(value, str) or not value.strip():
            return
        try:
            url = normalized_link(urljoin(target.url, value))
        except ValueError:
            return
        if not url or urlsplit(url).hostname != target.host:
            return
        name = ' '.join(clean(name).split())
        if name and len(name) <= 300 and len(found) < 100:
            found.setdefault(url, {'name': name, 'url': url, 'source': target.host})

    for node in nodes(page.root):
        if node.tag == 'script' and (node.attrs.get('type') or '').split(';')[0].strip().lower() == 'application/ld+json':
            try:
                data = json.loads(text(node, raw=True))
            except (ValueError, RecursionError):
                continue
            for item in json_nodes(data):
                types = item.get('@type', [])
                types = [types] if isinstance(types, str) else types
                if not isinstance(types, list):
                    continue
                if 'Recipe' in types:
                    add(item.get('name', ''), item.get('url') or final_url)
                if 'ItemList' in types:
                    entries = item.get('itemListElement', [])
                    if not isinstance(entries, list):
                        continue
                    for entry in entries[:100]:
                        if not isinstance(entry, dict):
                            continue
                        value = entry.get('item', entry)
                        if isinstance(value, dict):
                            add(value.get('name') or entry.get('name', ''), value.get('url', ''))
                        elif isinstance(value, str):
                            add(entry.get('name', ''), value)
        elif node.tag == 'a':
            href = node.attrs.get('href', '')
            try:
                path = urlsplit(urljoin(target.url, href)).path
            except ValueError:
                continue
            # Recognizable recipe routes, rather than arbitrary navigation links.
            if re.fullmatch(r'/(?:.*\/)?recettes?/[^/]*[0-9][^/]*', path) or re.fullmatch(r'/[^/]+-r[0-9]+\.htm', path) or re.fullmatch(r'/recipes/(?!collection/?$|search/?$|category/?$)[^/]+/?', path):
                add(text(node), href)
    if not found:
        raise ImportProblem('Aucune recette reconnue sur cette page. Essayez une page de recettes ou une autre source ; certains sites ne sont pas compatibles.')
    return tuple(found.values())


def source_catalogue(url: str) -> tuple[dict, ...]:
    if not _lock.acquire(blocking=False):
        raise ImportProblem('La recherche web est déjà en cours. Réessayer dans quelques instants.')
    try:
        cached = _custom_cache.get(url)
        if cached and time.monotonic() < cached[0]:
            _custom_cache.move_to_end(url)
            return cached[1]
        html, final_url = fetch_html(url)
        items = parse_source(html, final_url)
        _custom_cache[url] = (time.monotonic() + CACHE_SECONDS, items)
        _custom_cache.move_to_end(url)
        while len(_custom_cache) > MAX_SOURCES:
            _custom_cache.popitem(last=False)
        return items
    finally:
        _lock.release()


def catalogue() -> tuple[dict, ...]:
    global _cached, _expires
    # One fetch at a time; a busy source never queues unbounded requests.
    if not _lock.acquire(blocking=False):
        raise ImportProblem('La recherche web est déjà en cours. Réessayer dans quelques instants.')
    try:
        if _cached and time.monotonic() < _expires:
            return _cached
        html, final_url = fetch_html(INDEX_URL)
        _cached = parse_index(html, final_url)
        _expires = time.monotonic() + CACHE_SECONDS
        return _cached
    finally:
        _lock.release()


def discover(excluded: list[str], saved: list[str], source_url: str | None = None) -> dict:
    normalize = normalized_link if source_url else recipe_link
    ignored = {link for value in [*excluded, *saved] if (link := normalize(value))}
    items = source_catalogue(source_url) if source_url else catalogue()
    candidates = [item for item in items if normalize(item['url']) not in ignored]
    if not candidates:
        return {'item': None, 'message': 'Toutes les idées disponibles ont déjà été vues ou sont dans votre carnet. Vous pouvez revoir les idées.'}
    return {'item': dict(secrets.choice(candidates)), 'message': ''}
