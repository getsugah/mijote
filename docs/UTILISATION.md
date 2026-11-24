# Utiliser Mijote

Le menu principal donne accès à **Menus**, **Recettes**, **Stocks**, **Courses**,
**Suggestions**, **Historique** et **Paramètres**. Les anciennes versions
utilisaient les libellés « Ma semaine », « Mes recettes », « Mes réserves »,
« Mes courses » et « Mon organisation ».

## Premier parcours

1. Dans **Paramètres**, définir les portions et les midis/soirs habituels.
   Ce modèle s’applique seulement aux semaines créées ensuite. La semaine courante
   est créée à la première connexion. Si elle est vide, **Appliquer à cette semaine vide**
   permet d’y reprendre explicitement le modèle, sans écraser de repas. Ses créneaux
   restent modifiables directement.
2. Dans **Recettes**, créer les ingrédients puis une recette et ses quantités.
   Un intitulé simple est possible, sans mouvement automatique de stock.
3. Dans **Stocks**, ajouter les aliments déjà disponibles et leur emplacement.
4. Dans **Menus**, choisir le repas. Un midi au travail peut devenir maison,
   sans modifier l’organisation habituelle. Passer hors maison conserve le plat.
5. Dans **Courses**, vérifier les manquants et cocher les achats dans le panier.
   **Terminer les courses** permet de corriger les quantités, choisir un remplacement
   ou signaler un article non trouvé avant l’entrée en stock.
6. Dans le repas, choisir **Ce repas est préparé**, vérifier les quantités consommées
   puis confirmer. Une confirmation répétée ne redéduit jamais les ingrédients.

## Menus

- Planning sur sept jours, midi et soir, selon un modèle de présence modifiable.
- Portions familiales par défaut et exception par repas.
- Intitulés simples, plats improvisés et recettes avec ingrédients et quantités.

Sur ordinateur, sélectionner un créneau affiche ses détails à droite ; **Modifier le repas**
ouvre le formulaire. Sur téléphone, toucher le créneau ouvre directement ce formulaire.
Les miniatures proviennent des photos des recettes ; une marmite remplace les photos
absentes. Les repas au travail ou à l’extérieur conservent leurs choix enregistrés
sans les afficher comme des repas à cuisiner.

### Composer un repas : entrée, plat, dessert

Ouvrir une case du calendrier pour choisir le plat principal. Dans **Accompagnement**,
la liste propose **Recettes** et **Ingrédients** : on peut sélectionner directement
du riz, des pâtes ou un autre ingrédient du répertoire, avec sa quantité et son unité.

**+ Ajouter un plat ou un ingrédient** ajoute une ligne au même repas. Choisir son type
**Entrée**, **Plat** ou **Dessert**, puis une recette, un ingrédient quantifié ou un
intitulé libre. Jusqu’à 20 ajouts sont possibles par repas. Les catégories sont affichées
dans l’ordre entrée, plat, dessert. Un intitulé libre ne crée aucun besoin fictif.

Les quantités des **recettes** sont ajustées aux portions du repas. Pour un
**ingrédient choisi directement**, la quantité saisie est le **total pour ce repas**
(par exemple 400 g de riz pour toute la famille) : l’ajuster soi-même si les portions
changent. Les ingrédients communs sont additionnés, puis les stocks sont pris en
compte sans double comptage.

« Ce repas est préparé » confirme l’ensemble du repas. Les copies, réutilisations et
l’historique conservent les ajouts et leur catégorie. Un créneau contenant seulement
des ajouts ou un accompagnement est considéré comme rempli et n’est pas écrasé par
une copie.

### Annuler une préparation

Pour corriger un repas marqué préparé par erreur, ouvrir sa case, choisir
**Annuler « Repas préparé »**, puis **Confirmer l’annulation**. Le repas redevient
modifiable et entre à nouveau dans le calcul des courses. Les quantités réellement
déduites sont remises dans leurs lots d’origine ; les manques signalés lors de la
préparation ne créent aucun stock fictif.

Le repas annulé quitte l’historique ; le journal des stocks conserve les déductions
et leur annulation. Un double envoi ne restitue jamais le stock deux fois. Une
annulation devenue ancienne ne peut pas défaire une nouvelle préparation. Si la
confirmation d’origine est absente, l’annulation est refusée avec un message explicite.

### Copier une semaine

Dans **Menus**, **Copier** ouvre **Copier une semaine** : choisir le lundi d’une semaine
existante, examiner l’aperçu et confirmer. Seuls les créneaux maison vides sont remplis ;
aucun repas existant, état préparé ou mouvement de stock n’est recopié.

### Calendrier et impression

Les jours fériés nationaux français ont un en-tête coloré et leur nom. Les dates sont
calculées localement. Alsace-Moselle et territoires ultramarins ne sont pas inclus.
Ce repérage ne change ni les statuts des repas ni les stocks. Référence :
[calendrier officiel](https://calendrier.api.gouv.fr/jours-feries/metropole/2026.json).

Dans **Menus**, **Imprimer** ouvre l’impression du navigateur en A4 paysage : les sept
jours, midi/soir, plats, accompagnements, portions et présence. Une case hors maison
affiche son statut. Le navigateur permet aussi **Enregistrer au format PDF**.

## Recettes

Dans **Recettes** : bouton favori, filtres favoris/à tester/catégorie/tag et **Mon avis**
pour l’appréciation, le commentaire et la variante personnelle. Les variantes sont des
notes : elles ne changent pas les ingrédients calculés. Une recette importée est marquée
« À tester » ; sa préparation retire ce statut.

### Importer une recette

Dans **Recettes → Importer une recette**, utiliser un lien public ou coller le texte
d’une recette. Une prévisualisation permet de corriger les portions, les ingrédients,
les quantités et les étapes avant d’enregistrer.

Seules les lignes quantifiées et validées participent aux besoins. L’import ne modifie
ni le stock ni les courses. La compatibilité dépend de la source ; le collage de texte
reste disponible en cas d’échec. Le champ **Source** d’une recette conserve seulement
l’URL : utiliser **Importer une recette** pour lire un lien.

Planifier la recette ajuste ses quantités aux portions du repas, puis calcule les
manquants après réservation du stock. Exemple : 400 g pour quatre portions deviennent
600 g pour six ; avec 200 g libres en stock, 400 g figurent aux courses. Les ingrédients
restés uniquement dans les notes sont hors calcul.

### Partager une recette depuis Android

Avec Mijote installé depuis Chrome sur Android (PWA en **HTTPS**), ouvrir une recette
puis **Partager → Mijote**. Le lien ou le texte préremplit le formulaire d’import.
Si nécessaire, se connecter d’abord : le partage attend dans la page. Choisir
**Prévisualiser**, vérifier puis confirmer. Rien n’est téléchargé ni enregistré sans
confirmation. Plusieurs liens sans source explicite demandent de choisir la source.
Les images et fichiers partagés ne sont pas acceptés.

Avec une adresse HTTP locale, copier le lien puis utiliser **Importer une recette**.
Le serveur doit être accessible pour recevoir le partage. Les données arrivent par POST,
ne sont pas mises en cache et restent en mémoire pendant la connexion : fermer ou
recharger la page peut les perdre. Voir les
[conditions de Chrome](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target).

### Photos

Le bouton **Photo** d’une recette permet de choisir une image depuis l’appareil,
de vérifier l’aperçu puis **Conserver cette photo**, de la remplacer ou de la retirer.
Pour une nouvelle recette manuelle, l’enregistrer d’abord puis ouvrir son bouton Photo.
Lors d’un import, la photo proposée doit être cochée explicitement.

Formats : **JPEG, PNG et WebP fixes**, jusqu’à **12 Mio et 24 mégapixels**. HEIC, SVG
et animations sont refusés. Les images sont orientées, réduites à 1 600 pixels sur leur
grand côté et réencodées en JPEG (512 Kio maximum). Les métadonnées EXIF/GPS ne sont
pas conservées, ni la photo d’origine.

Les photos sont privées, servies après authentification et stockées dans la base
SQLite : la sauvegarde habituelle les inclut. Elles augmentent la taille des sauvegardes.
La source et l’attribution disponibles sont conservées ; respecter les droits des
contenus et les garder dans l’usage privé du foyer.

### Tags, titre et photo proposés

Dans l’éditeur et dans la prévisualisation d’import, **Tags et propositions** →
**Proposer un titre et des tags** suggère un titre et des tags à partir du nom, des
ingrédients et du temps. Ces propositions sont calculées localement par des règles
fixes, sans service d’IA.

Choisir **Utiliser ce titre**, cliquer sur les tags souhaités ou saisir ses propres
tags, puis enregistrer. Les propositions seules n’écrivent rien. Limites : 20 tags par
recette, 50 caractères par tag. Aucun classement alimentaire ni contrôle d’allergènes
n’est garanti.

Pour une recette avec un lien source, **Proposer la photo du site source** réutilise
les contrôles de téléchargement existants. Vérifier l’image et sa source avant de la
choisir. Une photo existante reste conservée sans nouveau choix.

La section **Un titre et sa photo** permet aussi de rechercher un plat sur TheMealDB
(**Proposer des titres avec photo**) et d’en reprendre le titre, des tags ou la photo
après prévisualisation. Ce service est externe : voir
[INSTALLATION_AVANCEE.md](INSTALLATION_AVANCEE.md#recherche-themealdb).

Parcours de test : [TAGS_RECETTES.md](TAGS_RECETTES.md).

### Corriger les noms et fusionner les doublons d’ingrédients

Dans **Recettes → Mon répertoire d’ingrédients**, cliquer sur le nom ou le crayon pour
corriger une faute. L’identifiant est conservé : recettes, stocks et courses restent liés.
La croix supprime uniquement une entrée inutilisée.

À la création ou à l’import, Mijote signale les noms proches (par exemple
**tomate / tomates**). Choisir **Utiliser « tomate »** pour confirmer qu’il s’agit du
même aliment, ou **Créer un ingrédient distinct**. Les accents et qualificatifs sont
conservés : « tomate séchée », « sauce tomate », « pâtes » et « pâtés » ne sont pas
réunis au hasard.

Pour réunir deux doublons existants :

1. Ouvrir celui qui doit disparaître et choisir **Fusionner avec un autre ingrédient**.
2. Sélectionner le nom à conserver, puis **Vérifier la fusion**.
3. Vérifier les références affichées, puis **Confirmer la fusion**.

La fusion exige le même type de mesure (poids, volume ou pièces). Les quantités d’une
recette contenant les deux ingrédients sont additionnées ; les lots de stock restent
séparés. Les courses sont recalculées et les articles concernés doivent être cochés
à nouveau. L’ancien nom devient un alias. **Il n’existe pas d’annulation automatique** :
faire une sauvegarde avant une fusion importante.

## Stocks

- Aliments par emplacement et date facultative, corrections et journal.
- Les lots sont consommés par date limite puis ordre d’entrée.
- Une date dépassée est signalée mais ne supprime pas le stock.
- Un manque n’empêche pas la préparation et ne crée pas de quantité négative.

Dans **Stocks**, cliquer sur un aliment pour modifier son nom, sa quantité, son unité,
son emplacement et sa date limite. Le nom saisi est propre à ce lot : il ne renomme
pas l’ingrédient dans les recettes. Si le lot change pendant l’édition, fermer puis
rouvrir sa fiche.

Le sélecteur affiche tous les emplacements. **Nouvel emplacement** permet d’en créer un,
même vide. **Gérer les emplacements** permet de renommer un emplacement ou de le supprimer
après avoir choisi où déplacer ses articles ; les quantités restent identiques.

Les besoins réservent le stock pour tous les repas maison non préparés, dans l’ordre des
dates, y compris d’autres semaines. Définir un créneau hors maison ou retirer son plat
libère ses besoins. Planifier ne déduit jamais le stock.

## Courses

- Manquants calculés et ajouts manuels ; panier distinct de la confirmation d’achat.
- **Terminer les courses** confirme les quantités réellement achetées, sans double mouvement.

**Regrouper des semaines** sélectionne de deux à douze semaines déjà créées. Les aliments
communs sont additionnés sans compter deux fois les stocks. Le panier, la confirmation et
l’impression utilisent alors ces semaines. **Revenir à cette semaine** quitte le
regroupement sans rien supprimer.

**Imprimer la liste** produit une feuille A4 portrait avec la semaine, les articles,
les quantités, des cases à cocher et l’état du panier. L’impression ne modifie rien ;
les cases cochées sur papier ne se synchronisent pas.

**Emporter ma liste / courses hors connexion** enregistre une copie locale pour les
courses sans réseau, limitée à une semaine. Voir
[COURSES_HORS_LIGNE.md](COURSES_HORS_LIGNE.md).

## Suggestions

**Suggestions** propose des idées selon quatre modes : varier, utiliser le stock, rapide
et découverte, avec une justification et **Une autre idée**. Le moteur utilise le carnet,
les préparations, les catégories et les stocks libres. **Ne plus proposer** retire une
recette des suggestions. Aucune IA n’est utilisée.

Une découverte peut être consultée, remplacée ou importée après vérification. Rien n’est
enregistré ni ajouté aux courses automatiquement. **Ajouter ou gérer les liens pour les
idées** conserve jusqu’à 20 liens personnels, vérifiés avant ajout et inclus dans les
sauvegardes.

## Historique

Repas réellement confirmés, avec noms et portions au moment de la préparation. Pour les
anciennes confirmations, l’heure inconnue est indiquée. Choisir un créneau maison vide de
la semaine affichée pour replanifier un repas.

## Paramètres

Portions, présence habituelle et, dans **Apparence**, palette claire ou sombre (conservée
dans ce navigateur).

## Détails de calcul

Conversions : g/kg et ml/l seulement ; les pièces sont une dimension distincte. Les
quantités sont stockées en milli-unités entières et les besoins arrondis au millième
supérieur. Les identifiants de confirmation sont conservés : une action rejouée est
idempotente, un même identifiant avec un autre contenu est refusé.
