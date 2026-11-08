"""Ephemeral links from a public recipe index; no recipe or photo downloads."""
import re
import secrets
import threading
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from .recipe_import import Page, nodes, text
from .safe_fetch import ImportProblem, fetch_html, validate_url

SOURCE = 'Journal des Femmes Cuisine'
INDEX_URL = 'https://cuisine.journaldesfemmes.fr/derniererecette/'
HOST = 'cuisine.journaldesfemmes.fr'
CACHE_SECONDS = 900
_lock = threading.Lock()
_cached: tuple[dict, ...] = ()
_expires = 0.0


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


def discover(excluded: list[str], saved: list[str]) -> dict:
    ignored = {link for value in [*excluded, *saved] if (link := recipe_link(value))}
    candidates = [item for item in catalogue() if item['url'] not in ignored]
    if not candidates:
        return {'item': None, 'message': 'Toutes les idées disponibles ont déjà été vues ou sont dans votre carnet. Vous pouvez revoir les idées.'}
    return {'item': dict(secrets.choice(candidates)), 'message': ''}
