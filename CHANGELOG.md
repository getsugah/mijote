# Journal de Mijote

## Repas composés, accompagnements et impression des courses

- Accompagnement choisi parmi les recettes ou directement dans le répertoire d’ingrédients avec quantité totale et unité.
- Bouton Ajouter pour plusieurs recettes, ingrédients ou intitulés libres, classés Entrée, Plat ou Dessert dans le calendrier et l’impression.
- Cumul de toutes les quantités dans les besoins ; préparation, annulation, copie, historique, suggestions et fusion d’ingrédients adaptés.
- Impression A4 de la liste de courses courante, avec quantités, cases et ajouts personnels, sans effet sur le stock.
- Migration additive 0007 et conservation des nouveaux champs lors des requêtes d’anciens clients ; aucune nouvelle dépendance.

## Noms et doublons des ingrédients

- Propositions singulier/pluriel à confirmer lors de la création et de l’import ; réutilisation des noms et alias déjà confirmés, tout en conservant les distinctions culinaires.
- Renommage sans suppression ni perte des liens ; nom précédent reconnu comme alias.
- Fusion confirmée après aperçu, avec addition des lignes communes d’une recette et conservation des lots, dates, mouvements, produits et courses manuelles.
- Rejeu protégé, refus d’un aperçu devenu ancien, contrôle des types de mesure et gestion des conflits de copies hors connexion.
- Migration additive 0006, sans fusion automatique de données existantes ni nouvelle dépendance.

## Annuler un repas préparé

- Action « Annuler Repas préparé » dans le calendrier, avec confirmation explicite.
- Restitution des seules quantités réellement déduites dans les lots d’origine, retour du repas dans les besoins et recalcul des courses.
- Historique des préparations corrigé, mouvements conservés dans le journal. Double envoi, annulations concurrentes et demandes anciennes protégés ; préparation à nouveau possible.
- Aucune migration, dépendance ou modification des restrictions Docker.

## Correction des courses hors connexion

- Écran blanc corrigé à l’ouverture d’une copie locale : la copie d’affichage accepte désormais les données réactives Vue.
- Liste sauvegardée et modifications en attente conservées ; aucun changement des règles de stock ou de synchronisation.

## Liens personnalisés pour les idées

- Ajout d’un lien vérifié dans « Des idées », choix de la source et retrait après confirmation, sans suppression des recettes importées.
- Reconnaissance de pages de recettes et de recettes précises, avec protections réseau existantes et message d’incompatibilité si aucun lien n’est reconnu.
- Migration additive 0005 : jusqu’à 20 liens privés conservés dans SQLite et inclus dans les sauvegardes ; sélection temporaire bornée en mémoire.

## Découvertes de recettes sur le web

- Bouton dans « Des idées » pour proposer une recette aléatoire depuis une source culinaire publique, avec source, lien et autre idée sans répétition dans le panneau.
- Recettes déjà importées écartées par leur URL ; aucune création automatique, aucun changement du planning, des stocks ou des courses.
- Import proposé avec l’aperçu éditable et la confirmation existants ; recherche réseau bornée, sélection temporaire en mémoire, gestion des erreurs de source.
- Aucune dépendance, migration ou modification des restrictions Docker.

## Lisibilité du calendrier

- Noms des plats et accompagnements centrés ; taille de police augmentée de 2 px sur ordinateur et téléphone. Pictogramme du plat centré au-dessus du menu.

## Installateur interactif de déploiement

- Script Bash pour Linux et ZimaOS : prérequis, port 8095 proposé, IPv4 et origines, construction et contrôle de santé.
- Configuration existante préservée, mise à jour Git en avance rapide, désinstallation confirmée sans suppression des données.
- Guide GitHub, téléchargement ZIP, sauvegardes, HTTPS et limites ZimaOS ; aucun changement métier ni modification des restrictions Docker.

## Préparation de publication — licence, 8 novembre 2026

- Code propre du projet sous PolyForm Noncommercial 1.0.0, texte officiel intégral sans modification ; mention Required Notice séparée, copyright Getsugah uniquement pour ses droits.
- README français, possibilité de licence commerciale dans COMMERCIAL.md sans tarif ni coordonnées inventés, provenance des visuels confirmée par le responsable dans ASSETS.md.
- Inventaire et notices tierces distincts, sans changement de leur licence ; copies dans les fichiers statiques pour accompagner les prochaines distributions compilées.
- Métadonnée de licence npm ajoutée ; aucun code métier, visuel, schéma, configuration ou comportement modifié. Aucune publication ni mise à jour du conteneur en service.
- Texte officiel et 76 textes tiers contrôlés ; compilation frontend réussie, JavaScript et CSS identiques au service existant, copies des notices incluses dans le build.


## 0.5.0 — Photos des recettes, 8 novembre 2026

- Bouton Photo dans le carnet : choix sur l’appareil, aperçu, conservation, remplacement et retrait sans supprimer la recette. Recherche proposée depuis la source d’une recette existante.
- Photo déclarée dans les données de recette ou les métadonnées de page proposée pendant l’import, prévisualisée localement et conservée seulement avec la confirmation. Échec photo non bloquant pour le texte ; source et attribution préservées.
- Validation JPEG/PNG/WebP fixes, limites de taille et de pixels, orientation, réduction et réencodage JPEG sans métadonnées. HEIC, SVG et animations refusés. Nouvelle dépendance Pillow 13.0.0 verrouillée.
- Migration additive 0004, photos privées dans SQLite : la sauvegarde et la restauration existantes les incluent. Aucun fichier personnel ni nom de fichier original conservé dans les sources ou la base photo.
- Réutilisation des protections SSRF pour les images, aperçus réseau hors transaction SQLite, endpoints authentifiés et CSRF, import photo atomique/idempotent. Compatibilité des anciennes confirmations d’import conservée.
- Mise à jour LAN appliquée après sauvegarde privée vérifiée : compte et volume conservés, migration 0004 et intégrité contrôlées. Instance de test arrêtée ; aucune photo de test ajoutée au foyer.
- 121 tests backend et 31 tests frontend réussis ; compilation et image Docker construites. Parcours HTTP synthétique et récupération d’une photo proposée par une page publique vérifiés en instance isolée, sans enregistrer ce contenu comme recette.

## 0.4.0 — Réception de partage Android/PWA, 8 novembre 2026

- Cible de partage POST pour liens, titres et texte, reliée au formulaire d’import existant. Préremplissage seulement : prévisualisation et confirmation explicites conservées.
- Contenu gardé en mémoire pendant la connexion, consommé une seule fois depuis un bloc JSON inerte échappé. Aucune écriture en base ni requête distante à la réception ; pas de données dans l’URL ou dans le cache de réception.
- Liens Android reconnus dans le texte ou le titre, choix laissé à l’utilisateur en cas de sources multiples, protocoles dangereux et identifiants dans l’URL refusés. Réception bornée et fichiers non acceptés.
- Aide dans le carnet et documentation : PWA installée en HTTPS nécessaire ; copier/coller sur HTTP local, réception connectée uniquement.
- 101 tests backend et 28 tests frontend réussis, compilation et image Docker construites, parcours HTTP isolé validé. Aucune dépendance ajoutée ni migration de données.
- Mise à jour LAN appliquée après sauvegarde privée vérifiée : même volume, compte et schéma 0003 conservés, intégrité et fichiers servis contrôlés. Conteneur de test arrêté.
- L’intégration native au menu de partage Android reste à tester après installation en HTTPS. Aucun code-barres, OCR ni IA commencé.

## 0.3.1 — Affichage mobile, 8 novembre 2026

- Menu inférieur contenu dans la largeur de l’écran : correction du box-sizing qui ajoutait la largeur des marges intérieures à 100 % de l’écran.
- Six entrées de navigation réparties dans la largeur disponible, libellés pouvant revenir à la ligne ; espace réservé sous le contenu avec prise en compte de la zone système du téléphone.
- Colonnes et champs autorisés à rétrécir, textes longs pouvant revenir à la ligne, hauteur adaptée à la fenêtre mobile et effet de survol désactivé au toucher.
- Aucun changement métier ni migration de données. Compilation et contrôle HTTP isolé réussis, mise à jour appliquée après sauvegarde ; compte et volume conservés. Validation visuelle laissée à l’utilisateur sur son téléphone.

## 0.3.0 — Phase B, 8 novembre 2026

- Favoris, à tester, appréciations, catégories, commentaires et variantes personnelles ; filtres du carnet et écran d’avis.
- Historique figé des préparations réelles, curseur stable et reprise des anciennes confirmations sans inventer d’heure. Une préparation retire « À tester ».
- Suggestions déterministes varier/stock/rapide/découverte avec raisons, exclusion des recettes refusées et bouton « Une autre idée ». Planification protégée contre l’écrasement d’un créneau modifié.
- Copie de semaine avec aperçu et contrôle de version, réutilisation depuis l’historique uniquement dans un créneau maison vide ; aucun débit ou état préparé recopié.
- Liste de courses à emporter volontaire dans IndexedDB, ajouts et modifications locales, UUID durables, reprises idempotentes et conflits explicites. Aucune confirmation d’achat hors connexion. Contrôle des changements entre onglets et de l’identité de la maison.
- Cache PWA limité au shell et aux fichiers construits ; les API restent hors cache. HTTP LAN : conserver un onglet chargé ; réouverture autonome hors connexion réservée à HTTPS/localhost.
- Migration additive 0003, documentation des conflits et recette Android manuelle. 91 tests backend et 19 tests frontend réussis ; image Docker et parcours HTTP isolé validés.
- Mise à jour LAN appliquée après sauvegarde privée vérifiée : même volume, compte inchangé, migration 0003 et intégrité contrôlées. Instance de test arrêtée, données de test conservées.
- Consignes de confidentialité ajoutées dans AGENTS.md ; anciens chemins personnels retirés des documents et contrôle ciblé des fichiers distribuables ajouté.

## 0.2.0 — Import de recettes, 8 novembre 2026

- Ajout ciblé demandé après la mise en service des bases : URL publique, priorité JSON-LD Recipe, repli HTML générique et collage de texte.
- Fenêtre de prévisualisation modifiable, portions/durée à vérifier, association aux ingrédients existants ou création à la confirmation. Mesures inconnues conservées en texte, hors calcul par défaut ; aucun mouvement de stock.
- Auteur et texte original ajoutés par migration 0002, avec conservation des anciennes recettes ; anciennes mises à jour de clients préservant les nouvelles métadonnées.
- Confirmation atomique et idempotente. Une erreur de ligne annule toute la création, sans laisser d’ingrédients orphelins.
- Téléchargement borné, DNS/IP publics contrôlés puis connexion épinglée, TLS vérifié, redirections revalidées ; adresses locales, ports non standards, contenus non HTML/JSON et pages protégées refusés.
- Aucun cookie, proxy d’environnement, sous-ressource ou photo téléchargé ; aucun contenu réel de recette copié dans les fixtures du projet.
- 80 tests backend et 7 tests frontend réussis ; build Vue/TypeScript et image Docker réussis. Essais sur plusieurs sources publiques et parcours HTTP d’import sur conteneur isolé validés.
- Mise à jour LAN appliquée après sauvegarde privée vérifiée ; même volume familial, compte conservé, migration 0002, intégrité et accès protégé de l’import contrôlés.

## 0.1.1 — Calendrier et menu imprimable

- Jours fériés nationaux français repérés par une couleur et un libellé, calculés localement pour chaque année, sans modification du planning ou des besoins. Particularités locales non incluses.
- Bouton « Imprimer la semaine » et vue dédiée A4 paysage avec 7 jours × midi/soir, accompagnements, portions, statuts et jours fériés ; impression ou PDF via le navigateur.
- Champ URL clarifié : conservation de la source sans import automatique. Aucun import Internet développé.
- 7 tests frontend réussis, dont rendu réel du composant imprimable sans navigateur ; 22 tests backend réussis ; compilation TypeScript/Vite et image Docker 0.1.1 réussies.
- Déploiement LAN effectué après sauvegarde SQLite privée et vérifiée ; même volume familial conservé, base intègre et nouveaux fichiers contrôlés via HTTP.

## 0.1.0 — Phase A, 7 novembre 2026

### Inspection et fondations

- Lecture intégrale du cahier des charges ; aucun projet existant trouvé. Création isolée dans le répertoire du projet, plan technique avant développement.
- API FastAPI/Pydantic, SQLite et migration Alembic initiale ; compte familial initial, mots de passe scrypt, sessions hachées, CSRF et vérification des origines.
- Application Vue 3/TypeScript française, palette aubergine/orange/crème, semaine et navigation adaptées au mobile ; manifeste PWA, cache limité au shell public.

### Fonctionnalités du MVP

- Modèle hebdomadaire midi/soir, portions globales et par repas, statut indépendant de chaque créneau. Les exceptions conservent les recettes et ne modifient pas le modèle. Application explicite possible sur une semaine encore vide, refusée dès qu’un repas est planifié.
- Ingrédients normalisés, intitulés simples, plats improvisés et recettes structurées ; CRUD, accompagnements et source URL conservée sans import distant.
- Stock manuel par lot/emplacement/date, corrections et journal des mouvements ; conversions g/kg et ml/l, aucune conversion masse/volume implicite.
- Réservation logique entre repas et entre semaines ; planifier ne consomme rien. Liste calculée et ajouts manuels ; cocher ne modifie pas le stock.
- Achats confirmés séparément, quantités réelles, substitutions et articles non trouvés. Préparation avec correction des quantités, pénurie non bloquante et opérations idempotentes transactionnelles.
- Image Docker multi-stage et Compose à un service, volume persistant, utilisateur non privilégié ; sauvegarde SQLite cohérente et restauration hors ligne protégée.

### Validation

- 22 tests API/métier/sauvegarde réussis ; confirmations concurrentes, reprises idempotentes et rollback d’achat partiel couverts.
- TypeScript et build Vite réussis ; audit npm final sans vulnérabilité signalée ; dépendances Python cohérentes et verrouillées.
- Image Docker construite et démarrée ; parcours HTTP d’acceptation et redémarrage avec persistance réussis sur l’image finale.
- Sauvegarde cohérente par flux et restauration arrêtée vérifiées dans Compose ; restauration refusée serveur actif, ancienne base préservée.
- Déconnexion rendue accessible sur mobile, contraste des boutons renforcé. Recette graphique Chrome/Android laissée à l’utilisateur, sans automatisation.
- Conteneurs de validation arrêtés, volumes et sauvegarde de test conservés. Aucun push ni déploiement public.

Détails et limites dans VALIDATION.md. Fonctions avancées des phases B/C non commencées.

### Démarrage sur le réseau local

- À la demande de l’utilisateur, configuration locale `.env` privée et lancement persistant sur l’adresse LAN de la VM, port 8080. Origine autorisée ajoutée pour le navigateur distant.
- Volume réel créé séparément des volumes de validation ; aucun compte de test injecté. API de santé et interface contrôlées via l’adresse LAN.
