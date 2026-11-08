# Mijote

Les repas de la semaine, les recettes, les réserves et les courses dans une
application familiale auto-hébergée. Interface française, aubergine, orange et
crème, adaptée à l’ordinateur et au téléphone.

## Licence et utilisations autorisées

Le code propre à Mijote est proposé sous **PolyForm Noncommercial 1.0.0**.
Le texte officiel, intégral et inchangé figure dans [LICENSE](LICENSE).

**Copyright 2026 Getsugah**, pour les éléments sur lesquels Getsugah détient les
droits. Getsugah est le pseudonyme du responsable du projet, développé à sa demande
avec l’assistance de Codex. Voir la mention à conserver dans [NOTICE](NOTICE).

- L’utilisation personnelle et non commerciale est gratuite, dans les conditions
  prévues par la licence.
- Vous pouvez consulter, modifier et redistribuer le code pour les usages autorisés,
  en respectant les conditions de la licence, notamment la transmission de ses
  conditions ou de leur URL et des lignes `Required Notice:` fournies avec le logiciel.
- Une exploitation commerciale **non couverte par cette licence** nécessite une
  autorisation distincte. Un contrat de licence commerciale peut être conclu
  directement avec Getsugah pour les droits qu’il détient ; voir [COMMERCIAL.md](COMMERCIAL.md).
- Le texte officiel prévoit aussi des usages autorisés pour certaines organisations.
  Tout usage professionnel ou tout financement ne signifie donc pas automatiquement
  qu’une licence commerciale est nécessaire. La présente explication ne remplace
  pas les conditions du fichier LICENSE.

Mijote est ainsi **à code consultable (« source-available »)**. La restriction des
usages commerciaux ne correspond pas à la définition « open source » de l’OSI.
Le logiciel est fourni sans garantie dans les limites prévues par la licence.

Les dépendances conservent leurs licences et copyrights propres : la licence de
Mijote ne les remplace pas et ne restreint pas les droits qu’elles accordent.
Les textes tiers sont dans [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) et
l’inventaire des versions dans [THIRD_PARTY_MANIFEST.json](THIRD_PARTY_MANIFEST.json).
Le bilan et les limites de l’audit sont dans [docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md).

La provenance du nom, du logo SVG et des variantes PNG est documentée dans
[ASSETS.md](ASSETS.md). Ils sont inclus pour les droits détenus par Getsugah.
Les recettes, photos et autres contenus personnels ajoutés ou importés ne sont
pas couverts par cette licence du projet et restent exclus de sa publication.

## Organiser les repas et les courses

- Planning sur sept jours, midi et soir, selon un modèle de présence modifiable.
- Portions familiales par défaut et exception par repas ; plat et accompagnement.
- Intitulés simples, plats improvisés et recettes avec ingrédients et quantités.
- Réserves par emplacement et date facultative, corrections et journal.
- Besoins calculés entre les repas sans déduire le stock lors de la planification.
- Courses calculées et ajouts manuels ; panier distinct de la confirmation d’achat.
- Confirmation des quantités réellement achetées ou consommées, sans double mouvement.

Les changements sont décrits dans [CHANGELOG.md](CHANGELOG.md) et les
vérifications dans [VALIDATION.md](VALIDATION.md).

## Calendrier et impression

Les jours fériés nationaux français ont un en-tête coloré et leur nom dans le
calendrier. Les dates sont calculées localement, sans service externe à l’exécution.
Les particularités d’Alsace-Moselle et des territoires ultramarins ne sont pas
incluses pour le moment. Ce repérage ne change ni les statuts des repas ni les stocks.
Référence des dates : [calendrier officiel français](https://calendrier.api.gouv.fr/jours-feries/metropole/2026.json).

Dans **Ma semaine**, **Imprimer la semaine** ouvre l’impression du navigateur avec
une mise en page A4 paysage : les sept jours, midi/soir, plats, accompagnements,
portions et indications de présence. Une case hors maison affiche son statut,
sans présenter les recettes conservées comme des repas à préparer. Le navigateur
permet aussi de choisir **Enregistrer au format PDF**. L’aperçu final reste à
vérifier sur Chrome et sur l’imprimante utilisée.

Le champ **Source** conserve l’URL. Depuis la version 0.2.0, utiliser **Importer une
recette** dans le carnet pour lire un lien et préremplir la recette avant validation.

## Importer une recette

Dans **Mes recettes → Importer une recette** :

1. Coller une URL publique, puis choisir **Prévisualiser la recette**.
2. Vérifier le titre, les portions de référence, la durée, les ingrédients et les étapes.
3. Associer les lignes au répertoire existant ou corriger le nom des nouveaux ingrédients.
4. Inclure uniquement les quantités et unités vérifiées dans les besoins ; les lignes
   non cochées restent dans le texte d’origine, sans déduction automatique.
5. Confirmer la vérification et enregistrer. La recette et les nouveaux ingrédients
   sont créés ensemble ; le stock ne change pas. Une requête de confirmation rejouée
   avec le même identifiant ne crée pas de doublon.

L’extraction privilégie Schema.org Recipe en JSON-LD, puis utilise un repli HTML
générique, sans liste fermée de sites. URL et auteur (lorsqu’il est disponible)
sont conservés. Les quantités ambiguës, les cuillères, les pincées et autres mesures
non convertibles ne sont pas transformées arbitrairement en grammes. Les portions
absentes ou exprimées en nombre de pièces doivent être vérifiées.

Si le site bloque l’accès, requiert un compte ou ne fournit pas de contenu lisible,
utiliser **Coller le texte**. Les intitulés `Ingrédients` et `Préparation` aident à
séparer les lignes. Le champ URL peut alors servir simplement d’attribution.
Aucun cookie de consentement n’est accepté et aucun contrôle d’accès n’est contourné.
Depuis la version 0.5.0, une photo proposée par le site peut être prévisualisée et conservée. Les textes et photos importés restent dans votre instance privée.

Les téléchargements sont limités aux sites publics HTTP/HTTPS sur ports standards,
avec validation DNS et connexion sur l’IP approuvée, certificat TLS du vrai domaine,
redirections revalidées, 15 secondes au total et 3 Mio maximum (y compris après
décompression). Les adresses privées/locales/métadonnées sont refusées. L’analyse
ne conserve pas de transaction SQLite pendant le téléchargement.

Essais publics réussis : [Marmiton](https://www.marmiton.org/recettes/recette_soupe-de-legumes_222646.aspx)
et [Good Food](https://www.bbcgoodfood.com/recipes/easy-pancakes) en JSON-LD,
[750g](https://www.750g.com/pate-a-crepes-r6965.htm) via le repli HTML. Ce résultat ne
promet pas la lecture de tous les sites. Les contenus réels ne sont pas intégrés aux
fixtures du projet ; les tests enregistrent seulement des recettes synthétiques.

## Favoris, suggestions et courses hors connexion

- **Mes recettes** : bouton favori, filtre favoris/à tester/catégorie et **Mon avis**
  pour l’appréciation, le commentaire et la variante personnelle. Les variantes
  sont des notes : elles ne changent pas automatiquement les ingrédients calculés.
  Une recette importée est marquée « À tester » ; sa préparation retire ce statut.
- **Historique** : repas réellement confirmés, noms et portions conservés au moment
  de la préparation. Pour les anciennes confirmations, l’heure inconnue est indiquée.
  Choisir un créneau maison vide de la semaine affichée pour replanifier un repas.
- **Ma semaine → Des idées** : modes varier, utiliser le stock, rapide et découverte,
  avec une justification et **Une autre idée**. Le moteur utilise le carnet, les
  préparations, les catégories et les réserves libres après les autres repas.
  « Ne plus proposer » retire la recette des suggestions. Aucune IA n’est utilisée.
- **Ma semaine → Copier un menu** : choisir le lundi d’une semaine existante,
  examiner l’aperçu et confirmer. Seuls les créneaux maison vides sont remplis ;
  aucun repas existant, état préparé ou mouvement de stock n’est recopié.
- **Mes courses → Emporter ma liste** : copie locale volontaire, cases à cocher,
  ajouts personnels, modifications hors connexion et synchronisation au retour
  du réseau. Un conflit demande un choix explicite, sans écrasement silencieux.
  Voir [le guide des courses hors ligne](docs/COURSES_HORS_LIGNE.md).

L’import seul n’ajoute rien aux courses. Planifier la recette ajuste ses quantités
aux portions du repas et calcule les manquants après réservation du stock. Exemple :
400 g pour quatre portions deviennent 600 g pour six ; avec 200 g libres en stock,
400 g figurent aux courses. Les ingrédients restés uniquement dans les notes sont
hors calcul.

## Découvrir une recette sur le web

Dans **Ma semaine → Des idées**, choisir **Découvrir un plat sur le web** pour
recevoir une recette au hasard depuis la source choisie. Par défaut, les idées
viennent des dernières publications du [Journal des Femmes Cuisine](https://cuisine.journaldesfemmes.fr/derniererecette/).
Son nom, sa source et un lien vers la recette sont affichés. **Une autre idée sur
le web** propose un autre résultat ; les liens déjà vus dans ce panneau et les
recettes déjà importées depuis la même URL sont écartés. Quand la sélection est
épuisée, **Revoir les idées web** permet de la parcourir à nouveau.

**Voir la recette sur le site** ouvre la source dans un nouvel onglet.
**Importer cette recette** ouvre le formulaire habituel avec son URL : cliquer
sur **Prévisualiser**, vérifier puis confirmer pour l’ajouter au carnet. La simple
découverte n’enregistre rien et ne modifie ni le planning, ni les stocks, ni les
courses. Elle reste disponible même si le carnet est vide.

Dans **Ajouter ou gérer les liens pour les idées**, coller l’URL d’un site, d’une
page qui liste des recettes ou d’une recette précise, puis choisir **Vérifier et
ajouter ce lien**. Mijote lit la page avec les protections de l’import et ne garde
le lien que si des recettes sont reconnues. Choisir ensuite cette source dans
**Source des idées** et demander une découverte. Jusqu’à 20 liens personnels
peuvent être conservés, en plus de la source initiale. Les doublons sont signalés.
**Retirer ce lien** demande confirmation et conserve les recettes déjà importées.

Les liens restent privés dans la base SQLite : ils sont conservés au redémarrage,
à la mise à jour et par la sauvegarde/restauration habituelle. La migration 0005
ajoute cette liste sans modifier les recettes existantes. Faire une sauvegarde
avant de mettre à jour l’installation.

Chaque source fournit un choix limité aux recettes reconnues sur la page donnée,
sans filtre selon les réserves, les préférences ou le temps de préparation.
L’extraction reconnaît les données structurées Recipe/ItemList et certains liens
de recettes usuels, sur le même domaine que la page finale. Elle ne parcourt pas
le site entier et ne garantit pas la compatibilité de tous les sites. Si rien
n’est reconnu, essayer une page listant les recettes plutôt que la page d’accueil,
ou directement une recette. Les pages protégées, rendues uniquement en JavaScript
ou bloquant l’accès automatisé peuvent être refusées ; aucun accès n’est contourné.

Une connexion Internet est nécessaire pour vérifier et actualiser une source.
Seuls les titres et liens sont utilisés pour les idées, sans téléchargement des
photos ni enregistrement d’ingrédients. Les sélections sont gardées en mémoire
pendant 15 minutes au maximum ; seul le lien source est conservé en base.
Un changement du site, une panne ou un blocage peuvent rendre une source
indisponible ; une autre source et les idées du carnet restent utilisables.

## Partager une recette depuis Android

Avec Mijote installé depuis Chrome sur Android, ouvrir une recette puis choisir
**Partager → Mijote**. Le lien ou le texte préremplit le formulaire d’import.
Si nécessaire, se connecter d’abord : le partage attend dans la page. Choisir
**Prévisualiser**, vérifier la recette puis confirmer son enregistrement comme
pour l’import habituel. Aucun téléchargement n’est lancé à la seule réception et
aucune recette n’est enregistrée sans confirmation.

Le lien peut être reçu dans le champ URL, le texte ou le titre. Plusieurs liens
sans source explicite demandent de choisir la source ; aucun choix n’est inventé.
Les images et fichiers ne sont pas acceptés dans cette itération.

Le partage natif demande **une PWA installée en HTTPS** et la compatibilité du
navigateur Android. Avec l’adresse HTTP locale, continuer à copier le lien puis
utiliser **Importer une recette**. Le serveur doit être accessible pour recevoir
le partage ; sa réception hors connexion n’est pas implémentée. Voir les
[conditions de Chrome](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target).
L’apparition effective dans le menu Android reste à vérifier sur l’appareil.

Les données partagées arrivent par POST, sans figurer dans l’URL. La page de
réception n’est pas mise en cache ; Mijote ne conserve pas ce brouillon dans sa
base ni dans le stockage local. Le contenu attend en mémoire pendant la connexion.
Annuler l’import l’efface ; fermer ou recharger la page peut le perdre. Refaire le
partage si nécessaire. Le contrôle d’accès et les protections SSRF habituels
s’appliquent à la prévisualisation, puis la confirmation reste authentifiée.

## Une photo pour chaque recette

Dans **Mes recettes**, le bouton **Photo** permet de choisir une image depuis le
téléphone ou l’ordinateur. Vérifier l’aperçu puis **Conserver cette photo**. Le même
écran permet de la remplacer ou de la retirer sans supprimer la recette. Pour une
nouvelle recette manuelle, l’enregistrer d’abord puis ouvrir son bouton Photo.

Si la recette possède une URL source, **Proposer la photo du site source** cherche
l’image annoncée sur cette page. Lors d’un nouvel import URL, la photo disponible
est téléchargée et prévisualisée automatiquement. Décocher **Conserver cette photo**
pour enregistrer seulement la recette. L’absence de photo ou un site qui refuse
son téléchargement n’empêchent pas l’import du texte. Aucune image n’est choisie au
hasard pour les recettes sans source.

Formats : **JPEG, PNG et WebP fixes**, jusqu’à **12 Mio et 24 mégapixels** en ajout
manuel. HEIC, SVG et animations ne sont pas acceptés ; exporter en JPEG si nécessaire.
Les images sont orientées, réduites à 1 600 pixels maximum sur leur grand côté et
réencodées en JPEG, à 512 Kio maximum. Les métadonnées EXIF/GPS, commentaires et
profils incorporés ne sont pas conservés. La photo d’origine n’est pas stockée.

Les photos sont privées, servies après authentification et conservées dans la base
SQLite. **La sauvegarde/restauration habituelle inclut aussi les photos**, sans
répertoire supplémentaire à copier. Leur ajout augmente donc la taille de la base
et des sauvegardes. Les listes de courses hors connexion ne contiennent pas les photos.

Le téléchargement des photos du web reprend les protections réseau de l’import :
HTTP/HTTPS publics, DNS et redirections validés, connexion épinglée, 15 secondes et
3 Mio maximum. Les images sont décodées puis réencodées avant affichage ; le navigateur
ne charge pas directement le site tiers pour afficher une photo de recette.
La source et l’attribution disponibles sont conservées et restent modifiables dans
l’aperçu. Conserver ces contenus dans l’usage privé du foyer et respecter leurs droits.

Le traitement utilise [Pillow](https://python-pillow.org/), sous licence [MIT-CMU](https://pillow.readthedocs.io/en/stable/about.html#license) et
licences tierces indiquées dans sa distribution. La dépendance est verrouillée ;
elle ne change pas la licence du code de l’application.

## Installation guidée sur ZimaOS ou Linux

Prérequis : **Bash, Git, Docker Engine démarré et Docker Compose v2**. Le script
vérifie leur présence sans installer de paquets système. Une connexion Internet
et suffisamment d’espace pour construire l’image sont nécessaires.

Depuis un terminal, dans le dossier où conserver les sources :

```sh
git clone https://github.com/getsugah/migote.git
cd migote
bash install.sh
```

Le script demande le port HTTP (**8095 par défaut**), l’adresse d’écoute
(**0.0.0.0 par défaut**) et l’IPv4 privée du serveur. Il propose l’IP détectée,
à vérifier : un serveur peut avoir plusieurs interfaces. Il prépare les origines
autorisées, construit l’image puis attend que le conteneur soit sain avant
d’afficher les URL. Créez ensuite le compte familial dans le navigateur ; aucun
mot de passe n’est prédéfini.

Le fichier `.env` est créé avec des droits privés. S’il existe déjà, il est
**conservé intégralement**, y compris son ancien port ou sa configuration HTTPS :
aucune nouvelle question ne remplace ses valeurs. Pour changer le port, modifier
`MIJOTE_PORT` et les ports dans `MIJOTE_ALLOWED_ORIGINS`, puis relancer le script.
La relance reconstruit et redémarre au besoin avec le même volume de données.

### Télécharger depuis GitHub sans exécuter de script distant

La page [GitHub de Mijote](https://github.com/getsugah/migote) propose **Code →
Download ZIP**. Extraire l’archive entière dans un dossier permanent, lire
`install.sh`, puis y ouvrir un terminal et lancer `bash install.sh`. Git doit
également être installé pour les vérifications du script. Ne pas utiliser
`curl | bash` : le script est téléchargé et consultable avant son lancement.
La mise à jour automatique du code nécessite un clone Git ; elle n’est pas
proposée pour une archive ZIP. Pour cette raison, le clone est recommandé.

### Mettre à jour

Faire d’abord une sauvegarde avec la procédure **Sauvegarder et restaurer**
ci-dessous, puis, depuis le même dossier :

```sh
bash install.sh update
```

Après confirmation, le script récupère la branche suivie (ou celle du même nom
sur `origin` en l’absence de suivi), accepte seulement une avance rapide, puis
reconstruit et relance les conteneurs. Il refuse les modifications locales et les
fichiers non suivis non ignorés ; `.env`, données et sauvegardes ignorés restent
en place. Il ne fait aucun stash, reset ou écrasement automatique. Si Git diverge,
une résolution manuelle est nécessaire. Un échec de construction laisse le code
actualisé ; corriger l’erreur puis relancer `bash install.sh`. Les migrations
s’appliquent au démarrage : conserver la sauvegarde pour tout retour en arrière.

Pour une installation par ZIP, sauvegarder puis extraire la nouvelle version
dans un autre dossier, y recopier le `.env` existant et relire le script avant de
le lancer. Le nom du projet Compose reste `mijote`, donc le volume existant est
réutilisé sur le même démon Docker. Conserver l’ancienne copie ; ne pas lancer
simultanément deux installations utilisant cette même base.

### Désinstaller en conservant les données

```sh
bash install.sh uninstall
```

La saisie exacte de `DESINSTALLER` est nécessaire. Seuls les conteneurs et le réseau
Compose sont retirés. Le volume, les sources, `.env`, les images et les sauvegardes
restent en place. Relancer `bash install.sh` permet de reprendre l’installation.
Aucune commande de suppression des données n’est exécutée ou proposée par le script.

### Particularités ZimaOS et accès réseau

- Utiliser un terminal SSH ou le terminal disponible sur le serveur. Le script
  déploie avec Compose ; il ne crée pas de fiche dans le catalogue d’applications
  ZimaOS. Son exécution sur un appareil ZimaOS réel reste à valider.
- Choisir un dossier permanent sur un disque monté, où le compte peut écrire.
  Les données applicatives résident dans le volume Docker `mijote_mijote_data`,
  pas dans le dossier du clone. Sauvegarder la base par la procédure dédiée.
- Docker et le plugin Compose v2 doivent être disponibles dans le terminal.
  Si les permissions Docker le demandent, utiliser `sudo bash install.sh`
  (ou `sudo bash install.sh update` / `uninstall`) avec un compte autorisé.
  Le script ne modifie pas les groupes ni les permissions du socket Docker.
  Éviter d’alterner les comptes : Git peut refuser un dépôt possédé par un autre
  utilisateur. Ne pas désactiver globalement ses contrôles de propriété.
- Le port choisi doit être libre. Si un autre service le réserve, modifier `.env`
  puis relancer. Les erreurs du démon Docker restent affichées ; le script ne
  désactive aucun service existant. Une réservation sur une autre interface peut
  aussi être signalée par le contrôle préliminaire du port.
- L’écoute sur `0.0.0.0` couvre toutes les interfaces IPv4 : utiliser HTTP seulement
  sur un réseau privé de confiance. Le script n’ouvre aucun port du pare-feu ou du
  routeur. Pour un accès distant, utiliser un VPN privé ou un reverse proxy HTTPS.
- Pour HTTPS ultérieurement, configurer le proxy, limiter l’écoute au réseau du
  proxy ou à `127.0.0.1`, définir l’origine exacte `https://…` dans
  `MIJOTE_ALLOWED_ORIGINS` et `MIJOTE_SECURE_COOKIE=true`, puis relancer.
  Voir aussi **Configuration et accès depuis le téléphone** ci-dessous.
- Une seule installation Compose nommée `mijote` est gérée par démon Docker.
  Plusieurs foyers isolés nécessitent une configuration manuelle distincte.

## Démarrer avec Docker Compose

Sur un hôte Debian 13 disposant de Docker Engine et de Compose v2 :

```sh
docker --version
docker compose version
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Ouvrir **http://localhost:8080**, puis créer le compte familial depuis l’écran
d’accueil. Aucun mot de passe prédéfini. Choisir au moins 12 caractères et conserver
ce mot de passe : la récupération par courriel n’est pas implémentée.

Les commandes Docker peuvent nécessiter `sudo` selon les droits du compte hôte.
Dans cet environnement Debian, Docker et Compose ont été installés depuis les
dépôts Debian existants ; le client est fourni par le paquet distinct `docker-cli`.
Un seul service sert l’interface et l’API, sans base ni proxy supplémentaires.

Pour consulter les journaux ou arrêter sans supprimer les données :

```sh
docker compose logs --tail=100 mijote
docker compose stop
docker compose start
```

Ne pas utiliser `docker compose down -v` : cela supprime le volume des données.

## Configuration et accès depuis le téléphone

La configuration locale est dans `.env`, exclu de Git. Les données sont dans le
volume nommé `mijote_data` de ce projet Compose. Aucun secret de session fixe n’est
nécessaire : les sessions opaques sont générées aléatoirement et hachées en base.

| Variable | Valeur locale | Rôle |
| --- | --- | --- |
| `MIJOTE_BIND` | `127.0.0.1` | Adresse d’écoute sur l’hôte |
| `MIJOTE_PORT` | `8080` | Port de l’application |
| `MIJOTE_ALLOWED_ORIGINS` | `http://localhost:8080,http://127.0.0.1:8080` | Origines autorisées à modifier les données |
| `MIJOTE_SECURE_COOKIE` | `false` | `true` impose HTTPS pour le cookie |

Pour un test sur un réseau privé de confiance, utiliser `MIJOTE_BIND=0.0.0.0` et
ajouter l’origine exacte du serveur à `MIJOTE_ALLOWED_ORIGINS`, par exemple
`http://IP_DU_SERVEUR:8080`. Appliquer avec `docker compose up -d`. Ne pas publier
ce port directement sur Internet et initialiser le compte avant d’ouvrir l’accès.

Pour un accès distant, utiliser le reverse proxy HTTPS existant ou un VPN privé.
Avec un proxy HTTPS, définir `MIJOTE_SECURE_COOKIE=true` et l’origine HTTPS exacte.
Le proxy doit transmettre vers le port local de Mijote et supporter les en-têtes
usuels ; aucun en-tête `X-Forwarded-*` n’est utilisé pour décider des permissions.
L’accès HTTP simple sur IP locale n’est pas chiffré ; le réserver à un test privé.

La PWA fournit un manifeste et un service worker. L’installation dans Chrome
nécessite **HTTPS ou localhost**, et dépend des critères du navigateur. HTTP sur
une IP locale ne suffit pas. Le shell public est conservé en cache ; les courses
hors connexion demandent une copie locale volontaire. Sur HTTP local, garder
l’onglet chargé avant de quitter le réseau : la réouverture autonome hors connexion
nécessite HTTPS ou localhost. Aucune API privée n’est mise en cache par le service worker.

## Premier parcours

1. Dans **Mon organisation**, définir les portions et les midis/soirs habituels.
   Le modèle s’applique seulement aux semaines créées ensuite. La semaine courante
   est créée à la première connexion. Si elle est vide, **Appliquer à cette semaine vide**
   permet d’y reprendre explicitement le modèle, sans écraser de repas. Ses créneaux
   restent modifiables directement.
2. Dans **Mes recettes**, créer les ingrédients puis une recette et ses quantités.
   Un intitulé simple est possible, sans mouvement automatique de stock.
3. Dans **Mes réserves**, ajouter les aliments déjà disponibles et leur emplacement.
4. Dans **Ma semaine**, choisir le repas. Un midi au travail peut devenir maison,
   sans modifier l’organisation habituelle. Passer hors maison conserve le plat.
5. Dans **Mes courses**, vérifier les manquants et cocher les achats dans le panier.
   **Terminer les courses** permet de corriger les quantités, choisir un remplacement
   ou signaler un article non trouvé avant l’entrée en stock.
6. Dans le repas, choisir **Ce repas est préparé**, vérifier les quantités consommées
   puis confirmer. Une confirmation répétée ne redéduit jamais les ingrédients.

Les réservations concernent tous les repas maison non préparés, dans l’ordre des
dates, y compris dans d’autres semaines. Définir un créneau hors maison ou retirer
son plat libère ses besoins. Les lots sont consommés par date limite puis ordre
d’entrée. Une date dépassée est signalée mais ne supprime pas le stock : la décision
reste manuelle. Un manque n’empêche pas la préparation et ne crée pas de quantité
négative. Le journal permet une correction manuelle si le stock était approximatif.

Conversions : g/kg et ml/l seulement ; les pièces sont une dimension distincte.
Les quantités sont stockées en milli-unités entières et les besoins arrondis au
millième supérieur. Les identifiants de confirmation sont conservés en base : une
action rejouée est idempotente, un même identifiant avec un autre contenu est refusé.
Les transactions SQLite sérialisent les confirmations concurrentes.

## Sauvegarder et restaurer

La base inclut recettes, planning, stocks, journal, compte et sessions : conserver
les sauvegardes dans un emplacement privé. Ne pas copier seulement le fichier
SQLite actif sans tenir compte du journal WAL.

Sauvegarde cohérente pendant le fonctionnement :

```sh
mkdir -p backups
umask 077
(set -C; docker compose exec -T mijote python -m app.backup backup - > backups/mijote-sauvegarde.sqlite3)
```

Choisir un nouveau nom à chaque sauvegarde : `set -C` refuse d’écraser la destination.
Le flux évite les différences d’identifiants utilisateur entre l’hôte et le conteneur.
Copier aussi `.env` séparément dans un emplacement privé pour conserver la configuration.

Restauration, après arrêt de l’application :

```sh
docker compose stop mijote
docker compose run --rm --no-deps -T mijote python -m app.backup restore - < backups/mijote-sauvegarde.sqlite3
docker compose up -d
```

Le volume persistant reste attaché au service éphémère. L’intégrité et le schéma
de la sauvegarde sont vérifiés. Un verrou refuse la restauration si le serveur
tourne encore. L’ancienne base est sauvegardée sous `pre-restore-*.sqlite3` dans le
volume avant remplacement. Les migrations sont rejouées au prochain démarrage.

## Développement local et tests

Python 3.13 et Node ≥ 20.19 (ou Node 22 LTS), avec npm et `python3-venv` :

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/pytest backend/tests -q
cd frontend
npm ci
npm run build
```

API, depuis la racine du projet :

```sh
MIJOTE_SECURE_COOKIE=false \
MIJOTE_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 \
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Interface, dans un second terminal : `cd frontend && npm run dev`. Ouvrir
http://localhost:5173 ; Vite transmet `/api` à FastAPI. La base locale est dans
`data/`, exclu de Git. Les versions directes Python sont dans `requirements.txt`,
les dépendances de production verrouillées dans `requirements-lock.txt`, et les
versions frontend dans `package-lock.json`.

## Limites actuelles

- Une seule maison et un compte familial ; pas de comptes individuels ni de récupération par courriel.
- Partage Android/PWA préparé pour une installation HTTPS, à valider sur l’appareil ; pas encore de codes-barres, OCR ou IA. L’import URL et le collage manuel restent disponibles.
- Les courses hors ligne ne confirment pas les achats : « Terminer les courses » exige le serveur. Une session valide est nécessaire à la synchronisation.
- Photos JPEG/PNG/WebP disponibles ; HEIC et animations non pris en charge. Aucun contenu importé n’est redistribué publiquement.
- L’ergonomie réelle sur Chrome/GNOME et Android doit être vérifiée manuellement ; aucun parcours graphique n’est simulé.

## Ce qui pourrait être ajouté

Ces pistes ne sont pas encore disponibles et ne constituent pas un calendrier de livraison :

- **Lecture de tickets de caisse** : photographier un ticket, reconnaître les articles
  et proposer des entrées en réserve, avec correction et validation avant tout ajout.
- **Scan de codes-barres** : retrouver les informations d’un produit pour faciliter
  la saisie des achats et des réserves.
- **Import depuis une photo ou une capture d’écran** : extraire le texte d’une recette
  par reconnaissance de caractères (OCR), puis vérifier les ingrédients et les étapes.
- **Import de fichiers de recettes** : reprendre un carnet existant dans des formats
  à définir, avec aperçu et contrôle des doublons.
- **Proposition d’un menu complet** : suggérer des repas pour les créneaux maison vides,
  selon les goûts, le temps disponible et les réserves, avec validation avant application.

Le partage Android en HTTPS reste à vérifier sur un appareil réel.

## Notices à conserver dans une distribution

Conserver `LICENSE`, `NOTICE`, `COMMERCIAL.md`, `ASSETS.md`,
`THIRD_PARTY_NOTICES.txt` et `THIRD_PARTY_MANIFEST.json` avec les sources.
Les copies dans `frontend/public/legal/` sont automatiquement reprises par la
construction frontend existante et par l’image Docker, sans changement de l’interface.

Après mise à jour des documents juridiques, depuis la racine du projet :

```sh
python3 scripts/sync_legal.py
python3 scripts/sync_legal.py --check
```

Avant une nouvelle distribution, toute modification de dépendance exige de
réexaminer son entrée dans l’inventaire et de mettre à jour les textes tiers avec
ceux de la version réellement distribuée. Le script de synchronisation ne refait
pas cet audit et ne choisit pas de licence pour une nouvelle dépendance.

L’inventaire concerne les dépendances applicatives auditées. Une publication
ultérieure d’une image Docker complète doit aussi conserver les notices des
composants système et satisfaire leurs obligations propres ; cet inventaire
n’est pas une nomenclature exhaustive des images de base.
