📄 Spécification générale – Projet rosa (Open Network Aid)

🎯 Objectif

rosa est une application web open-source destinée aux associations d’aide sociale (associations de quartier, ONG locales, structures caritatives).
Elle permet :
	•	la gestion des bénéficiaires (suivi des personnes aidées),
	•	la gestion des interventions et aides (alimentaires, financières, sociales, administratives),
	•	le suivi statistique et administratif (rapports, synthèses, indicateurs),
	•	la gestion des bénévoles et utilisateurs (authentification, rôles, permissions).

L’application doit être simple à déployer, maintenable, et réutilisable par d’autres associations grâce à un code clair et bien structuré.

⸻

🛠️ Stack technologique
	•	Backend : Django 5
	•	Frontend : Django Templates + HTMX (+ AlpineJS facultatif pour interactions locales)
	•	UI : TailwindCSS (via CDN ou django-tailwind)
	•	Base de données : PostgreSQL
	•	Auth : Django auth natif (avec rôles : admin, bénévole, invité)
	•	Infra locale : uv pour gestion des dépendances Python, Postgres local ou via Docker Compose

⸻

🔑 Principes de développement
	1.	Architecture Django classique (MVT)
	•	Découpage en apps claires :
	•	users (auth, rôles, profils bénévoles)
	•	beneficiaries (suivi des bénéficiaires)
	•	aids (enregistrements des aides fournies)
	•	stats (rapports, indicateurs)
	•	Utiliser partials/ pour les fragments HTML manipulés par HTMX.
	2.	HTMX = interaction dynamique
	•	CRUD sans rechargement complet (formulaires, listes, pagination).
	•	Modales inline pour édition/ajout rapide.
	•	Pagination infinie ou “Load More”.
	3.	Design & UX
	•	Sobre, lisible, responsive (mobile-friendly via Tailwind).
	•	Navigation claire (Dashboard, Bénéficiaires, Aides, Stats, Utilisateurs).
	•	Pas de design complexe → priorité à l’ergonomie.
	4.	Code Style
	•	PEP8, commentaires clairs, modularité.
	•	CBV quand pertinent, FBV si plus simple.
	•	Tests unitaires pour models et views critiques.

⸻

📋 Fonctionnalités MVP

1. Authentification & rôles
	•	Login / Logout / Register.
	•	Rôles :
	•	Admin : tout accès + gestion utilisateurs.
	•	Bénévole : accès aux bénéficiaires et aides.
	•	Invité (optionnel) : lecture seule.

2. Gestion des bénéficiaires
	•	CRUD bénéficiaires (nom, prénom, date naissance, coordonnées, situation).
	•	Historique des interactions/aides liées à un bénéficiaire.
	•	Recherche simple par nom/email.

3. Gestion des aides
	•	CRUD des aides attribuées (type, date, quantité, notes).
	•	Liaison à un bénéficiaire.
	•	Visualisation de l’historique d’un bénéficiaire.

4. Statistiques
	•	Nombre de bénéficiaires aidés par période.
	•	Volume d’aides distribuées (par type, par période).
	•	Export CSV (rapports simples).

5. Administration
	•	Gestion des utilisateurs/bénévoles.
	•	Paramétrage de base (catégories d’aides).

⸻

🚀 Extensions futures (hors MVP)
	•	Gestion des stocks (ex: denrées alimentaires).
	•	Suivi des dons financiers.
	•	Planning des bénévoles.
	•	API publique REST pour intégrations externes.

⸻

📦 Contraintes & philosophie
	•	Simplicité d’installation : un seul repo, uv venv, migrate, runserver.
	•	Open-source réutilisable : code clair, documentation minimale (README complet).
	•	Pas de dépendances lourdes (pas de React, pas de DRF).
	•	Respect vie privée : données sensibles protégées (usage Django sessions/CSRF).

⸻

👉 Avec cette spécification, les LLM sauront :
	•	quelle stack utiliser,
	•	comment structurer le code,
	•	quelles fonctionnalités coder en priorité,
	•	et dans quel esprit (simplicité, maintenabilité, UX claire).

