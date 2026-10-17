# Cosmetiques AI - environnement local indépendant

Préparation vérifiée le 11 septembre 2026. La marque « Cosmetiques » est provisoire.
Le code actuel a été repris sélectivement depuis Ecommerce AI, sans modifier cette source.

## Démarrer et consulter

Dans ce dossier : `docker compose up -d --build`.

- Boutique : http://localhost:5180
- API et documentation : http://localhost:8010/docs
- Santé : http://localhost:8010/health
- n8n : http://localhost:5688 (première configuration du propriétaire à effectuer)

Tous les ports sont liés à 127.0.0.1. Projet Compose : `cosmetiques-ai`.
Réseau : `cosmetiques-ai_default`. Les neuf volumes portent tous le préfixe `cosmetiques-ai_`.
Mongo 27028, Redis 6389, Qdrant 6343/6344, Ollama 11445, n8n 5688, API 8010, frontend 5180.
Pour arrêter uniquement ce projet : `docker compose stop`. Ne pas utiliser `down -v` si des données doivent être conservées.

## Partager une demonstration temporaire

La boutique et l'API passent par le meme gateway local sur `http://localhost:5180`.
Pour ouvrir un lien public temporaire, lancer explicitement le profil de partage :

```powershell
docker compose --profile share up -d demo-tunnel
docker compose logs --tail=50 demo-tunnel
```

Le journal affiche une adresse `https://...trycloudflare.com`. Elle reste active tant que
l'ordinateur, Docker et `demo-tunnel` restent demarres. Pour fermer uniquement le partage :

```powershell
docker compose stop demo-tunnel
```

Ce tunnel sert aux demonstrations. Pour la production, deployer le frontend et le backend
avec leurs bases et services IA sur une infrastructure persistante.

## Premier accès administrateur

Aucun utilisateur n'a été importé ou créé automatiquement. Exécuter depuis ce dossier :

```powershell
docker compose cp scripts/bootstrap_admin.py backend:/tmp/bootstrap_admin.py
docker compose exec -e PYTHONPATH=/app backend python /tmp/bootstrap_admin.py
```

Le mot de passe neuf est saisi de façon masquée, confirmé, puis haché. Le script refuse de créer un autre premier administrateur lorsqu'un admin existe. Aucun mot de passe n'est écrit dans le rapport.

## Fonctions reprises

Administration, support, rôles et authentification; catalogue et recherche; photos multiples et vidéos; packs et promotions; panier; checkout invité et paiement à la livraison; commandes et suivi; notifications cliquables; audit et historique. Les paiements carte hérités restent des simulations, sans prestataire réel configuré.

Agents conservés : orchestrator_service, product_agent, recommendation_agent, content_agent, seo_agent, analytics_agent, stock_forecast_agent, support_agent, delivery_agent, order_verification_agent, marketing_agent, promotion_scoring et safety_agent. Regroupements UI : Contenu & SEO, Business Intelligence, Support & Livraison. Les mécanismes existants de validation humaine sont conservés.

## Architecture

FastAPI / SQLAlchemy / Alembic, MongoDB pour les produits, SQLite pour comptes et opérations, Redis, Qdrant, Ollama et n8n. Frontend React 19 / Vinext / Vite, configuré en local sans identité Sites, Cloudflare, ni ancien fichier .openai/hosting.json. Le fichier de verrouillage npm est conservé. Les dépendances Python utilisent encore les plages de versions héritées; un verrouillage reproductible reste à prévoir.

## Données exclues et contrôle réel

Catalogue vide, 18 tables métier SQLite à zéro, table de migration technique à une ligne. Mongo : products vide et seul compteur technique products initialisé à sequence=0. Aucun média stocké, aucune collection Qdrant, Redis DBSIZE=0 au contrôle. Aucun modèle Ollama installé.

Non copiés : .git, .env source, backups, CSV/Excel, dumps, SQLite, volumes, médias, embeddings, sessions, credentials n8n, node_modules, environnements virtuels et caches. Les scripts import_products.py et enrich_products.py sont conservés comme outils à adapter et n'ont pas été exécutés. Ne pas les utiliser avec les anciennes sources.

## Vérifications

- 204 tests backend réussis dans un conteneur jetable sans réseau ni volume de développement, avec SQLite en mémoire.
- Compilation frontend Vinext réussie.
- HTTP 200 : boutique, santé API, liste produits vide, Qdrant et santé n8n.
- Boutique inspectée dans le navigateur : interface française et 0 produits.
- Sept services en cours d'exécution; les six services munis d'un healthcheck sont healthy.
- open-webui laissé en service sur son port 3000; aucun conteneur ou volume NUTRIFIT modifié.

Les tests frontend hérités ciblent l'ancien worker Cloudflare et l'identité NUTRIFIT : ils restent à adapter et ne sont pas annoncés comme réussis. Aucun parcours d'achat complet n'a été exécuté sur la base de développement vide. Le script interactif de premier admin est préparé, pas exécuté.

## Automatisations et limites IA

Les trois workflows n8n sont importés inactifs. Leurs identifiants et noms hérités mentionnent encore NUTRIFIT dans cette instance indépendante. Les seuls appels HTTP configurés ciblent le backend interne; les étapes SMTP et WhatsApp sont des noOp, sans credentials importés. Aucun envoi externe ou paiement réel n'est activé. n8n signale l'absence du runner Python; ces workflows n'en ont pas besoin, mais son usage futur demandera une configuration dédiée.

La santé Ollama confirme le service, pas la disponibilité d'un modèle. Les prompts, exemples, routages et catégories restent largement nutritionnels : product_agent.py, recommendation_agent.py, orchestrator_service.py, content_agent.py, marketing_agent.py, seo_agent.py et safety_agent.py notamment. Des textes backend, règles de promotion et champs nutritionnels restent également à revoir. Le changement d'identité visuelle provisoire ne constitue PAS une adaptation cosmétique de l'IA. Ne pas utiliser ses conseils ou publications en conditions réelles avant cette adaptation et validation humaine.

## Prochaine étape

Recevoir le nom définitif, le logo et les deux sites de référence. Valider ensuite le design, les catégories, les attributs cosmétiques, les règles de recommandation et les garde-fous, y compris pour les éventuelles gammes enfants. Aucun catalogue, bénéfice produit ou donnée client n'est inventé. Installer les modèles et valider les parcours seulement après ce cadrage.

## Mise à jour : thème blanc et navigation cosmétique

La façade dispose d'un menu Produits avec les 16 catégories reprises comme structure, Nouveautés et Promotions; d'un menu Laboratoire et de ses sous-rubriques; et des liens Commandes, Professionnels, Franchise, Carte cadeau et Contact. Les produits tiers ne sont pas importés. Les catégories filtrent le catalogue réel et sont suggérées dans les formulaires produit admin et support.

Les pages d'information existent à /informations/[rubrique]. Elles sont volontairement sans contenu commercial inventé. Un administrateur peut renseigner leur titre et texte depuis /admin/site (lien « Pages du site » une fois connecté). Chaque publication manuelle est contrôlée par le rôle admin et inscrite dans l'audit. Migration 0012_site_pages, nouvelle table vide au démarrage. Le PDF de reprise reste le constat de la préparation initiale, avant cette mise à jour.

La rubrique Carte cadeau est pour l'instant une page d'information éditable : aucun système de solde ou achat de carte cadeau n'est annoncé comme fonctionnel. Magazine et Témoignages sont également des pages éditoriales simples, pas encore des modules multi-articles ou d'avis clients. Fidélité, variantes avancées, filtres peau/cheveux et autres modules des références restent à réaliser par étapes.
## Mise à jour du 12 septembre : rubriques pilotées par la base

L'administration dispose de /admin/navigation (« Rubriques ») pour ajouter, renommer à l'affichage, ordonner et retirer les catégories du menu. Les valeurs catalogue restent stables lors d'un changement de nom affiché. Les choix sont partagés entre menu, catalogue et formulaires produit admin/support. Migration 0013_site_settings; aucun enregistrement initial requis. Les publications sont réservées au rôle admin et auditées. Retirer du menu ne supprime aucun produit.

Validation : 215 tests backend réussis dans un conteneur isolé, compilation frontend réussie, API de navigation avec les 16 catégories initiales, santé healthy, catalogue à zéro. Contrôle navigateur du thème blanc, de la navigation, du filtre Visage, de la recherche et du menu mobile. Le premier compte administrateur reste à créer avec le script interactif; aucune connexion administrateur réelle n'a été simulée dans la base de développement.


## Procédés détaillés du Laboratory Agent

Chaque génération de formule et chaque révision demandée dans la conversation déclenche automatiquement un procédé détaillé pour la proposition concernée. Les phases affichent les matières et masses calculées, l’ordre d’incorporation, les températures, les durées et attentes, l’agitation et les critères de fin. La page suit la génération en arrière-plan. Le cahier des charges et le procédé sélectionné se téléchargent en Word depuis le dossier.

Le modèle des procédés peut être configuré séparément avec `OLLAMA_LABORATORY_MODEL`; sans cette valeur, `OLLAMA_CHAT_MODEL` est utilisé. La configuration locale utilise `qwen2.5:7b`, à installer avec `docker compose exec ollama ollama pull qwen2.5:7b`. Les références fournisseur manquantes et les paramètres d’essais proposés sont explicitement signalés; les champs vides et les affectations d’ingrédients incohérentes font échouer la génération au lieu d’être exportés.

La validation administrateur enregistre un produit brouillon lié au client et au dossier. Elle exige la décision d’approvisionnement pour les matières manquantes et attend la fin du procédé. La génération et la validation administrateur ne remplacent pas la validation technique du laboratoire ni les essais.
