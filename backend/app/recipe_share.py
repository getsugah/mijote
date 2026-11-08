"""Receive text-only shares without persisting them or fetching third-party content."""
import json
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

MAX_BYTES = 256 * 1024
LIMITS = {'title': 300, 'url': 2000, 'text': 60000}


async def receive(request: Request, static: Path):
    if request.headers.get('content-type', '').split(';')[0].lower() != 'application/x-www-form-urlencoded':
        raise HTTPException(415, 'Partager un lien ou un texte ; les fichiers ne sont pas pris en charge.')
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, 'Partage trop volumineux. Utiliser un lien ou un texte plus court.')
        body.extend(chunk)
    try:
        fields = parse_qs(body.decode('utf-8'), keep_blank_values=True, max_num_fields=3, errors='strict')
    except (UnicodeError, ValueError):
        raise HTTPException(422, 'Partage illisible.') from None
    if any(key not in LIMITS or len(values) != 1 or len(values[0]) > LIMITS[key] for key, values in fields.items()):
        raise HTTPException(422, 'Partage invalide ou texte trop long.')
    payload = {name: fields.get(name, [''])[0].strip() for name in LIMITS}
    if not any(payload.values()):
        raise HTTPException(422, 'Le partage ne contient ni lien ni texte.')
    index = static / 'index.html'
    if not index.is_file():
        raise HTTPException(503, 'Interface indisponible. Construire l’application avant de recevoir un partage.')
    # Inert JSON cannot close its script element. Never interpolate unescaped HTML.
    encoded = json.dumps(payload, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    marker = '<script type="application/json" id="mijote-recipe-share">' + encoded + '</script>'
    html = index.read_text().replace('</head>', marker + '</head>', 1)
    return HTMLResponse(html, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})
