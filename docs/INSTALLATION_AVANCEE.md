# Installation avancée

L’installation standard avec `install.sh` est décrite dans le [README](../README.md).
Ce document regroupe les cas particuliers et la configuration.

## Ce que fait `install.sh`

Le script demande le port HTTP (**8095 par défaut**), l’adresse d’écoute
(**0.0.0.0 par défaut**) et l’IPv4 privée du serveur. Il propose l’IP détectée, à
vérifier : un serveur peut avoir plusieurs interfaces. Il prépare les origines
autorisées, construit l’image puis attend que le conteneur soit sain avant d’afficher
les URL. Une connexion Internet et suffisamment d’espace disque sont nécessaires.

Le fichier `.env` est créé avec des droits privés. S’il existe déjà, il est
**conservé intégralement**, y compris son port ou sa configuration HTTPS. Pour changer
le port, modifier `MIJOTE_PORT` et les ports dans `MIJOTE_ALLOWED_ORIGINS`, puis
relancer `bash install.sh`. La relance reconstruit et redémarre au besoin avec le même
volume de données.

### Détails de la mise à jour

`bash install.sh update` récupère, après confirmation, la branche suivie (ou celle du
même nom sur `origin`), accepte seulement une avance rapide, puis reconstruit et relance.
Il refuse les modifications locales et les fichiers non suivis non ignorés ; `.env`,
données et sauvegardes restent en place. Il ne fait aucun stash, reset ou écrasement.
Si Git diverge, une résolution manuelle est nécessaire. Un échec de construction laisse
le code actualisé : corriger l’erreur puis relancer `bash install.sh`.

### Désinstaller en conservant les données

```sh
bash install.sh uninstall
```

La saisie exacte de `DESINSTALLER` est nécessaire. Seuls les conteneurs et le réseau
Compose sont retirés. Le volume, les sources, `.env`, les images et les sauvegardes
restent en place. Relancer `bash install.sh` permet de reprendre l’installation.

## Installer sans Git (archive ZIP)

Sur la page [GitHub de Mijote](https://github.com/getsugah/mijote), choisir
**Code → Download ZIP**. Extraire l’archive entière dans un dossier permanent, lire
`install.sh`, puis lancer `bash install.sh` depuis ce dossier. Git doit tout de même
être installé pour les vérifications du script. Ne pas utiliser `curl | bash`.

La mise à jour automatique n’est pas proposée pour une archive : le clone est recommandé.
Pour mettre à jour une installation ZIP, sauvegarder, extraire la nouvelle version dans
un autre dossier, y recopier le `.env` existant, relire le script et le lancer. Le projet
Compose s’appelle toujours `mijote` : le volume existant est réutilisé sur le même démon
Docker. Ne pas lancer simultanément deux installations utilisant la même base.

## ZimaOS et accès réseau

- Utiliser un terminal SSH ou celui du serveur. Le script déploie avec Compose ; il ne
  crée pas de fiche dans le catalogue d’applications ZimaOS. Son exécution sur un
  appareil ZimaOS réel reste à valider.
- Choisir un dossier permanent sur un disque monté, où le compte peut écrire. Les données
  résident dans le volume Docker `mijote_mijote_data`, pas dans le dossier du clone.
- Si les permissions Docker l’exigent, utiliser `sudo bash install.sh` (ou `update` /
  `uninstall`) avec un compte autorisé. Le script ne modifie ni les groupes ni le socket
  Docker. Éviter d’alterner les comptes : Git peut refuser un dépôt possédé par un autre
  utilisateur. Ne pas désactiver globalement ses contrôles de propriété.
- Le port choisi doit être libre. Si un autre service l’utilise, modifier `.env` puis
  relancer. Le script ne désactive aucun service existant.
- L’écoute sur `0.0.0.0` couvre toutes les interfaces IPv4 : n’utiliser HTTP que sur un
  réseau privé de confiance. Le script n’ouvre aucun port du pare-feu ou du routeur.
- Une seule installation Compose nommée `mijote` est gérée par démon Docker. Plusieurs
  foyers isolés nécessitent une configuration manuelle distincte.

## Démarrer avec Docker Compose seul

Sur un hôte disposant de Docker Engine et de Compose v2 :

```sh
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Cette méthode utilise les valeurs de `.env.example` : écoute sur `127.0.0.1` et port
**8095** (variable `MIJOTE_PORT`), comme `install.sh`. Ouvrir `http://localhost:8095`,
puis créer le compte familial. Pour un autre port, modifier `MIJOTE_PORT` et
`MIJOTE_ALLOWED_ORIGINS` dans `.env` avant le démarrage.

Les commandes Docker peuvent nécessiter `sudo`. Un seul service sert l’interface et
l’API, sans base ni proxy supplémentaires. Journaux et arrêt sans perte de données :

```sh
docker compose logs --tail=100 mijote
docker compose stop
docker compose start
```

Ne pas utiliser `docker compose down -v` : cela supprime le volume des données.

## Configuration

La configuration locale est dans `.env`, exclu de Git. Les données sont dans le volume
`mijote_data` du projet Compose `mijote`, nommé `mijote_mijote_data` par Docker. Aucun
secret de session fixe n’est nécessaire : les sessions sont générées aléatoirement et
hachées en base.

| Variable | Valeur par défaut | Rôle |
| --- | --- | --- |
| `MIJOTE_BIND` | `0.0.0.0` | Adresse d’écoute sur l’hôte |
| `MIJOTE_PORT` | `8095` | Port de l’application |
| `MIJOTE_ALLOWED_ORIGINS` | `http://IP_DU_SERVEUR:8095,…` | Origines autorisées à modifier les données |
| `MIJOTE_SECURE_COOKIE` | `false` | `true` impose HTTPS pour le cookie de session |
| `MIJOTE_THEMEALDB_KEY` | `1` | Clé de l’API TheMealDB ; non écrite par `install.sh`, valeur par défaut de `compose.yaml` |

Les quatre premières valeurs sont celles proposées par `install.sh`.
Après une modification de `.env`, appliquer avec `docker compose up -d` (ou relancer
`bash install.sh`). Initialiser le compte avant d’ouvrir l’accès au réseau.

### Accès distant et HTTPS

Ne pas publier le port directement sur Internet. Pour un accès distant, utiliser un VPN
privé ou un reverse proxy HTTPS :

1. configurer le proxy vers le port local de Mijote ;
2. limiter l’écoute au réseau du proxy ou à `127.0.0.1` (`MIJOTE_BIND`) ;
3. définir l’origine exacte `https://…` dans `MIJOTE_ALLOWED_ORIGINS` ;
4. définir `MIJOTE_SECURE_COOKIE=true`, puis relancer.

Aucun en-tête `X-Forwarded-*` n’est utilisé pour décider des permissions.

### PWA et téléphone

La PWA fournit un manifeste et un service worker. L’installation dans Chrome nécessite
**HTTPS ou localhost** ; HTTP sur une IP locale ne suffit pas. Le service worker met en
cache uniquement les fichiers publics, jamais les réponses de l’API privée. En HTTP
local, garder l’onglet chargé avant de quitter le réseau : la réouverture hors connexion
nécessite HTTPS ou localhost.

## Recherche TheMealDB

La section **Un titre et sa photo** de l’éditeur de recette et de l’import interroge
[TheMealDB](https://www.themealdb.com/), un service externe, lorsque l’utilisateur
lance une recherche. Le texte recherché (éventuellement traduit en anglais pour quelques
plats courants) est envoyé au serveur `www.themealdb.com` depuis le serveur Mijote, ainsi
que l’adresse IP de ce serveur. Aucune recette n’est enregistrée sans choix explicite, et
aucune collecte en masse n’est effectuée. La photo prévisualisée passe par les mêmes
contrôles de téléchargement que l’import.

`MIJOTE_THEMEALDB_KEY` vaut `1` par défaut, la clé de test publique de TheMealDB. Une clé
personnelle se définit dans `.env`, jamais dans Git. Sans accès Internet, cette recherche
échoue sans effet sur le reste de l’application.
