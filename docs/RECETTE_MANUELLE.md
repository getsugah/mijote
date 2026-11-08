# Vérification manuelle — Phase A

Cette recette complète les tests métier et HTTP. Aucun navigateur ni clic n’est
automatisé. Utiliser une maison de test si les données réelles ne doivent pas changer.

## Ordinateur : Chrome sous Debian/GNOME

1. Ouvrir l’application, créer le compte et vérifier la lisibilité des messages.
2. Dans l’organisation, définir quatre portions et les midis travaillés habituels.
3. Passer à une nouvelle semaine pour constater l’application du modèle. Revenir
   sur un midi travaillé et le passer maison : le modèle doit rester inchangé.
4. Créer « Riz » au poids puis une recette de quatre portions utilisant 200 g.
   Ajouter 50 g aux réserves et planifier la recette : les courses indiquent 150 g.
5. Passer temporairement ce repas hors maison puis revenir maison : le plat est
   conservé et les besoins disparaissent puis reviennent, sans mouvement de stock.
6. Cocher l’article : le stock reste 50 g. Terminer les courses avec 150 g réellement
   achetés : le stock atteint 200 g. Tester ensuite un article non trouvé et un remplacement.
7. Confirmer le repas préparé et essayer de confirmer de nouveau : une seule consommation.
   Tester une correction de quantité et une pénurie non bloquante.
8. Vérifier les formulaires au clavier, le focus des dialogues, les erreurs, la
   suppression refusée d’une recette utilisée et la déconnexion.

## Android : Chrome

1. Accéder au serveur sur le réseau privé ou son URL HTTPS ; vérifier le planning
   vertical midi/soir, la navigation inférieure et les zones tactiles.
2. Ajouter une recette/ingrédient et du stock, cocher un article, ouvrir la
   confirmation et vérifier l’absence de débordement horizontal.
3. Tester l’installation PWA avec HTTPS (ou localhost adapté). HTTP sur IP locale
   n’est pas annoncé comme installable.
4. Couper le réseau : le message hors connexion doit être visible et les actions
   désactivées. Aucune fausse confirmation ni promesse de synchronisation hors ligne.
5. Rétablir le réseau et actualiser. Les données doivent provenir du serveur.

Consigner la version de Chrome, la taille d’écran et les écarts constatés. Photos,
et fonctions avancées restent hors de cette recette initiale ; les ajouts sont détaillés ci-dessous.

## Calendrier et impression (0.1.1)

- Afficher la semaine du 9 novembre 2026 : le 11 novembre porte un en-tête coloré
  et le libellé Armistice 1918. Vérifier que les statuts maison/travail restent ceux choisis.
- Tester une semaine de Pâques et une semaine chevauchant le nouvel an.
- Cliquer **Imprimer la semaine** et vérifier l’aperçu A4 paysage : 7 jours,
  midi et soir, plats, accompagnements et portions, sans navigation ni formulaires.
- Un créneau au travail affiche son statut même si une recette y est conservée.
- Vérifier aussi les titres longs, une semaine vide et l’enregistrement au format PDF.
- Le rendu matériel de l’impression et les préférences du navigateur restent manuels.

## Import URL et collage (0.2.0)

1. Dans Mes recettes, choisir Importer une recette et un lien public. Vérifier
   que la prévisualisation ne crée encore ni recette ni ingrédient.
2. Vérifier portions, durée et étapes. Associer un ingrédient existant ; vérifier
   qu’une ligne sans quantité reste décochée et conservée en texte original.
3. Corriger une quantité ou une unité, confirmer la vérification puis enregistrer.
   La recette apparaît dans le carnet avec sa source et son auteur ; aucun stock ne change.
4. Ouvrir la recette et vérifier les lignes quantifiées et les notes d’origine.
5. Essayer le collage avec un titre, Pour 4 personnes, Ingrédients et Préparation.
6. Une URL locale doit être refusée. Un site inaccessible doit proposer le collage,
   sans tentative de connexion à un compte externe ou d’acceptation des cookies.
7. Vérifier les mêmes formulaires et le défilement du dialogue sur Android.

## Phase B — confort et courses à emporter (0.3.0)

1. Marquer une recette favorite, la retrouver avec le filtre puis enregistrer un avis,
   une catégorie, un commentaire et une variante. Vérifier ces champs après actualisation.
2. Confirmer un repas préparé puis consulter Historique. Replanifier dans un créneau
   maison vide ; vérifier que le nouveau repas n’est pas déjà préparé et qu’aucun
   stock n’est consommé à sa planification.
3. Dans Ma semaine, ouvrir Des idées, comparer les quatre modes et leurs raisons,
   puis Une autre idée. Une recette « Ne plus proposer » ne doit plus être suggérée.
4. Ouvrir Copier un menu, choisir une semaine existante et examiner l’aperçu. Vérifier
   que travail, extérieur, repas existants et préparations sont conservés.
5. Sur Android, enregistrer la liste à emporter, garder l’onglet ouvert sur HTTP local,
   couper le réseau, cocher et ajouter un article personnel, modifier sa quantité.
   Rétablir le réseau et vérifier la synchronisation. Aucun stock ne change à ce stade.
6. Depuis un autre appareil, modifier un article de la même liste. Renvoyer la demande
   locale ancienne : vérifier le conflit et les deux choix, sans écrasement silencieux.
7. Avec HTTPS et le service worker activé, tester la réouverture complète hors connexion.
   Ne pas attendre cette réouverture sur une adresse HTTP du réseau local.
8. Synchroniser, revenir aux courses et confirmer les achats séparément. Effacer
   la copie locale ou se déconnecter ; vérifier la confirmation si des demandes attendent.

Ces vérifications sont manuelles : aucun navigateur ni clic n’est automatisé.

## Partage Android/PWA (0.4.0)

1. Depuis une adresse HTTPS, installer Mijote dans Chrome sur Android. Si une ancienne
   installation ne reflète pas encore le manifeste, attendre sa mise à jour ; une
   réinstallation éventuelle nécessite d’envoyer d’abord les courses locales en attente.
2. Ouvrir une recette dans Chrome, choisir Partager puis Mijote. Le lien doit préremplir
   l’import, sans lancer automatiquement l’analyse ni enregistrer la recette.
3. Choisir Prévisualiser, vérifier puis confirmer. Vérifier source, auteur et portions.
4. Se déconnecter puis refaire le partage : se connecter avant de retrouver le formulaire.
5. Partager du texte seul, puis un texte avec deux liens ; vérifier le repli manuel et
   le choix de la source. Annuler et vérifier qu’aucune recette n’a été créée.
6. Sur HTTP local, utiliser le collage existant ; l’application ne doit pas promettre
   son apparition dans le menu Android. Sans accès au serveur, la réception n’est pas disponible.
7. Vérifier que la correction mobile 0.3.1 reste satisfaisante et qu’aucun débordement
   nouveau n’apparaît dans le formulaire prérempli.

Cette recette native est laissée à l’utilisateur ; aucun partage système ni clic
n’est automatisé. Les tests automatisés couvrent la réception HTTP et le formulaire.

## Photos de recettes (0.5.0)

1. Ouvrir Photo depuis une carte, choisir une photo du téléphone, vérifier l’aperçu
   puis conserver. Tester portrait et paysage ; la carte doit montrer l’image sans débordement.
2. Réouvrir, remplacer puis retirer la photo. Annuler un choix ne doit pas modifier la photo enregistrée.
3. Pour une recette avec URL, essayer Proposer la photo du site source. Corriger
   l’attribution si nécessaire et conserver seulement après avoir examiné l’aperçu.
4. Importer une URL : vérifier la photo proposée, puis essayer en décochant sa
   conservation. Une photo absente ou refusée ne doit pas bloquer les ingrédients et le texte.
5. Essayer un HEIC ou une animation : le refus doit être clair, l’ancienne photo conservée.
6. Vérifier la sélection et le défilement sur Android, les titres de recette longs,
   la navigation inférieure et l’absence de déplacement horizontal de la page.
7. Sauvegarde/restauration des images et retrait des métadonnées sont couverts par
   les tests ; ne pas utiliser les données du foyer comme jeux de test.
