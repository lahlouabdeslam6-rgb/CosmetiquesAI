# Références cosmétiques - première étape

Demandes validées : fond blanc, identité distincte de NUTRIFIT; conserver le nom et le logo provisoires. Avancer étape par étape. Aucun produit, média, avis ou texte commercial tiers importé.

## Sources observées

- Yves Rocher Maroc : https://www.yves-rocher.ma/c/produits-beaute
- Natus Marrakech : https://natusmarrakech.com/

Yves Rocher : navigation détaillée par univers, type de soin et type de peau; cheveux, maquillage, parfums, corps; promotions, favoris, fidélité et magasins affichés dans la navigation.

Natus : navigation par gammes, notamment visage, corps, cheveux, hammam, enfant, cadeaux et voyage; recherche, ajout au panier, options produit, promotions, avis, magazine, cartes cadeaux et accès professionnel affichés.

Les observations concernent les pages publiques. Leur administration, leurs intégrations et tous leurs comportements internes ne sont pas accessibles à partir de ces références.

## Correspondance avec la base existante

| Besoin | État |
|---|---|
| Catalogue, recherche, filtres prix/marque/catégorie, tri | Présents |
| Fiches produit, médias multiples, panier, COD, suivi | Présents |
| Packs, promotions et publication validée | Présents |
| Rôles admin/support et modification produit | Présents |
| Fond blanc, accents verts discrets, accueil allégé | Première étape appliquée |
| Sous-catégories et filtres peau/cheveux/besoins | À modéliser puis relier à l’admin |
| Favoris et avis clients | À implémenter et tester |
| Fidélité, cartes cadeaux, magasins, espace professionnel | À cadrer selon le commerce réel |
| Gammes enfants et garde-fous IA cosmétiques | À définir et valider avant usage |
| Nom définitif et logo | Reportés à la demande de l’utilisateur |

## Administration prévue

Les produits doivent rester pilotés par la base de données et les droits existants. Les prochaines catégories et attributs cosmétiques devront être éditables dans l’administration et utilisés par la recherche, les fiches et les recommandations. Les catégories des références servent à préparer ce modèle; elles ne prouvent pas que ces gammes existent dans le futur catalogue.

Cette étape livre la direction visuelle claire et conserve les fonctions existantes. Elle ne prétend pas reproduire toutes les fonctionnalités des deux boutiques.

## Mise à jour : thème blanc et navigation cosmétique

La façade dispose d'un menu Produits avec les 16 catégories reprises comme structure, Nouveautés et Promotions; d'un menu Laboratoire et de ses sous-rubriques; et des liens Commandes, Professionnels, Franchise, Carte cadeau et Contact. Les produits tiers ne sont pas importés. Les catégories filtrent le catalogue réel et sont suggérées dans les formulaires produit admin et support.

Les pages d'information existent à /informations/[rubrique]. Elles sont volontairement sans contenu commercial inventé. Un administrateur peut renseigner leur titre et texte depuis /admin/site (lien « Pages du site » une fois connecté). Chaque publication manuelle est contrôlée par le rôle admin et inscrite dans l'audit. Migration 0012_site_pages, nouvelle table vide au démarrage. Le PDF de reprise reste le constat de la préparation initiale, avant cette mise à jour.

La rubrique Carte cadeau est pour l'instant une page d'information éditable : aucun système de solde ou achat de carte cadeau n'est annoncé comme fonctionnel. Magazine et Témoignages sont également des pages éditoriales simples, pas encore des modules multi-articles ou d'avis clients. Fidélité, variantes avancées, filtres peau/cheveux et autres modules des références restent à réaliser par étapes.
## Mise à jour du 12 septembre : rubriques pilotées par la base

L'administration dispose de /admin/navigation (« Rubriques ») pour ajouter, renommer à l'affichage, ordonner et retirer les catégories du menu. Les valeurs catalogue restent stables lors d'un changement de nom affiché. Les choix sont partagés entre menu, catalogue et formulaires produit admin/support. Migration 0013_site_settings; aucun enregistrement initial requis. Les publications sont réservées au rôle admin et auditées. Retirer du menu ne supprime aucun produit.

Validation : 215 tests backend réussis dans un conteneur isolé, compilation frontend réussie, API de navigation avec les 16 catégories initiales, santé healthy, catalogue à zéro. Contrôle navigateur du thème blanc, de la navigation, du filtre Visage, de la recherche et du menu mobile. Le premier compte administrateur reste à créer avec le script interactif; aucune connexion administrateur réelle n'a été simulée dans la base de développement.