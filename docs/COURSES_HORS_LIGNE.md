# Emporter les courses — version 0.3.0

Dans **Mes courses**, ouvrir **Emporter ma liste / courses hors connexion**, puis
**Enregistrer la liste de la semaine**. Ce choix conserve une copie privée sur
l’appareil : liste, répertoire d’ingrédients utile et modifications en attente.
Ni mot de passe, ni jeton de session, ni planning complet ne sont enregistrés dans
ce stockage local. Choisir un appareil de confiance et effacer la copie après
utilisation sur un appareil partagé.

## Pendant les courses

- Cocher/décocher place un article dans le panier local.
- Ajouter un article du répertoire ; modifier la quantité ou retirer un ajout personnel.
- Les quantités des besoins calculés se changent depuis les repas, avec le serveur.
- Les modifications restent dans IndexedDB après fermeture de la vue et sont liées
  à une maison et une semaine. Un changement de semaine ne remplace pas une file en attente.
- Aucun achat n’est confirmé, aucun stock n’est ajouté ou consommé hors connexion.

À l’ouverture de la vue, au retour du réseau ou avec **Synchroniser**, Mijote tente
l’envoi si la session est valide. Une session expirée demande une reconnexion ; la
file reste conservée. Après reconnexion, rouvrir la liste à emporter et synchroniser.
Une autre maison ne peut pas recevoir cette file. Il n’y a pas de synchronisation
temps réel sans réseau, ni d’envoi garanti quand le navigateur est fermé.

## En cas de conflit

Chaque article possède une version serveur, et chaque opération un UUID durable.
Un envoi dont la réponse est perdue est rejoué avec le même UUID : aucun ajout en double.
Une opération déjà tentée reste figée jusqu’à sa réponse ; elle ne peut pas être
modifiée en place. Les modifications encore jamais envoyées peuvent être regroupées.

Si un autre appareil a changé l’article, sa quantité ou le besoin calculé, la
demande locale n’écrase pas le serveur. La vue montre la demande locale et la
version actuelle. Choisir **Conserver la version du serveur**, ou, après examen,
**Réappliquer ma modification** : cela crée une nouvelle opération basée sur la
version affichée. Si l’article a disparu, seule la conservation du serveur est
proposée ; il n’est pas recréé silencieusement. Un ajout invalide peut être retiré,
puis corrigé avec un nouvel ajout. Les autres articles sans conflit peuvent être envoyés.

Les onglets partagent une transaction locale ; une vue devenue ancienne ne doit
pas écraser une copie actualisée dans un autre onglet. Le retour au premier plan
relit la copie. Pour terminer, synchroniser, revenir à Mijote et utiliser
**Terminer les courses** pour contrôler les achats réellement effectués.

**Effacer la copie locale** abandonne les demandes locales après confirmation.
Une opération déjà reçue par le serveur n’est pas annulée par cet effacement.
Se déconnecter efface aussi la copie ; une file en attente demande confirmation.

## HTTP local et HTTPS

Sur une adresse HTTP du réseau local, conserver l’onglet déjà chargé avant de
quitter le réseau. La liste reste utilisable dans cet onglet ; son rechargement
hors connexion n’est pas garanti, car Chrome n’autorise pas le service worker sur
cette origine. Avec HTTPS ou localhost, le service worker conserve les fichiers
publics de l’application pour la réouverture hors connexion après son activation.
Les réponses API privées ne sont jamais mises en cache par le service worker.

L’installation et la réouverture réelles sur Android restent à vérifier sur
l’appareil utilisé. Le stockage peut être effacé par le navigateur, le mode privé
ou l’utilisateur : ce cache n’est pas une sauvegarde de la maison.
