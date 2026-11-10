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
- Portions familiales par défaut et exception par repas ; plusieurs plats et accompagnements.
- Intitulés simples, plats improvisés et recettes avec ingrédients et quantités.
- Réserves par emplacement et date facultative, corrections et journal.
- Besoins calculés entre les repas sans déduire le stock lors de la planification.
- Courses calculées et ajouts manuels ; panier distinct de la confirmation d’achat.
- Confirmation des quantités réellement achetées ou consommées, sans double mouvement.

Les changements sont décrits dans [CHANGELOG.md](CHANGELOG.md) et les
vérifications dans [VALIDATION.md](VALIDATION.md).

## Réserves et emplacements

Dans **Mes réserves**, cliquez sur un aliment pour modifier son nom, sa quantité,
son unité compatible, son emplacement et sa date limite. Le nom saisi est propre
à ce lot : il ne renomme pas l’ingrédient dans toutes les recettes. L’historique et
les quantités déjà consommées sont conservés. Si le lot change pendant l’édition,
fermez puis rouvrez sa fiche avant de recommencer.

Le sélecteur affiche tous les emplacements sans devoir taper. **Nouvel emplacement**
permet d’en enregistrer un, même vide. Le même choix est proposé à l’ajout d’un
aliment et lors de la confirmation des achats.

Dans **Mes courses**, **Regrouper des semaines** permet de sélectionner de deux à
douze semaines déjà créées. Les aliments communs sont additionnés sans compter
deux fois les réserves. Les listes d’origine restent conservées. Le panier, la
confirmation des achats et l’impression utilisent alors les semaines sélectionnées.
**Revenir à cette semaine** quitte le regroupement sans supprimer les listes.
Le regroupement n’est pas une copie de données ni un déplacement des repas.

Le regroupement reste disponible en ligne et à l’impression. La copie de courses
hors connexion reste limitée à une seule semaine, comme auparavant.

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

Dans **Mes recettes → Importer une recette**, utiliser un lien public ou coller
le texte d’une recette. Une prévisualisation permet de corriger les portions,
les ingrédients, les quantités et les étapes avant d’enregistrer.

Seules les lignes quantifiées et validées participent aux besoins. Une photo
peut être conservée lorsqu’elle est disponible. L’import ne modifie pas le stock.
La compatibilité dépend de la source ; le collage de texte reste disponible en
cas d’échec. Les contenus et leur attribution restent dans votre instance privée.

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

## Découvrir de nouvelles idées

Dans **Ma semaine → Des idées**, une découverte peut être consultée, remplacée
par une autre proposition ou importée après vérification. Rien n’est enregistré
ni ajouté aux courses automatiquement.

**Ajouter ou gérer les liens pour les idées** permet de conserver jusqu’à 20 liens
personnels, puis de choisir une source. Les liens sont vérifiés avant ajout et
inclus dans les sauvegardes. Leur disponibilité et leur compatibilité peuvent varier.

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

Une photo disponible lors d’un import peut être vérifiée avant conservation.
Vous pouvez aussi ajouter, remplacer ou retirer une photo depuis votre appareil.

Formats : **JPEG, PNG et WebP fixes**, jusqu’à **12 Mio et 24 mégapixels** en ajout
manuel. HEIC, SVG et animations ne sont pas acceptés ; exporter en JPEG si nécessaire.
Les images sont orientées, réduites à 1 600 pixels maximum sur leur grand côté et
réencodées en JPEG, à 512 Kio maximum. Les métadonnées EXIF/GPS, commentaires et
profils incorporés ne sont pas conservés. La photo d’origine n’est pas stockée.

Les photos sont privées, servies après authentification et conservées dans la base
SQLite. **La sauvegarde/restauration habituelle inclut aussi les photos**, sans
répertoire supplémentaire à copier. Leur ajout augmente donc la taille de la base
et des sauvegardes. Les listes de courses hors connexion ne contiennent pas les photos.

Les images sont vérifiées et réencodées avant leur conservation. La source et
l’attribution disponibles sont conservées. Respecter les droits des contenus et
les garder dans l’usage privé du foyer.

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

Pour corriger un repas marqué préparé par erreur, ouvrir sa case dans le calendrier,
choisir **Annuler « Repas préparé »**, puis **Confirmer l’annulation**. Le repas
redevient modifiable et entre à nouveau dans le calcul des courses. Les quantités
réellement déduites sont remises dans leurs lots d’origine ; les manques signalés
lors de la préparation ne créent aucun stock fictif. La recette actuelle n’est
pas utilisée pour deviner la consommation passée.

Le repas annulé quitte l’historique des préparations ; le journal des réserves
conserve les déductions et leur annulation. Il peut ensuite être marqué préparé
à nouveau avec la confirmation habituelle. Un double envoi ne restitue jamais le
stock deux fois. Une annulation devenue ancienne ne peut pas défaire une nouvelle
préparation. Si la confirmation d’origine est absente, l’annulation automatique
est refusée avec un message explicite ; les données restent inchangées.

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

## Composer un repas : entrée, plat, dessert

Ouvrir une case du calendrier pour choisir le plat principal habituel. Dans
**Accompagnement**, la liste propose maintenant **Recettes** et **Ingrédients** :
vous pouvez sélectionner directement du riz, des pâtes, des pommes de terre ou
un autre ingrédient du répertoire, puis indiquer sa quantité et son unité.

Le bouton **+ Ajouter un plat ou un ingrédient** ajoute une ligne au même repas.
Choisir son type **Entrée**, **Plat** ou **Dessert**, puis une recette, un ingrédient
quantifié ou un intitulé libre. Répéter pour compléter le menu, puis enregistrer.
Chaque ligne peut être retirée ; jusqu’à 20 ajouts sont possibles par repas.
Les catégories sont affichées dans l’ordre entrée, plat, dessert dans le calendrier
et le menu imprimé. Un intitulé libre décrit le menu sans créer de besoin fictif.

Les quantités des **recettes** sont ajustées aux portions du repas. Pour un
**ingrédient choisi directement**, la quantité saisie est le **total pour ce repas** :
par exemple 400 g de riz pour toute la famille. Si vous changez les portions,
ajustez vous-même ce total. Les ingrédients communs à plusieurs plats ou repas
sont additionnés, puis les réserves sont prises en compte sans double comptage.

« Ce repas est préparé » confirme l’ensemble du repas ; les quantités réellement
utilisées restent vérifiables avant validation. Annuler cette préparation restaure
les déductions de l’ensemble du repas. Les copies, réutilisations et l’historique
conservent les ajouts et leur catégorie. Un créneau contenant seulement des ajouts
ou un accompagnement est considéré comme rempli et n’est pas écrasé par une copie.
Les choix restent enregistrés si le repas passe temporairement hors maison.

La migration 0007 conserve les plats principaux et accompagnements existants,
et ajoute les éléments du menu dans des tables dédiées, incluses dans les
sauvegardes habituelles. Faire une sauvegarde avant la mise à jour.

## Imprimer la liste de courses

Dans **Mes courses**, choisir **Imprimer la liste**. La feuille A4 portrait contient
la semaine, les articles, les quantités et des cases à cocher, avec l’état actuel
du panier. Les ajouts personnels sont également inclus. Depuis la fenêtre du
navigateur, choisir une imprimante ou **Enregistrer au format PDF**.

L’impression utilise la liste affichée, sans modifier les courses ni les réserves.
Les cases cochées sur papier ne se synchronisent pas automatiquement. L’impression
du menu reste accessible séparément dans **Ma semaine → Imprimer la semaine**.
Le résultat sur l’imprimante et le téléphone utilisés reste à vérifier manuellement.

## Corriger les noms et éviter les doublons d’ingrédients

Dans **Mes recettes → Mon répertoire d’ingrédients**, cliquer sur le nom ou le
crayon pour corriger une faute d’orthographe. Enregistrer conserve le même
identifiant : recettes, réserves et courses restent liés à cet ingrédient. La
croix sert uniquement à supprimer une entrée inutilisée.

Lors d’une création ou d’un import, Mijote signale les noms proches, par exemple
**tomate / tomates**. Choisir **Utiliser « tomate »** pour confirmer qu’il s’agit
du même aliment ; la variante sera reconnue ensuite. Un nom déjà connu ou un
alias confirmé réutilise l’ingrédient existant. Si les aliments sont réellement
différents, choisir **Créer un ingrédient distinct**. Cette distinction reste
explicite : les accents et qualificatifs sont conservés ; « tomate », « tomate
séchée », « sauce tomate », « pâtes » et « pâtés » ne sont pas réunis au hasard.
Les propositions de pluriel sont prudentes et ne couvrent pas toutes les formes
irrégulières ni toutes les fautes d’orthographe.

Pour réunir deux doublons existants :

1. Ouvrir celui qui doit rejoindre un autre ingrédient et choisir
   **Fusionner avec un autre ingrédient**.
2. Sélectionner le nom à conserver, puis **Vérifier la fusion**.
3. Vérifier les noms et les références affichées, puis **Confirmer la fusion**.

La fusion exige le même type de mesure (poids, volume ou pièces). Dans une recette
qui contient les deux ingrédients, leurs quantités sont additionnées dans l’unité
de base. Les lots restent séparés avec leurs quantités, emplacements et dates ;
les articles manuels et les mouvements sont conservés. Les courses sont recalculées
et les articles calculés concernés doivent être vérifiés puis cochés à nouveau.

L’ancien nom devient un alias et l’ancienne entrée disparaît du répertoire actif.
Les identifiants historiques sont conservés pour protéger les références et les
confirmations déjà envoyées. Un ancien onglet ou une copie hors connexion peut
signaler un conflit : synchroniser et vérifier la version actuelle, sans effacer
une file de modifications non examinée. Si des données changent après l’aperçu,
un nouvel aperçu est demandé avant la fusion.

Faire une sauvegarde avant une fusion importante : il n’existe pas d’annulation
automatique de cette action. La migration 0006 ajoute les alias et liens de fusion
sans fusionner automatiquement les ingrédients existants. Ils sont inclus dans
les sauvegardes habituelles. Aucune dépendance supplémentaire n’est nécessaire.

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
