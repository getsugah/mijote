import gzip
import socket
import time

import pytest

from app import safe_fetch as fetch
from app.safe_fetch import ImportProblem


@pytest.mark.parametrize('url', [
    'file:///etc/passwd', 'ftp://public.example/file', 'https://name:password@public.example/',
    'http://localhost/', 'http://test.local/', 'http://service.internal/', 'https://public.example:8443/',
    'https://public.example/\nheader', 'https://public.example\\@localhost/', 'http://[fe80::1%25eth0]/',
])
def test_invalid_or_local_url_syntax_is_refused(url):
    with pytest.raises(ImportProblem):
        fetch.validate_url(url)


@pytest.mark.parametrize('ip', ['127.0.0.1', '192.168.50.20', '10.1.2.3', '172.16.0.1', '169.254.169.254',
                                '100.64.0.1', '0.0.0.0', '224.0.0.1', '::1', 'fc00::1', 'fe80::1',
                                '::ffff:127.0.0.1', '64:ff9b::a00:1', '2002:7f00:1::'])
def test_private_reserved_multicast_and_tunnel_addresses_are_rejected(ip):
    assert not fetch.public_address(ip)


def test_mixed_public_and_private_dns_is_not_allowed(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, 1, 6, '', ('93.184.216.34', 443)), (socket.AF_INET, 1, 6, '', ('10.0.0.1', 443))])
    with pytest.raises(ImportProblem, match='privée'):
        fetch.resolve_public(fetch.validate_url('https://public.example/'), time.monotonic() + 1)


def test_redirect_back_into_the_household_is_rejected_before_second_connection(monkeypatch):
    visited = []
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, 1, 6, '', ('93.184.216.34', 443))])
    def redirect(target, addresses, deadline):
        visited.append(target.url)
        return 302, 'http://192.168.50.20:8080/api/v1/health', None
    monkeypatch.setattr(fetch, 'request_once', redirect)
    with pytest.raises(ImportProblem):
        fetch.fetch_html('https://public.example/recipe')
    assert len(visited) == 1


def test_every_redirect_is_dns_validated_and_redirects_are_bounded(monkeypatch):
    resolved = []
    def dns(host, *a, **k):
        resolved.append(host)
        return [(socket.AF_INET, 1, 6, '', ('93.184.216.34', 443))]
    monkeypatch.setattr(socket, 'getaddrinfo', dns)
    monkeypatch.setattr(fetch, 'request_once', lambda *args: (302, 'https://next.example/recipe', None))
    with pytest.raises(ImportProblem, match='redirection'):
        fetch.fetch_html('https://public.example/recipe')
    assert len(resolved) == fetch.MAX_REDIRECTS + 1


class FakeSocket:
    def __init__(self):
        self.sent = b''
        self.closed = False
    def settimeout(self, value):
        pass
    def sendall(self, value):
        self.sent += value
    def shutdown(self, how):
        self.closed = True
    def close(self):
        self.closed = True


class FakeResponse:
    status = 200
    def __init__(self, data=b'<html>test</html>', headers=None):
        self.data = data
        self.headers = headers or {'Content-Type': 'text/html'}
    def begin(self):
        pass
    def getheader(self, name, default=None):
        return self.headers.get(name, default)
    def read1(self, size):
        part, self.data = self.data[:size], self.data[size:]
        return part
    def close(self):
        pass


@pytest.mark.parametrize('mime,allowed', [('image/jpeg',True), ('image/png',True), ('image/webp',True), ('text/html',False), ('image/svg+xml',False)])
def test_image_fetch_uses_pinned_transport_and_only_raster_mime(monkeypatch,mime,allowed):
    sock=FakeSocket()
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:sock)
    monkeypatch.setattr(fetch.http.client,'HTTPResponse',lambda *a,**k:FakeResponse(b'photo',{'Content-Type':mime}))
    target=fetch.validate_url('http://images.example/photo')
    if allowed:
        assert fetch.request_once(target,['93.184.216.34'],time.monotonic()+1,image=True)[2]==b'photo'
        assert b'image/jpeg,image/png,image/webp' in sock.sent and b'Cookie:' not in sock.sent
    else:
        with pytest.raises(ImportProblem,match='photo JPEG'):
            fetch.request_once(target,['93.184.216.34'],time.monotonic()+1,image=True)


def test_connection_uses_validated_numeric_ip_but_original_tls_and_host(monkeypatch):
    sock, connected, tls_names = FakeSocket(), [], []
    def connect(address, timeout):
        connected.append(address)
        return sock
    class Context:
        def wrap_socket(self, raw, server_hostname):
            tls_names.append(server_hostname)
            return raw
    monkeypatch.setattr(socket, 'create_connection', connect)
    monkeypatch.setattr(fetch.ssl, 'create_default_context', lambda: Context())
    monkeypatch.setattr(fetch.http.client, 'HTTPResponse', lambda *a, **k: FakeResponse())
    target = fetch.validate_url('https://public.example/recette')
    assert fetch.request_once(target, ['93.184.216.34'], time.monotonic() + 1)[2] == b'<html>test</html>'
    assert connected == [('93.184.216.34', 443)]
    assert tls_names == ['public.example']
    assert b'Host: public.example' in sock.sent and b'Cookie:' not in sock.sent


def test_decompression_bombs_are_bounded():
    data = gzip.compress(b'A' * (fetch.MAX_BYTES + 1))
    response = FakeResponse(data, {'Content-Encoding': 'gzip', 'Content-Length': str(len(data))})
    with pytest.raises(ImportProblem, match='volumineuse'):
        fetch.decode_body(response, FakeSocket(), time.monotonic() + 1)


@pytest.mark.parametrize('status,mime', [(403, 'text/html'), (429, 'text/html'), (200, 'image/jpeg')])
def test_access_controls_and_non_html_content_are_not_bypassed(monkeypatch, status, mime):
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: FakeSocket())
    response = FakeResponse(headers={'Content-Type': mime})
    response.status = status
    def unexpected_read(size):
        raise AssertionError('The rejected response body must not be read')
    response.read1 = unexpected_read
    monkeypatch.setattr(fetch.http.client, 'HTTPResponse', lambda *a, **k: response)
    with pytest.raises(ImportProblem):
        fetch.request_once(fetch.validate_url('http://public.example/'), ['93.184.216.34'], time.monotonic() + 1)


def test_declared_oversize_is_refused_without_reading():
    response = FakeResponse(headers={'Content-Length': str(fetch.MAX_BYTES + 1)})
    with pytest.raises(ImportProblem):
        fetch.decode_body(response, FakeSocket(), time.monotonic() + 1)


def test_slow_response_headers_are_cut_off_by_the_total_deadline(monkeypatch):
    sock = FakeSocket()
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: sock)
    class Slow(FakeResponse):
        def begin(self):
            end = time.monotonic() + 1
            while not sock.closed and time.monotonic() < end:
                time.sleep(.002)
            raise OSError('connection interrupted')
    monkeypatch.setattr(fetch.http.client, 'HTTPResponse', lambda *a, **k: Slow())
    start = time.monotonic()
    with pytest.raises(OSError):
        fetch.request_once(fetch.validate_url('http://public.example/'), ['93.184.216.34'], start + .03)
    assert sock.closed and time.monotonic() - start < .5
