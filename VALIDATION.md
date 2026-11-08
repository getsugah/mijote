# Validation — Mijote 0.1.0, phase A

Environnement : Debian 13, Python 3.13.5, Node 20.19.2, Docker 26.1.5 et Compose
2.26.1. Développement dans un nouveau dossier isolé, cahier des charges lu
intégralement avant le plan et l’implémentation. Autres projets préservés.

## Contrôles réussis

| Contrôle | Résultat |
| --- | --- |
| `pytest backend/tests -q` | 22 tests réussis |
| `npm run build` | TypeScript et Vite 7.3.7 réussis |
| `npm audit --json` | 0 vulnérabilité signalée, dépendances de développement comprises |
| `pip check` | Aucune incompatibilité de dépendance |
| `docker compose config --quiet` | Configuration valide |
| `docker compose build` | Image `mijote:0.1.0` construite, environ 165 Mo |
| Démarrage Compose `--wait` | Service sain, utilisateur non privilégié, port de test limité à localhost |
| `scripts/smoke.py --scenario` | Parcours familial HTTP réussi sur l’image finale |
| Redémarrage et contrôle HTTP | Données conservées, frontend, manifeste, icônes et authentification accessibles |
| Sauvegarde en fonctionnement | Flux SQLite valide, intégrité et état métier vérifiés |
| Restauration pendant fonctionnement | Refus attendu par verrou |
| Restauration après arrêt | Réussie, ancienne base conservée, service redémarré sain |

Image finale vérifiée :
`sha256:e3eef200ef07c95fe5b1d1d9cdfab131f397f7a5c45284e59f2c384748475413`.

Le scénario HTTP initialise uniquement une maison de test neuve. Il définit un
midi travaillé, crée ingrédients/recette/stock, passe le repas maison, vérifie
150 g manquants, coche sans modifier le stock, confirme les achats deux fois,
puis la préparation deux fois. Le stock et les mouvements ne sont jamais doublés.
Le modèle est applicable à une semaine vide mais refusé après planification.

Les tests couvrent aussi les portions, conversions d’unités et leur incompatibilité,
accompagnements, petites quantités, réservation entre repas et entre semaines,
libération des besoins, recettes sans ingrédients, pénuries non bloquantes,
quantités corrigées, substitutions, articles manuels, atomicité des achats,
réutilisation invalide d’un identifiant, confirmations simultanées, conservation
des références, migrations au redémarrage, hachage/session/CSRF/origines et limites
de connexion. Le journal distingue les mouvements de chaque lot consommé.

## Limites de vérification

- Aucun clic, parcours graphique ou navigateur automatisé. La recette Chrome sur
  Debian/GNOME et Android reste à effectuer : docs/RECETTE_MANUELLE.md.
- L’installation PWA via un vrai domaine HTTPS et l’accès distant derrière le proxy
  ou VPN de l’utilisateur ne sont pas testés ici. Les fichiers PWA sont servis.
- Un avertissement de dépréciation du client de test Starlette concernant `httpx`
  est émis ; les tests passent et ce client n’est pas inclus dans l’image de production.
- L’absence d’alerte npm n’est pas une certification de sécurité. Aucun audit
  d’intrusion ni test de charge n’est revendiqué.
- Fonctions B/C explicitement différées, notamment courses hors ligne et import URL.

## Environnement laissé en place

L’image et les dépendances sont réutilisables. Les trois instances de validation
ont été arrêtées ; leurs volumes de test sont conservés, distincts du volume de
la maison réelle. La sauvegarde de test privée se trouve dans `/tmp` avec des
droits restreints. Aucun service Mijote réel n’a été initialisé : le premier
lancement normal présentera l’écran de création du compte familial.

Démarrage : `docker compose up -d`, puis http://localhost:8080. Utiliser `sudo`
pour Docker si le compte n’a pas l’accès au démon. Aucun push ni publication.

## Mise à jour 0.1.1 — calendrier et impression

- `npm test` : 7 tests réussis. Dates officielles 2026, fêtes mobiles 2027/2024,
  changement d’année, statuts hors maison et rendu réel du composant imprimable
  (7 jours, 14 cellules, jours fériés, portions et accompagnement, aucun formulaire).
- `npm run build` : TypeScript et Vite réussis ; aucune dépendance ajoutée.
- `pytest backend/tests -q` : 22 tests réussis ; même avertissement du client de test.
- Image construite : `mijote:0.1.1`,
  `sha256:159329dc8c52951400ea1ee5358cefe418e8f8cb345d4f6e6f753a21f3474723`.
- Pas de migration de schéma ni de modification automatique des repas ou des stocks.
- La mise en page A4 est contrôlée par CSS et le contenu est testé par rendu
  serveur du composant, sans navigateur. L’aperçu Chrome/PDF et l’impression
  physique restent à vérifier manuellement.

- Image 0.1.1 démarrée et vérifiée sur conteneur de test isolé, arrêté ensuite.
- Mise à jour familiale appliquée après sauvegarde dans `backups/` (fichier privé).
- Même volume conservé, compte familial présent, intégrité SQLite et clés étrangères vérifiées après remplacement du conteneur. Nouveaux fichiers servis sur l’adresse LAN.

## Mise à jour 0.2.0 — import URL et collage

- 80 tests backend réussis, avec le même avertissement de dépréciation du client de test.
- 7 tests frontend réussis ; compilation Vue/TypeScript/Vite réussie. Aucune dépendance ajoutée.
- Protections testées : URL/protocoles/ports, IP privées et métadonnées, DNS mixte,
  redirections revalidées, connexion sur IP publique validée avec SNI/Host d’origine,
  compression excessive, limite de taille, coupure des en-têtes trop lents,
  refus des réponses protégées et contenus non HTML/JSON.
- Parseurs testés : JSON-LD graphes/listes/sections, microdonnées, HTML générique,
  collage manuel, fractions et unités métriques, ambiguïtés, portions en personnes
  ou en pièces et conservation des ingrédients non quantifiés.
- Fonctionnement testé : prévisualisation authentifiée sans écriture et sans verrou
  SQLite conservé pendant le réseau, confirmation atomique/idempotente sans stock,
  annulation complète sur unité invalide, distinctions culinaires conservées,
  métadonnées préservées avec un ancien client et migration 0001 → 0002 sans perte.
- Essais publics réussis : Marmiton (12 lignes, JSON-LD), Good Food (6 lignes,
  JSON-LD, nombre de pièces non assimilé à des personnes), 750g (6 lignes, HTML).
  Aucun contenu tiers de ces pages n’est enregistré dans les sources du projet.
- Parcours HTTP Docker isolé : prévisualisation Marmiton/750g sans écrire en base,
  puis collage et enregistrement d’une recette synthétique, confirmation rejouée
  sans doublon, attribution conservée, aucun mouvement de stock et URL locale refusée.
- Image `mijote:0.2.0` :
  `sha256:40f3dd15dc45a36c1419815fe35c861bb60799c2132545883327064644a5f90a`.
- L’instance de validation est arrêtée et son volume conservé. La recette visuelle
  de la fenêtre d’import reste manuelle ; les blocages de sites tiers peuvent varier.

- Déploiement familial 0.2.0 réalisé après sauvegarde SQLite cohérente et privée dans `backups/`. Même volume et compte conservés, migration 0002, intégrité et clés étrangères vérifiées. Nouveaux fichiers servis via le LAN ; accès à l’aperçu sans session refusé.

## Mise à jour 0.3.0 — phase B

- 91 tests backend réussis : préférences, historique réel et curseur, copie avec
  aperçu périmé refusé, réutilisation sans débit, suggestions déterministes,
  synchronisation partielle/idempotente et conflits. Migration 0002 vers 0003
  testée sur une base synthétique avec préparation existante et sans date inventée.
- 19 tests frontend réussis : calendrier/impression préservés, rendu des avis et
  échappement des notes, cache public sans API, persistance IndexedDB, regroupement
  d’opérations non envoyées, reprise après perte de réponse, conflits, protection
  des maisons/semaines et des onglets ayant une copie ancienne.
- Compilation Vue/TypeScript/Vite et image Docker réussies. Seule dépendance ajoutée :
  fake-indexeddb 6.2.7, réservée aux tests ; aucune dépendance de production ajoutée.
- Image finale : `mijote:0.3.0`, `sha256:9c433320a0d820c73a6e1246a854d2a53cb134bc33f1436e07e6ecc9eabecbf2`.
- Parcours HTTP isolé réussi : avis, préparation réelle, quatre modes de suggestion,
  copie protégée, UUID rejoué et conflit de courses ; aucune entrée ni déduction
  de stock par la synchronisation. Instance de validation arrêtée, volume conservé.
- Contrôle des fichiers distribuables réussi : aucun chemin utilisateur personnel
  ni adresse IPv4 privée détecté hors fixtures réseau fictives. Les nouveaux fichiers
  JavaScript servis ont aussi été contrôlés pour les chemins utilisateurs.
- Mise à jour familiale effectuée après sauvegarde privée 0600 vérifiée. Même
  volume, compte inchangé contrôlé par empreinte sans en afficher le contenu,
  schéma 0003, intégrité SQLite et clés étrangères correctes, préparations anciennes
  reprises. API, nouveaux écrans servis sur le LAN et santé Docker vérifiés.
- Avertissement de dépréciation du client de test Starlette déjà présent, sans échec.
- Aucun push ni publication. Les données réelles ne servent pas de fixtures.

À vérifier manuellement : ergonomie Android, aperçu d’impression, interruption
réseau réelle et réouverture PWA sur une origine HTTPS. Sur HTTP LAN, conserver
l’onglet chargé pour les courses hors connexion. La politique de conflits est dans
[docs/COURSES_HORS_LIGNE.md](docs/COURSES_HORS_LIGNE.md).

## Mise à jour 0.3.1 — largeur mobile

- Cause identifiée par lecture CSS : le menu fixe cumulait 100 % de largeur et
  dix pixels de padding, à cause de box-sizing:content-box.
- Menu en border-box, navigation répartie dans la largeur, contenu pouvant rétrécir
  et espace inférieur calculé avec la zone système. Hauteur dynamique de fenêtre,
  viewport-fit=cover et absence d’effet de survol au toucher.
- Fichiers concernés : frontend/src/style.css, frontend/index.html, métadonnées de
  version frontend/backend/Compose et journal. Aucune règle métier modifiée.
- Compilation TypeScript/Vite et image Docker 0.3.1 réussies. Démarrage isolé,
  API et règles CSS réellement servies contrôlés. Aucun navigateur automatisé,
  aucun nouveau test métier nécessaire pour cette correction de présentation.
- Image finale : `sha256:71839f10cde89e5019ad3149e326ceae3758842ac188b21ea2298c0bfbc21c99`.
- Déploiement après sauvegarde privée 0600 vérifiée ; même volume, compte inchangé,
  intégrité et clés étrangères correctes, schéma 0003 inchangé. CSS corrigé servi
  sur l’instance familiale. Conteneur de test arrêté, volume préservé.
- Le résultat visuel et le défilement restent à confirmer sur le téléphone utilisé.

## Mise à jour 0.4.0 — réception de partage Android/PWA

- 101 tests backend réussis : dix nouveaux contrôles de réception POST sans compte,
  sans écriture et sans fetch automatique ; échappement du JSON inerte, limites des
  champs et du flux sans Content-Length, refus des fichiers et encodages invalides.
- 28 tests frontend réussis : extraction des URL dans titre/texte, liens multiples,
  rejet des protocoles dangereux, absence de troncature, consommation unique du
  marqueur, préremplissage réel du formulaire par rendu serveur, cache excluant le
  partage. Les validations précédentes du calendrier et des courses passent aussi.
- TypeScript/Vite et image Docker réussis, aucune dépendance ajoutée, schéma 0003
  inchangé. Image : `sha256:4d76387b9c94fb188b2c2203151489df0e2a08a9da3ecbe6ec9f081f4e43eaa0`.
- Parcours HTTP sur instance fraîche isolée réussi : manifeste POST, HTML non
  cachable, JSON échappé, refus du partage vide, aucune maison initialisée. Instance
  de test arrêtée, volume conservé. Aucune recette réelle utilisée comme fixture.
- Mise à jour familiale après sauvegarde privée 0600 vérifiée ; volume et compte
  conservés, intégrité et clés étrangères correctes. Santé API, manifeste, fichiers
  d’import et correction CSS mobile servis vérifiés, sans créer de recette de test
  dans la maison. Contrôle de confidentialité des fichiers distribuables réussi.
- Aucun push, aucune publication, aucun proxy HTTPS ni certificat configuré.

Limite restante : la réception HTTP et le formulaire sont validés ; l’apparition
native dans le menu Android demande une PWA installée sur une origine HTTPS et une
vérification manuelle. Le serveur doit être joignable pour recevoir le partage.
Sur HTTP LAN, l’import par collage demeure le parcours disponible. Aucun navigateur
ou menu système n’est automatisé. Pas d’OCR, de code-barres ou d’IA dans ce jalon.

## Mise à jour 0.5.0 — photos des recettes

- 121 tests backend réussis : formats raster, orientation et retrait des métadonnées,
  taille/pixels/animations, accès privé et CSRF, remplacement invalide sans perte,
  upload en flux borné, import atomique/idempotent avec photo, source/attribution,
  aperçu sans écriture, extraction relative JSON-LD/HTML, transport épinglé et types
  MIME, redirections privées refusées. Les photos sont conservées à la sauvegarde
  et à la restauration ; suppression de recette avec cascade vérifiée.
- 31 tests frontend réussis : ajout de l’envoi binaire authentifié et des erreurs,
  rendu de l’éditeur avec image locale, attribution et conservation explicite.
  Calendrier/impression, partage et courses hors connexion restent validés.
- TypeScript/Vite et image Docker réussis. Seule nouvelle dépendance : Pillow 13.0.0,
  verrouillée ; licence MIT-CMU documentée. Migration additive 0004, table BLOB séparée
  pour ne pas inclure les données binaires dans les tableaux de recettes.
- Image finale : `sha256:a24aed6e7a5f899718fd8841a74e8e38939339b8af7fcced499364046648bf5b`.
- Parcours HTTP isolé réussi sur données synthétiques : PNG transmis, JPEG réduit
  et dépourvu d’EXIF servi après authentification, import photo atomique et retrait.
- Essai public Marmiton : image déclarée extraite, téléchargée par le transport
  sécurisé et normalisée ; ni texte ni image de ce site enregistrés comme recette
  ni conservés dans les fixtures du projet. Aucune lecture de recette réelle du foyer.
- Sauvegarde familiale privée 0600 vérifiée avant mise à jour. Même volume et compte
  conservés, schéma 0004, intégrité et clés étrangères correctes, dépendance et nouveaux
  fichiers servis contrôlés sur le LAN. Aucune photo de test injectée dans la maison.
- Instance de validation arrêtée, volume et images Docker conservés. Aucun push ni
  publication. Contrôle de confidentialité des fichiers distribuables réussi.

À vérifier manuellement : choix d’une image depuis le téléphone, aperçu portrait,
remplacement/retrait et absence de débordement dans le dialogue. JPEG/PNG/WebP fixes
acceptés ; HEIC, SVG et animations refusés. L’import du texte reste possible sans
photo si le site bloque l’image. Le cache de courses hors ligne n’inclut pas les photos.

## Préparation juridique de publication — 8 novembre 2026

- LICENSE téléchargé depuis le texte officiel PolyForm Noncommercial 1.0.0, sans
  modification. SHA-256 : ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8.
- Copyright Getsugah dans NOTICE, distinct du texte officiel ; code propre et
  visuels couverts uniquement dans la mesure des droits détenus. Provenance du
  nom/SVG et des deux variantes PNG confirmée par le responsable dans ASSETS.md.
- 122 entrées de dépendances inventoriées : 19 Python de production, 7 de tests,
  96 npm dont 50 variantes optionnelles absentes. 76 textes de licence et notice
  collectés et contrôlés par empreinte et inclusion complète depuis les fichiers amont.
- Copies des six documents juridiques vérifiées dans frontend/public/legal et
  dans frontend/dist/legal. Synchronisation contrôlée avec scripts/sync_legal.py --check.
- Compilation Vue/TypeScript/Vite réussie. JavaScript et CSS résultants strictement
  identiques, par SHA-256, aux fichiers de l’instance en service.
- Empreintes des sources existantes, tests, visuels, migrations, exigences Python,
  Dockerfile, Compose, service worker et configuration Vite inchangées. Seules les
  métadonnées de licence npm, la documentation et les nouveaux fichiers juridiques
  ou de synchronisation sont concernés.
- Contrôle ciblé de confidentialité réussi. Aucun nouveau test métier nécessaire,
  aucune fonctionnalité modifiée, aucune dépendance installée ou mise à jour pour
  ce travail. Aucun build Docker ni remplacement du conteneur, push ou publication.

Les prochaines constructions reprennent les notices via les fichiers publics
existants. Une image Docker publique nécessite aussi de conserver les obligations
propres aux composants système ; l’inventaire applicatif n’est pas un SBOM système
exhaustif. Voir docs/LICENSE_AUDIT.md pour le périmètre et les limites de l’audit.
