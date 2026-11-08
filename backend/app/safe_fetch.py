"""Bounded public HTTP fetch with DNS pinning; no cookies, proxies or subresources."""
import http.client
import ipaddress
import queue
import socket
import ssl
import threading
import time
import zlib
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

MAX_BYTES = 3 * 1024 * 1024
MAX_SECONDS = 15
MAX_REDIRECTS = 3
FETCH_SLOTS = threading.BoundedSemaphore(2)
DNS_SLOTS = threading.BoundedSemaphore(2)


class ImportProblem(ValueError):
    pass


@dataclass(frozen=True)
class Target:
    url: str
    scheme: str
    host: str
    port: int
    path: str


def validate_url(value: str) -> Target:
    if len(value) > 2000 or any(ord(c) < 33 or ord(c) == 127 for c in value) or '\\' in value:
        raise ImportProblem('URL invalide. Coller un lien HTTP ou HTTPS public.')
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or '').encode('idna').decode('ascii').rstrip('.').lower()
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    except (ValueError, UnicodeError):
        raise ImportProblem('URL invalide.') from None
    if parsed.scheme not in ('http', 'https') or not host or parsed.username is not None or parsed.password is not None:
        raise ImportProblem('Seules les URL HTTP/HTTPS publiques sans identifiants sont acceptées.')
    if port != (443 if parsed.scheme == 'https' else 80):
        raise ImportProblem('Seuls les ports HTTP et HTTPS standards sont autorisés.')
    if '%' in host or host == 'localhost' or host.endswith(('.localhost', '.local', '.lan', '.internal', '.home', '.onion')):
        raise ImportProblem('Les adresses locales et privées ne sont pas autorisées.')
    authority = f'[{host}]' if ':' in host else host
    path = parsed.path or '/'
    # Encode non-ASCII path/query without changing existing escaped bytes.
    from urllib.parse import quote
    path = quote(path, safe="/%:@!$&'()*+,;=-._~")
    query = quote(parsed.query, safe="%/?@:!$&'()*+,;=-._~")
    normalized = urlunsplit((parsed.scheme, authority, path, query, ''))
    return Target(normalized, parsed.scheme, host, port, path + ('?' + query if query else ''))


def public_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped:
            return public_address(str(address.ipv4_mapped))
        if address.sixtofour or address.teredo:
            return False
        if address in ipaddress.ip_network('64:ff9b::/96'):
            return public_address(str(ipaddress.IPv4Address(int(address) & 0xffffffff)))
    return address.is_global and not address.is_multicast and not address.is_reserved


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise ImportProblem('Le site met trop de temps à répondre. Essayer le collage de texte.')
    return value


def resolve_public(target: Target, deadline) -> list[str]:
    try:
        literal = ipaddress.ip_address(target.host)
    except ValueError:
        literal = None
    if literal:
        addresses = [str(literal)]
    else:
        if '.' not in target.host:
            raise ImportProblem('Un nom de domaine public est nécessaire.')
        if not DNS_SLOTS.acquire(blocking=False):
            raise ImportProblem('Résolution réseau occupée. Réessayer dans quelques instants.')
        results = queue.Queue(maxsize=1)

        def worker():
            try:
                results.put((socket.getaddrinfo(target.host, target.port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP), None))
            except OSError as error:
                results.put((None, error))
            finally:
                DNS_SLOTS.release()

        threading.Thread(target=worker, daemon=True).start()
        try:
            records, error = results.get(timeout=min(5, remaining(deadline)))
        except queue.Empty:
            raise ImportProblem('Le nom du site ne répond pas. Essayer le collage de texte.') from None
        if error:
            raise ImportProblem('Impossible de trouver ce site.')
        addresses = list(dict.fromkeys(record[4][0] for record in records))
    if not addresses or any(not public_address(address) for address in addresses):
        raise ImportProblem('Cette URL pointe vers une adresse privée ou non publique : import refusé.')
    return sorted(addresses, key=lambda value: ':' in value)


def decode_body(response, sock, deadline):
    encoding = response.getheader('Content-Encoding', 'identity').strip().lower()
    if encoding not in ('identity', 'gzip', ''):
        raise ImportProblem('Format de compression non pris en charge. Utiliser le collage de texte.')
    length = response.getheader('Content-Length')
    if length:
        try:
            if int(length) < 0 or int(length) > MAX_BYTES:
                raise ImportProblem('La page est trop volumineuse.')
        except ValueError:
            raise ImportProblem('Taille de réponse invalide.') from None
    inflater = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == 'gzip' else None
    output = bytearray()
    transferred = 0
    while True:
        sock.settimeout(min(5, remaining(deadline)))
        chunk = response.read1(65536)
        if not chunk:
            break
        transferred += len(chunk)
        if transferred > MAX_BYTES:
            raise ImportProblem('La page est trop volumineuse.')
        try:
            decoded = inflater.decompress(chunk, MAX_BYTES + 1 - len(output)) if inflater else chunk
        except zlib.error:
            raise ImportProblem('Réponse compressée invalide.') from None
        output.extend(decoded)
        if len(output) > MAX_BYTES or (inflater and inflater.unconsumed_tail):
            raise ImportProblem('La page décompressée est trop volumineuse.')
    if inflater and not inflater.eof:
        raise ImportProblem('Réponse compressée incomplète.')
    return bytes(output)


def request_once(target: Target, addresses: list[str], deadline, image=False):
    raw = None
    for address in addresses[:4]:
        try:
            # Numeric IP only: no second resolution between validation and connection.
            raw = socket.create_connection((address, target.port), timeout=min(5, remaining(deadline)))
            break
        except OSError:
            continue
    if raw is None:
        raise ImportProblem('Connexion au site impossible. Essayer le collage de texte.')
    connection = http.client.HTTPConnection(target.host, target.port, timeout=min(5, remaining(deadline)))
    timer = None
    response = None
    try:
        raw.settimeout(min(5, remaining(deadline)))
        if target.scheme == 'https':
            raw = ssl.create_default_context().wrap_socket(raw, server_hostname=target.host)
        connection.sock = raw

        def abort():
            try:
                raw.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            raw.close()

        # A hard deadline also bounds slow-drip response headers, not just body reads.
        timer = threading.Timer(remaining(deadline), abort)
        timer.daemon = True
        timer.start()
        connection.request('GET', target.path, headers={
            'User-Agent': 'Mijote/0.2.0 (import de recette a la demande)',
            'Accept': 'image/jpeg,image/png,image/webp' if image else 'text/html,application/xhtml+xml,application/ld+json,application/json',
            'Accept-Encoding': 'identity', 'Connection': 'close',
        })
        # Own the response/socket lifecycle through the bounded read. getresponse()
        # may close HTTPConnection's socket early for Connection: close responses.
        response = http.client.HTTPResponse(raw, method='GET')
        response.begin()
        if response.status in (301, 302, 303, 307, 308):
            return response.status, response.getheader('Location'), None
        if response.status != 200:
            raise ImportProblem(f'Le site refuse l’accès ou ne fournit pas cette page (HTTP {response.status}). Coller le texte de la recette.')
        content_type = response.getheader('Content-Type', '')
        mime = content_type.split(';')[0].strip().lower()
        allowed = ('image/jpeg', 'image/png', 'image/webp') if image else ('text/html', 'application/xhtml+xml', 'application/ld+json', 'application/json')
        if mime not in allowed:
            if image:
                raise ImportProblem('Le site ne fournit pas une photo JPEG, PNG ou WebP.')
            raise ImportProblem('Ce lien ne renvoie pas une page de recette HTML ou JSON.')
        body = decode_body(response, raw, deadline)
        return response.status, content_type, body
    finally:
        if timer:
            timer.cancel()
        if response:
            response.close()
        connection.close()
        raw.close()


def fetch_html(url: str):
    if not FETCH_SLOTS.acquire(blocking=False):
        raise ImportProblem('Deux imports sont déjà en cours. Réessayer dans quelques instants.')
    deadline = time.monotonic() + MAX_SECONDS
    try:
        target = validate_url(url.strip())
        for hop in range(MAX_REDIRECTS + 1):
            addresses = resolve_public(target, deadline)
            status, value, body = request_once(target, addresses, deadline)
            remaining(deadline)
            if status in (301, 302, 303, 307, 308):
                if not value or hop == MAX_REDIRECTS:
                    raise ImportProblem('Trop de redirections ou redirection invalide.')
                target = validate_url(urljoin(target.url, value))
                continue
            import re
            charset = re.search(r'charset\s*=\s*["\x27]?([a-zA-Z0-9_-]+)', value or '', re.I)
            meta_charset = re.search(rb'charset\s*=\s*["\x27]?([a-zA-Z0-9_-]+)', body[:4096], re.I) if not charset else None
            encoding = charset.group(1) if charset else meta_charset.group(1).decode('ascii') if meta_charset else 'utf-8'
            try:
                text = body.decode(encoding, errors='replace')
            except LookupError:
                text = body.decode('utf-8', errors='replace')
            return text, target.url
        raise ImportProblem('Redirection invalide.')
    except ImportProblem:
        raise
    except (OSError, ssl.SSLError, http.client.HTTPException, ValueError, OverflowError):
        raise ImportProblem('Téléchargement impossible ou interrompu. Essayer le collage de texte.') from None
    finally:
        FETCH_SLOTS.release()


def fetch_image(url: str):
    if not FETCH_SLOTS.acquire(blocking=False):
        raise ImportProblem('Deux téléchargements sont déjà en cours. Réessayer dans un instant.')
    deadline = time.monotonic() + MAX_SECONDS
    try:
        target = validate_url(url.strip())
        for hop in range(MAX_REDIRECTS + 1):
            addresses = resolve_public(target, deadline)
            status, value, body = request_once(target, addresses, deadline, image=True)
            remaining(deadline)
            if status in (301, 302, 303, 307, 308):
                if not value or hop == MAX_REDIRECTS:
                    raise ImportProblem('Trop de redirections ou redirection invalide pour la photo.')
                target = validate_url(urljoin(target.url, value))
                continue
            return body, target.url
        raise ImportProblem('Redirection invalide.')
    except ImportProblem:
        raise
    except (OSError, ssl.SSLError, http.client.HTTPException, ValueError, OverflowError):
        raise ImportProblem('Téléchargement de la photo impossible ou interrompu.') from None
    finally:
        FETCH_SLOTS.release()
