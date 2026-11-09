# Mijote — plan de livraison

## Périmètre et inspection

Cahier des charges lu intégralement : ../MIJOTE_CODEX.md. Aucun projet Mijote préexistant trouvé dans le répertoire de développement. Les autres projets et leurs caches sont conservés. Phase A uniquement ; aucune publication distante. Interface française aubergine, orange et crème.

## Architecture

- Vue 3, TypeScript et Vite pour l’interface responsive. Manifeste PWA et cache du shell uniquement ; la synchronisation des courses hors ligne appartient à la phase B.
- FastAPI/Pydantic, API /api/v1, service métier séparé des routes.
- SQLite : quantités décimales représentées en milli-unités entières ; g/kg et ml/l convertibles, pièces séparées. Transactions BEGIN IMMEDIATE, clés étrangères et journal WAL. Alembic pour les migrations ; accès aux données isolé dans backend/app/db.py.
- Une image Docker multi-stage sert le frontend et l’API sur la même origine. Un seul service Compose, utilisateur non privilégié et volume persistant. Port lié à localhost par défaut ; accès distant uniquement via reverse proxy HTTPS ou VPN.
- Premier compte familial créé depuis l’interface au premier démarrage, sans mot de passe prédéfini. Scrypt, sessions opaques hachées en base, cookies HttpOnly/SameSite, CSRF et contrôle d’origine. Aucune inscription après initialisation.

## Modèle de données

Compte et sessions ; réglages familiaux et modèle de présence (14 créneaux) ; semaines et repas datés ; ingrédients normalisés ; recettes et lignes d’ingrédients ; lots de stock par emplacement ; mouvements de stock ; articles manuels de courses ; opérations d’achat et de préparation idempotentes.

Un repas garde ses choix lorsqu’il passe hors maison. Les besoins sont calculés à la lecture, dans l’ordre des repas : seuls les repas maison non préparés réservent logiquement le stock. La planification ne crée aucun mouvement. Préparer un repas déduit une seule fois les quantités confirmées ; une insuffisance est signalée sans bloquer et ne produit pas de stock négatif. Les achats cochés restent hors stock jusqu’à confirmation. Les identifiants d’opération, contraintes uniques et transactions empêchent les doubles confirmations et les confirmations concurrentes contradictoires.

## Jalons

1. Fondations : configuration, migrations, authentification, image et Compose.
2. Métier : ingrédients/recettes, stock et mouvements, planning selon modèle, portions et réservations.
3. Parcours MVP : besoins et courses, panier et quantités réellement achetées, confirmations idempotentes.
4. Interface : connexion/initialisation, semaine midi/soir, recettes, stock, courses, réglages ; adaptation mobile.
5. Vérifications : tests API/métier (scénario d’acceptation, unités, réservation, concurrence et idempotence), typecheck/build frontend, Compose et test de démarrage si Docker disponible. Journal et procédure de sauvegarde/restauration.

## Vigilance et limites assumées

Pas d’import Internet, OCR, scan, suggestions automatiques, impression, copie de semaine ou synchronisation hors ligne en phase A. Sources URL et modèle produit distinct préparés sans fetch distant. Aucune conversion masse/volume sans information spécifique. Pas de cache des réponses API privées dans le service worker. Une PWA installable exige HTTPS ou localhost ; l’accès HTTP sur IP locale n’est pas présenté comme équivalent. Les essais visuels sur Chrome/Android restent manuels conformément aux consignes locales.

## État de livraison

Les cinq jalons de phase A sont implémentés et leurs contrôles automatisés sont
réalisés. L’image `mijote:0.1.0` est disponible localement. La recette visuelle sur
les appareils de l’utilisatrice reste manuelle ; voir docs/RECETTE_MANUELLE.md et
VALIDATION.md. À ce jalon initial, les phases B/C n’avaient pas encore été commencées.

## Ajouts ciblés demandés après validation des bases

Version 0.1.1 : repérage des jours fériés nationaux français et impression de la
semaine A4. L’impression, initialement prévue en phase B, est livrée sur demande
explicite après mise en service de la phase A. L’import automatique de recettes
reste en phase C ; une URL saisie reste une attribution de source.

## Itération import URL — demande explicite après la version 0.1.1

Périmètre : URL publique et collage manuel, priorité Schema.org Recipe JSON-LD,
repli HTML générique, aperçu entièrement modifiable et confirmation explicite.
Conserver URL, auteur et texte d’origine des ingrédients. Aucun ingrédient ni
recette enregistré lors de l’analyse ; confirmation atomique seulement, aucun
mouvement de stock. Quantités ambiguës sans conversion inventée, à vérifier.

Sécurité réseau : HTTP/HTTPS sur ports standards, toutes les adresses DNS publiques
validées et connexion épinglée sur l’IP approuvée avec certificat TLS du vrai nom,
chaque redirection revalidée. Durée totale, volume compressé/décompressé, profondeur
HTML/JSON et imports concurrents limités. Pas de cookie de consentement ni de
contournement de compte/CAPTCHA. La vérification de session de l’aperçu ferme sa
transaction SQLite avant le téléchargement pour ne pas bloquer la maison.

Migration additive pour auteur/source et ingrédients textuels ; formulaire courant
réutilisé, import dans une fenêtre dédiée. Tests SSRF, parseurs multi-formats,
validation sans écriture, atomicité et conservation des données existantes. Vérifier
quelques pages publiques, construire et tester un conteneur isolé avant sauvegarde
et mise à jour LAN. Aucun partage Android, OCR ou autre automatisation dans cette itération.

### État de l’itération import

URL et collage livrés en 0.2.0, avec migration additive 0002, aperçu sans écriture,
association manuelle au répertoire et confirmation transactionnelle idempotente.
80 tests backend et 7 tests frontend réussis ; lecture publique vérifiée sur trois
sites, dont un par extraction HTML générique. Parcours HTTP d’import vérifié dans
un conteneur isolé, sans créer de recette dans la maison réelle. Aucun développement
du partage Android, des codes-barres, de l’OCR ou de l’IA.

## Phase B — confort, inspiration et courses hors ligne

Demande explicite de poursuite après la version 0.2.0, bases et import déjà testés.
Préserver les recettes, opérations idempotentes, réservations et la charte actuelles.

1. Migration additive 0003 : préférences de recette (favori, à tester, appréciation,
   catégorie, commentaire, variante), historique figé des repas réellement préparés,
   identité de la maison et révisions des articles de courses. Les anciennes
   confirmations sont reprises sans inventer d’heure de préparation.
2. Historique consultable, édition des préférences, filtres et suggestions déterministes
   varier/stock/rapide/découverte ; exclusion de ne_plus_proposer et justification
   lisible. Historique fondé sur les préparations, stock libre après réservations.
3. Aperçu puis copie d’un menu uniquement vers les créneaux maison vides de la
   semaine cible ; présences, repas existants et états préparés conservés. Réutilisation
   explicite d’un repas sans recopier son historique ni ses déductions.
4. Courses hors ligne ciblées : copie locale volontaire IndexedDB, panier et articles
   manuels éditables, file d’opérations UUID persistante, synchronisation authentifiée.
   Aucune confirmation d’achat ou déduction de stock hors connexion. Préconditions
   par article : en cas de changement serveur, conflit visible à résoudre, sans
   écrasement silencieux. File liée à l’identité de la maison, jamais au mot de passe.
   La déconnexion efface la copie locale seulement après accord explicite si une file
   attend son envoi. Les réponses API ne sont pas mises en cache par le service worker.
5. Tests métier, concurrence, copie sans écrasement, suggestions et réconciliation
   hors ligne ; build, instance Compose isolée, sauvegarde puis mise à jour LAN.
   Journal, documentation du conflit et recette Android manuelle.

HTTPS ou localhost est requis pour le service worker et une réouverture autonome
hors ligne. Sur l’adresse HTTP LAN actuelle, prise en charge de la liste chargée
et conservée dans un onglet ; ne pas annoncer une PWA installable hors ligne sur
cette origine. Impression déjà livrée et conservée. Aucune IA, OCR, code-barres,
notification distante ou génération automatique de toute une semaine.

### État de développement de la phase B

Les cinq jalons sont implémentés. Les validations métier, migrations et sauvegardes
passent (91 tests backend), ainsi que le rendu, le stockage local, les conflits et
le cache public (19 tests frontend). Image 0.3.0 construite et parcours HTTP isolé
validé. L’impression et l’import existants sont conservés. Le déploiement familial
est précédé d’une sauvegarde privée ; les validations visuelles Android restent
manuelles. Les fonctions avancées hors de cette phase ne sont pas commencées.

Mise en service 0.3.0 effectuée : sauvegarde privée, même volume et compte conservés,
migration 0003 et intégrité contrôlées, service sain et interface LAN vérifiée.
Aucun push ni publication. Voir VALIDATION.md pour les preuves et limites.

## Phase C — partage de recettes, première itération

Après validation mobile de la 0.3.1, poursuivre par le partage Android/PWA, l’import
URL et le collage étant déjà disponibles. Ni code-barres, OCR ni IA dans ce jalon.

- Déclarer une cible de partage POST pour titre, texte et URL dans le manifeste.
- Réception bornée sans authentification préalable, sans écriture en base ni fetch
  distant ; contenu transmis dans une page HTML non cachable avec données JSON
  inertes et échappées, jamais dans une URL ou un cache partagé.
- Garder le partage en mémoire pendant la connexion, puis préremplir l’import
  existant. Une action explicite déclenche l’analyse, la confirmation habituelle
  reste nécessaire pour enregistrer. Annulation efface le partage en mémoire.
- Reconnaître les URL reçues dans texte ou titre, refuser les protocoles dangereux,
  conserver le texte et signaler plusieurs liens pour laisser le choix.
- Tests des limites, absence d’écriture/fetch, échappement et du préremplissage ;
  compilation, conteneur isolé, sauvegarde et mise à jour du service.
- Partage natif à valider sur Android avec PWA installée en HTTPS. Sur HTTP LAN,
  conserver le collage ; aucun proxy ou certificat n’est configuré sans demande.

### État de l’itération partage

Implémentation et validations automatisées terminées : 101 tests backend,
28 tests frontend, build TypeScript/Vite/Docker et réception HTTP isolée réussis.
Le partage natif reste à valider manuellement après installation Android en HTTPS.
L’adresse HTTP locale conserve le collage. Aucun développement OCR/code-barres/IA.

Version 0.4.0 mise en service après sauvegarde privée vérifiée. Compte et volume
conservés, schéma 0003 inchangé, API et fichiers LAN contrôlés. Recette native HTTPS
Android encore manuelle ; le collage reste disponible sur HTTP local.

## Photos de recettes — itération 0.5.0

- Réutiliser les recettes, le formulaire d’import et le téléchargement public sécurisé.
- Ajouter une table de photos JPEG normalisées liée aux recettes (BLOB borné et
  métadonnées de source/attribution) ; aucune donnée binaire dans les tableaux JSON.
  Les sauvegardes SQLite existantes contiennent ainsi aussi les photos.
- Téléversement manuel JPEG/PNG/WebP, aperçu, remplacement et retrait explicites.
  Décodage borné avec Pillow, correction d’orientation, redimensionnement, réencodage
  et suppression des métadonnées. Pas de SVG, GIF animé ou HEIC dans ce jalon.
- À l’import, proposer l’image déclarée par la recette ou les métadonnées de page,
  télécharger par le mécanisme SSRF existant et montrer une prévisualisation locale.
  Choix de conservation avant confirmation atomique de la recette et de sa photo.
  Échec de photo non bloquant pour le texte ; conserver source et attribution.
- Tests des formats/tailles/métadonnées, accès authentifié, transactions, sauvegarde,
  extraction et réseau ; rendu et compilation ; validation Compose isolée avant
  sauvegarde privée et mise à jour du foyer. Aucune donnée réelle en fixture.

### État de l’itération photos

Version 0.5.0 développée et mise en service après sauvegarde privée. 121 tests
backend, 31 tests frontend, compilation et parcours HTTP isolé réussis ; une photo
publique a été proposée et normalisée sans enregistrer la recette. Schéma 0004,
compte et volume conservés, intégrité contrôlée. La sauvegarde SQLite contient les
photos. Sélection et confort sur le téléphone restent à confirmer manuellement.

## Installateur de déploiement

Réutiliser Dockerfile, Compose et volume existants sans changement métier. Ajouter
un script Bash avec configuration initiale privée, relance sans écrasement, mise
à jour Git en avance rapide et désinstallation confirmée sans suppression du volume.
Valider la syntaxe et les parcours avec des outils simulés et des données fictives ;
ne pas toucher au service familial ni automatiser l’interface ZimaOS.

## Découverte web dans les idées

Ajouter une recherche volontaire sur un premier index public compatible ; ne
renvoyer que titre, lien et source, sans enregistrer la recette. Réutiliser le
téléchargement borné et l’import après validation. Exclure les liens vus et les
recettes déjà importées ; cache temporaire en mémoire et gestion des pannes.
Valider autorisation, absence d’effets métier, exclusion des liens non conformes,
cache et passage au formulaire d’import avec des fixtures synthétiques.

## Liens personnalisés pour les idées

Permettre d’ajouter une URL vérifiée et de choisir la source, sans parcours du site
entier ni ajout automatique de recettes. Migration additive pour les liens privés,
limite de 20 sources et cache en mémoire borné ; réutiliser fetch sécurisé et import.
Valider sécurité réseau, permissions, absence d’effets métier, migration, sauvegarde
et gestion des liens avec des données fictives.

## Annulation d’une préparation

Proposer une action confirmée depuis le repas préparé. Réutiliser les opérations
idempotentes et les mouvements pour restituer exactement les lots consommés ; ne
pas déduire la consommation de la recette actuelle ou des manques. Retirer le
repas de l’historique actif, conserver le journal et recalculer les courses.
Identifier la préparation ciblée pour refuser une annulation ancienne après une
nouvelle préparation. Tests de cycle complet, quantités corrigées, manque de stock,
rejeu, concurrence, autorisation et rendu du formulaire.

## Variantes et fusion des ingrédients

Proposer des variantes singulier/pluriel à confirmer sans confondre les aliments
qualifiés. Conserver les noms confirmés comme alias. Permettre le renommage sans
suppression et une fusion avec aperçu vérifié, transaction et identifiant de rejeu.
Conserver les lots, mouvements et identifiants historiques ; masquer les anciennes
entrées fusionnées et refuser les demandes anciennes jusqu’à actualisation.
Valider migration, sauvegarde, recettes avec quantités communes, stock, courses,
annulation de préparation après fusion et conflits hors connexion.
