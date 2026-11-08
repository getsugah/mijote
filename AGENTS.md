# Consignes de développement — Mijote

Appliquer également les consignes du répertoire parent et le cahier des charges du projet.

## Confidentialité et portabilité

- Ne mettre aucun chemin personnel ni aucune donnée personnelle dans le code source, les commentaires, les tests, les fixtures, les exemples ou la documentation distribuée.
- Utiliser des chemins relatifs au projet, des variables d’environnement ou les répertoires standards de l’application ; ne jamais coder en dur un nom de compte, un répertoire utilisateur, une adresse de machine personnelle ou une information propre au foyer.
- Utiliser uniquement des identités et contenus fictifs dans les tests et les exemples.
- Conserver les paramètres propres à l’installation dans des fichiers locaux ignorés, notamment `.env`. Les bases, sauvegardes, journaux privés et secrets ne doivent pas être distribués.
- Ne pas recopier de données réelles du foyer pour les validations. Préserver les données existantes et vérifier les changements sur une instance isolée.
- Avant livraison, contrôler les fichiers modifiés pour détecter les chemins absolus personnels et les données privées introduites par les changements. Ne pas afficher de secrets pendant ce contrôle.

## Continuité

- Réutiliser le code fonctionnel ; terminer et tester les bases avant les fonctions avancées.
- Conserver un journal des modifications, les limites connues et les résultats de validation.
- Aucun push ni publication sans accord explicite.
