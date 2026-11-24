# Mijote

Les menus de la semaine, les recettes, les stocks et les courses dans une
application familiale auto-hébergée. Interface en français, adaptée à
l’ordinateur et au téléphone.

## Ce que fait Mijote

- **Menus** : planning sur sept jours, midi et soir, avec présence, portions et
  plusieurs plats par repas (entrée, plat, dessert, accompagnements).
- **Recettes** : saisie manuelle ou import depuis un lien ou un texte collé,
  photos, favoris, avis, tags et fusion des ingrédients en double.
- **Stocks** : aliments par emplacement et date limite, consommés lorsqu’un
  repas est confirmé comme préparé.
- **Courses** : manquants calculés d’après les menus et les stocks, panier,
  confirmation des achats, impression et liste à emporter hors connexion.
- **Suggestions** et **Historique** : idées de repas tirées du carnet et
  repas déjà préparés.

Aucune action sur les stocks n’est faite sans confirmation. Le guide complet est
dans [docs/UTILISATION.md](docs/UTILISATION.md).

## Installation

Prérequis : **Bash, Git, Docker Engine démarré et Docker Compose v2**. Le script
vérifie leur présence sans installer de paquets système.

```sh
git clone https://github.com/getsugah/mijote.git
cd mijote
bash install.sh
```

Le script demande le port HTTP (**8095 par défaut**), l’adresse d’écoute
(**0.0.0.0 par défaut**) et l’IPv4 privée du serveur, puis construit et démarre
l’application. Ouvrir ensuite `http://IP_DU_SERVEUR:8095` et créer le compte
familial : aucun mot de passe n’est prédéfini (12 caractères minimum, pas de
récupération par courriel).

La configuration est enregistrée dans `.env`, qui est conservé lors des relances.
Les données sont dans le volume Docker `mijote_mijote_data`, pas dans le dossier
des sources.

Accès réseau, HTTPS, ZimaOS, installation sans Git ou avec Docker Compose seul :
voir [docs/INSTALLATION_AVANCEE.md](docs/INSTALLATION_AVANCEE.md).

## Mise à jour

Faire d’abord une sauvegarde (section suivante), puis, depuis le dossier des sources :

```sh
bash install.sh update
```

Le script récupère la nouvelle version par avance rapide uniquement, puis
reconstruit et relance l’application. Il refuse de continuer si des fichiers
suivis ont été modifiés localement. Les migrations de la base s’appliquent au
démarrage ; pour revenir en arrière, restaurer la sauvegarde avec l’ancienne version.

## Sauvegarde et restauration

La base contient recettes, menus, stocks, photos, compte et sessions : conserver
les sauvegardes dans un emplacement privé, avec une copie de `.env`.

Sauvegarde pendant le fonctionnement (choisir un nouveau nom à chaque fois) :

```sh
mkdir -p backups
umask 077
(set -C; docker compose exec -T mijote python -m app.backup backup - > backups/mijote-sauvegarde.sqlite3)
```

Restauration :

```sh
docker compose stop mijote
docker compose run --rm --no-deps -T mijote python -m app.backup restore - < backups/mijote-sauvegarde.sqlite3
docker compose up -d
```

La restauration vérifie la sauvegarde et conserve l’ancienne base sous
`pre-restore-*.sqlite3` dans le volume. Ne jamais utiliser `docker compose down -v` :
cette commande supprime le volume des données.

## Limites connues

- Une seule maison et un compte familial ; pas de comptes individuels ni de
  récupération du mot de passe par courriel.
- La recherche de recettes interroge le service externe **TheMealDB** : le texte
  recherché lui est transmis (voir [docs/INSTALLATION_AVANCEE.md](docs/INSTALLATION_AVANCEE.md)).
- L’installation de la PWA, le partage depuis Android et la réouverture hors
  connexion nécessitent HTTPS ; en HTTP local, garder l’onglet ouvert.
- La liste de courses hors connexion ne confirme pas les achats et reste limitée
  à une semaine.
- Photos JPEG, PNG et WebP uniquement (pas de HEIC ni d’animations).
- Jours fériés : France métropolitaine seulement (pas d’Alsace-Moselle ni d’outre-mer).
- **Restent à vérifier manuellement :**
  - l’installation sur un appareil ZimaOS réel ;
  - l’apparition de Mijote dans le menu **Partager** d’Android ;
  - l’installation et la réouverture de la PWA sur Android ;
  - le rendu d’impression des menus et des courses sur Chrome et l’imprimante utilisée ;
  - l’ergonomie sur Chrome/GNOME et Android.

Les parcours de vérification sont dans [docs/RECETTE_MANUELLE.md](docs/RECETTE_MANUELLE.md).

## Licence

Le code propre à Mijote est **à code consultable (« source-available »)**, sous
**PolyForm Noncommercial 1.0.0** ([LICENSE](LICENSE)), Copyright 2026 Getsugah
([NOTICE](NOTICE)). L’usage personnel et non commercial est gratuit. Le code peut
être consulté, modifié et redistribué pour les usages autorisés, en transmettant
les conditions de la licence et les lignes `Required Notice:`. Une
exploitation commerciale non couverte par la licence nécessite une autorisation
distincte, voir [COMMERCIAL.md](COMMERCIAL.md). Cette explication ne remplace pas
les conditions du fichier LICENSE, qui prévoit aussi des usages autorisés pour
certaines organisations. Ce n’est pas une licence « open source » au sens de l’OSI.

Les dépendances conservent leurs licences : voir
[THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) et
[docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md). Le nom et le logo sont décrits
dans [ASSETS.md](ASSETS.md). Les recettes et photos ajoutées restent privées et
ne sont pas couvertes par cette licence.

Développement, tests et notices de distribution :
[docs/DEVELOPPEMENT.md](docs/DEVELOPPEMENT.md). Historique : [CHANGELOG.md](CHANGELOG.md).
