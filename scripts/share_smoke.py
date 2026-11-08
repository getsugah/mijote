"""Check text-only share reception on a fresh, isolated loopback instance."""
import json
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def main():
    base = sys.argv[1].rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.port == 8080 or parsed.path:
        raise SystemExit('Utiliser une instance isolée sur loopback et un port de validation distinct.')
    def initialized():
        with urlopen(base+'/api/v1/auth/status') as response:
            return json.load(response)['initialized']
    assert not initialized(), 'Une instance fraîche est nécessaire ; aucun compte existant utilisé.'
    with urlopen(base+'/manifest.webmanifest') as response:
        target = json.load(response)['share_target']
    assert target['method'] == 'POST' and target['action'] == '/share-recipe'
    body = {'title':'Soupe témoin', 'text':'<script>exemple fictif</script>', 'url':'https://recettes.example/soupe'}
    request = Request(base+target['action'], data=urlencode(body).encode(), headers={'Content-Type':target['enctype']})
    with urlopen(request) as response:
        html = response.read().decode()
        assert response.headers['Cache-Control'] == 'no-store'
        assert response.headers['Referrer-Policy'] == 'no-referrer'
    marker = re.search(r'id="mijote-recipe-share">(.*?)</script>', html).group(1)
    assert json.loads(marker) == body and body['text'] not in html
    asset = re.search(r'src="(/assets/[^\"]+\.js)"', html).group(1)
    with urlopen(base+asset) as response:
        assert 'mijote-recipe-share' in response.read().decode()
    try:
        urlopen(Request(base+target['action'],data=b'',headers={'Content-Type':target['enctype']}))
        raise AssertionError('Un partage vide doit être refusé')
    except HTTPError as error:
        assert error.code == 422
    assert not initialized()
    print('Partage HTTP : manifeste POST, page non cachable, JSON inerte échappé et refus du partage vide validés ; aucune maison initialisée.')


if __name__ == '__main__':
    main()
