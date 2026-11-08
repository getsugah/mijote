"""Bounded raster decoding and metadata-free JPEGs. No personal filenames are stored."""
import base64
import binascii
import hashlib
from io import BytesIO
import threading

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD = 12 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_OUTPUT = 512 * 1024
SLOTS = threading.BoundedSemaphore(2)


def normalize(data):
    if not data or len(data) > MAX_UPLOAD:
        raise HTTPException(413, 'Choisir une photo de 12 Mio maximum.')
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Deux photos sont déjà en traitement. Réessayer dans un instant.')
    try:
        with Image.open(BytesIO(data), formats=['JPEG', 'PNG', 'WEBP']) as original:
            if original.width * original.height > MAX_PIXELS:
                raise HTTPException(422, 'Photo trop grande : 24 mégapixels maximum. Réduire sa taille avant l’envoi.')
            if getattr(original, 'n_frames', 1) != 1:
                raise HTTPException(422, 'Choisir une photo fixe, sans animation.')
            original.load()
            oriented = ImageOps.exif_transpose(original)
            oriented.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            # Paste only pixels into a fresh RGB image: no EXIF/GPS, ICC, XMP or comments.
            clean = Image.new('RGB', oriented.size, 'white')
            rgba = oriented.convert('RGBA')
            clean.paste(rgba, mask=rgba.getchannel('A'))
            for quality in (82, 68, 52):
                output = BytesIO()
                clean.save(output, 'JPEG', quality=quality, optimize=True, exif=b'', icc_profile=None)
                encoded = output.getvalue()
                if len(encoded) <= MAX_OUTPUT:
                    return {'data': encoded, 'digest': hashlib.sha256(encoded).hexdigest(), 'width': clean.width, 'height': clean.height}
                clean.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            raise HTTPException(422, 'Cette photo reste trop volumineuse après compression. Choisir une image plus simple.')
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise HTTPException(422, 'Photo illisible. Utiliser une image JPEG, PNG ou WebP fixe, sans fichier HEIC ou SVG.') from None
    finally:
        SLOTS.release()


def from_draft(draft):
    try:
        raw = base64.b64decode(draft.data_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(422, 'Photo de prévisualisation invalide.') from None
    if len(raw) > MAX_OUTPUT:
        raise HTTPException(422, 'La photo de prévisualisation est trop volumineuse.')
    return normalize(raw)


def save(db, ident, image, source_url='', attribution=''):
    from .services import require
    require(db, 'recipes', ident)
    db.execute('''INSERT INTO recipe_photos (recipe_id,data,digest,width,height,source_url,attribution)
      VALUES (?,?,?,?,?,?,?) ON CONFLICT(recipe_id) DO UPDATE SET data=excluded.data,
      digest=excluded.digest,width=excluded.width,height=excluded.height,
      source_url=excluded.source_url,attribution=excluded.attribution,
      updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')''',
      (ident, image['data'], image['digest'], image['width'], image['height'], source_url, attribution))
    return {'photo_version': image['digest'], 'width': image['width'], 'height': image['height']}
