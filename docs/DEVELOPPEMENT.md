# Développement

## Prérequis

Python 3.13 et Node ≥ 20.19 (ou Node 22 LTS), avec npm et `python3-venv`.

## Tests et construction

Depuis la racine du projet :

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/pytest backend/tests -q
cd frontend
npm ci
npm run build
```

Les vérifications manuelles (navigateur, Android, impression) sont décrites dans
[RECETTE_MANUELLE.md](RECETTE_MANUELLE.md) ; aucun parcours graphique n’est automatisé.
Les résultats de validation sont consignés dans [VALIDATION.md](../VALIDATION.md).

## Lancer en local

API, depuis la racine du projet :

```sh
MIJOTE_SECURE_COOKIE=false \
MIJOTE_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 \
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Interface, dans un second terminal : `cd frontend && npm run dev`, puis ouvrir
http://localhost:5173 ; Vite transmet `/api` à FastAPI. La base locale est dans `data/`,
exclu de Git.

Les versions directes Python sont dans `backend/requirements.txt`, les dépendances de
production verrouillées dans `backend/requirements-lock.txt`, et les versions frontend
dans `frontend/package-lock.json`.

## Migrations

Les migrations Alembic (`backend/migrations/versions/`) s’appliquent au démarrage.
Elles conservent les données existantes ; par exemple :

- **0006** : alias et liens de fusion d’ingrédients ;
- **0007** : éléments de menu (entrée, plat, dessert) dans des tables dédiées ;
- **0009** : tags de recettes et leurs liens.

Aucun retour de schéma destructif n’est automatisé : pour revenir à une version
antérieure, restaurer une sauvegarde faite avant la mise à jour avec le code correspondant.

## Notices à conserver dans une distribution

Conserver `LICENSE`, `NOTICE`, `COMMERCIAL.md`, `ASSETS.md`,
`THIRD_PARTY_NOTICES.txt` et `THIRD_PARTY_MANIFEST.json` avec les sources. Les copies
dans `frontend/public/legal/` sont reprises par la construction frontend et par l’image
Docker.

Après mise à jour des documents juridiques, depuis la racine du projet :

```sh
python3 scripts/sync_legal.py
python3 scripts/sync_legal.py --check
```

Toute modification de dépendance exige de réexaminer son entrée dans l’inventaire et de
mettre à jour les textes tiers avec ceux de la version réellement distribuée. Le script
de synchronisation ne refait pas cet audit et ne choisit pas de licence pour une nouvelle
dépendance. Le traitement des images utilise [Pillow](https://python-pillow.org/), sous
licence MIT-CMU ; voir [LICENSE_AUDIT.md](LICENSE_AUDIT.md).

L’inventaire concerne les dépendances applicatives auditées. Une publication d’une image
Docker complète doit aussi conserver les notices des composants système et respecter leurs
obligations propres.

## Pistes non planifiées

Ces idées ne sont pas disponibles et ne constituent pas un calendrier :

- lecture de tickets de caisse pour proposer des entrées en stock, avec validation ;
- scan de codes-barres pour faciliter la saisie des achats et des stocks ;
- import depuis une photo ou une capture d’écran (OCR) ;
- import de fichiers de recettes, avec aperçu et contrôle des doublons ;
- proposition d’un menu complet pour les créneaux maison vides, avec validation.

## Annexe : environnement du poste de développement

Note propre au poste utilisé pour développer Mijote, sans valeur de prérequis : Docker
et Compose y ont été installés depuis les dépôts Debian 13 ; le client Docker y est
fourni par le paquet distinct `docker-cli`.
