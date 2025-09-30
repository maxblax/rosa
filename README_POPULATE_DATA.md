# 🎲 Commande de Population des Données

Cette commande Django génère un jeu de données réaliste pour tester et démontrer le fonctionnement de l'application ONA avec des données variées.

## 🚀 Utilisation

### Commande de base
```bash
python manage.py populate_data
```

### Options disponibles
```bash
python manage.py populate_data --help
```

### Exemples d'utilisation

#### Générer un jeu de données complet (par défaut)
```bash
python manage.py populate_data
```
- **12 utilisateurs** (1 admin, 2 salariés, 8 bénévoles entretien, 1 bénévole gouvernance)
- **15 bénéficiaires** avec profils variés
- **Snapshots financiers** avec 1-6 mois d'historique par bénéficiaire
- **Rendez-vous** répartis entre passé, présent et futur
- **Interactions** variées entre bénévoles et bénéficiaires

#### Effacer et regénérer toutes les données
```bash
python manage.py populate_data --clear
```

#### Personnaliser le nombre d'entités
```bash
python manage.py populate_data --users 20 --beneficiaries 30
```

## 📊 Types de données générées

### 👥 Utilisateurs et Bénévoles
- **1 Administrateur** : Accès complet à l'application
- **2 Salariés** : Droits administratifs étendus
- **8 Bénévoles Entretien** : Peuvent créer/modifier les dossiers bénéficiaires
- **1 Bénévole Gouvernance** : Accès lecture seule aux rapports

Chaque bénévole a :
- Des informations personnelles réalistes
- Des compétences variées
- Des créneaux de disponibilité
- Un suivi d'heures mensuel (pour les actifs)

### 🏠 Bénéficiaires
- **Profils diversifiés** : Âges, situations familiales, statuts de logement variés
- **Enfants à charge** : Certains bénéficiaires ont des enfants avec âges réalistes
- **Coordonnées** : Adresses, téléphones, emails (partiellement remplis)
- **Situations sociales** : Différents statuts de logement et situations familiales

### 💰 Snapshots Financiers
- **Données partielles** : Simule la réalité où tous les champs ne sont pas toujours remplis
- **Historique variable** : Entre 1 et 6 mois d'antériorité par bénéficiaire
- **Montants réalistes** : Prestations sociales, revenus et charges avec des valeurs cohérentes
- **Diversité des sources** : RSA, AAH, salaires, allocations familiales, etc.

### 📅 Calendriers et Rendez-vous
- **Créneaux de disponibilité** : Horaires récurrents pour chaque bénévole éligible
- **Répartition inégale des RDV** : Certains bénévoles très sollicités, d'autres moins
- **Statuts variés** : Rendez-vous programmés, confirmés, terminés, annulés
- **Historique et futur** : 60% passés, 20% à venir proche, 20% futurs

### 📝 Interactions
- **Types diversifiés** : Entretiens, appels, visites, emails
- **Contenus réalistes** : Titres et descriptions d'interactions typiques
- **Suivi** : Certaines interactions nécessitent un suivi avec dates futures
- **Attribution** : Créées par des bénévoles habilités

## 🎯 Objectifs de cette commande

1. **Test de performance** : Voir comment l'application se comporte avec plus de données
2. **Démonstration** : Présenter l'application avec des données crédibles
3. **Développement** : Tester les fonctionnalités avec des cas d'usage variés
4. **Formation** : Permettre aux utilisateurs de découvrir l'application

## ⚠️ Notes importantes

- **Données fictives** : Toutes les données sont générées par Faker et ne correspondent à aucune personne réelle
- **Mots de passe** : Tous les utilisateurs ont le mot de passe `demo123`
- **Transactionnel** : La commande utilise une transaction atomique
- **Sécurisé** : L'option `--clear` supprime uniquement les données non-admin

## 🔄 Maintenance

Cette commande est conçue pour évoluer avec le modèle de données. Quand vous ajoutez de nouveaux champs ou modèles :

1. Modifiez la commande pour inclure les nouveaux champs
2. Ajustez les méthodes de génération selon vos besoins
3. Testez avec `--users 2 --beneficiaries 2` avant la génération complète

## 📦 Dépendances

- **Faker** : Génération de données fictives réalistes
- **Django** : Framework et ORM pour la persistance
- Tous les modèles ONA (Beneficiary, Volunteer, Calendar, etc.)