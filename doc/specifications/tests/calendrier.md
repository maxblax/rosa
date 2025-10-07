# Spécifications de Tests - Application Calendrier

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Prérequis et données de test](#prérequis-et-données-de-test)
3. [Tests de permissions et accès](#tests-de-permissions-et-accès)
4. [Tests de création de disponibilités](#tests-de-création-de-disponibilités)
5. [Tests d'édition de disponibilités](#tests-dédition-de-disponibilités)
6. [Tests de création de rendez-vous](#tests-de-création-de-rendez-vous)
7. [Tests d'édition de rendez-vous](#tests-dédition-de-rendez-vous)
8. [Tests de changement de statut](#tests-de-changement-de-statut)
9. [Tests d'impersonation](#tests-dimpersonation)
10. [Tests d'interface et UX](#tests-dinterface-et-ux)

---

## Vue d'ensemble

Cette spécification couvre l'ensemble des fonctionnalités de l'application Calendrier d'rosa, incluant :
- La gestion des disponibilités (créneaux récurrents et ponctuels)
- La gestion des rendez-vous avec bénéficiaires
- Les fonctionnalités d'impersonation (admin/salarié gérant les calendriers des bénévoles)
- Les vues multiples (semaine, jour, mois, listes)
- Les changements de statut et workflows

---

## Prérequis et données de test

### Utilisateurs de test

**Administrateur**
- Username: `admin_test`
- Role: `ADMIN`
- Permissions: Toutes
- Calendrier: Actif

**Salarié**
- Username: `salarie_test`
- Role: `EMPLOYEE`
- Permissions: impersonation, modification complète
- Calendrier: Actif

**Bénévole Entretien**
- Username: `benevole1_test`
- Role: `VOLUNTEER_INTERVIEW`
- Permissions: Modification bénéficiaires, gestion propre calendrier
- Calendrier: Actif

**Bénévole Gouvernance** (lecture seule)
- Username: `benevole2_test`
- Role: `VOLUNTEER_GOVERNANCE`
- Permissions: Lecture rapports uniquement
- Calendrier: Inactif

### Bénéficiaires de test

**Bénéficiaire 1**
- Nom: `MARTIN`
- Prénom: `Jean`
- Email: `jean.martin@example.com`
- Téléphone: `01 23 45 67 89`

**Bénéficiaire 2**
- Nom: `DUPONT`
- Prénom: `Marie`
- Email: `marie.dupont@example.com`
- Téléphone: `06 12 34 56 78`

### Données temporelles

Les tests doivent utiliser des dates relatives :
- **Aujourd'hui** : Date du jour du test
- **Semaine courante** : Lundi à dimanche de la semaine en cours
- **Mois courant** : 1er au dernier jour du mois
- **Dates futures** : J+7, J+14, J+30
- **Dates passées** : J-7, J-14

---

## Tests de permissions et accès

### TEST-PERM-001 : Accès calendrier - Administrateur
**Objectif** : Vérifier que l'admin peut accéder à toutes les vues calendrier

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier affichage de la vue semaine
4. Naviguer vers `/calendrier/day/`
5. Vérifier affichage de la vue jour
6. Naviguer vers `/calendrier/month/`
7. Vérifier affichage de la vue mois
8. Naviguer vers `/calendrier/appointments/`
9. Vérifier affichage de la liste des rendez-vous
10. Naviguer vers `/calendrier/availability/`
11. Vérifier affichage de la liste des disponibilités

**Résultat attendu** : Toutes les vues sont accessibles sans erreur 403

---

### TEST-PERM-002 : Accès calendrier - Bénévole Entretien
**Objectif** : Vérifier que le bénévole entretien peut accéder à son calendrier

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier affichage de la vue semaine avec ses propres disponibilités
4. Naviguer vers `/calendrier/appointments/`
5. Vérifier affichage de ses propres rendez-vous uniquement

**Résultat attendu** : Accès autorisé, affichage limité à ses propres données

---

### TEST-PERM-003 : Refus d'accès - Bénévole Gouvernance
**Objectif** : Vérifier que le bénévole gouvernance ne peut pas accéder au calendrier

**Étapes** :
1. Se connecter en tant que `benevole2_test`
2. Tenter de naviguer vers `/calendrier/week/`
3. Vérifier redirection ou erreur 403

**Résultat attendu** : Accès refusé

---

### TEST-PERM-004 : impersonation - Administrateur
**Objectif** : Vérifier que l'admin peut voir/gérer les calendriers des autres

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier présence du dropdown d'impersonation dans l'en-tête
4. Sélectionner `benevole1_test` dans le dropdown
5. Vérifier que l'URL contient `?as_user=<id_benevole1>`
6. Vérifier que le titre indique "Calendrier de [Nom Bénévole]"
7. Vérifier que les disponibilités affichées sont celles du bénévole

**Résultat attendu** : impersonation fonctionne, affichage correct

---

### TEST-PERM-005 : impersonation - Salarié
**Objectif** : Vérifier que le salarié peut voir/gérer les calendriers des autres

**Étapes** :
1. Se connecter en tant que `salarie_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier présence du dropdown d'impersonation
4. Sélectionner `benevole1_test`
5. Vérifier comportement identique à TEST-PERM-004

**Résultat attendu** : impersonation fonctionne pour salarié

---

### TEST-PERM-006 : Absence d'impersonation - Bénévole
**Objectif** : Vérifier que le bénévole ne voit pas le dropdown d'impersonation

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier absence du dropdown d'impersonation dans l'en-tête

**Résultat attendu** : Dropdown non présent

---

## Tests de création de disponibilités

### TEST-DISPO-001 : Création disponibilité récurrente via formulaire
**Objectif** : Créer une disponibilité hebdomadaire depuis le formulaire dédié

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/availability/create/`
3. Remplir le formulaire :
   - Type : "Disponible"
   - Récurrence : "Hebdomadaire"
   - Jour : "Lundi"
   - Heure début : "09:00"
   - Heure fin : "12:00"
   - Titre : "Permanence du lundi matin"
   - Actif : Coché
4. Soumettre le formulaire
5. Vérifier redirection vers liste des disponibilités
6. Vérifier présence de la nouvelle disponibilité dans la liste
7. Naviguer vers `/calendrier/week/` (lundi visible)
8. Vérifier affichage du créneau vert de 9h à 12h sur la colonne lundi

**Résultat attendu** : Disponibilité créée et visible dans toutes les vues

---

### TEST-DISPO-002 : Création disponibilité ponctuelle via formulaire
**Objectif** : Créer une disponibilité pour une date spécifique

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/availability/create/`
3. Remplir le formulaire :
   - Type : "Disponible"
   - Récurrence : "Ponctuelle"
   - Date spécifique : J+7 (date future dans 7 jours)
   - Heure début : "14:00"
   - Heure fin : "18:00"
   - Titre : "Disponibilité exceptionnelle"
   - Actif : Coché
4. Soumettre le formulaire
5. Naviguer vers la vue semaine de J+7
6. Vérifier affichage du créneau ponctuel le bon jour
7. Vérifier badge "Spot" ou indicateur visuel distinctif

**Résultat attendu** : Disponibilité ponctuelle créée et visible uniquement à la date spécifiée

---

### TEST-DISPO-003 : Création disponibilité "Occupé"
**Objectif** : Créer un créneau d'indisponibilité

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/availability/create/`
3. Remplir le formulaire :
   - Type : "Occupé"
   - Récurrence : "Hebdomadaire"
   - Jour : "Mercredi"
   - Heure début : "10:00"
   - Heure fin : "11:00"
   - Titre : "Réunion hebdomadaire"
4. Soumettre
5. Naviguer vers vue semaine
6. Vérifier affichage créneau rouge/occupé sur mercredi 10h-11h

**Résultat attendu** : Créneau occupé créé, couleur distincte (rouge)

---

### TEST-DISPO-004 : Création via clic sur calendrier semaine - créneau horaire
**Objectif** : Créer une disponibilité en cliquant sur une heure précise dans la vue semaine

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Cliquer sur la case "Mardi 14h" (intersection colonne mardi / ligne 14h)
4. Vérifier ouverture du panel latéral "Nouvelle disponibilité"
5. Vérifier pré-remplissage :
   - Date : Mardi de la semaine en cours
   - Heure début : 14:00
   - Heure fin : 15:00 (heure +1 par défaut)
6. Modifier :
   - Heure fin : 16:00
   - Titre : "Consultation"
   - Type : Disponible
   - Récurrence : Ponctuelle
7. Cliquer "Enregistrer"
8. Vérifier fermeture du panel
9. Vérifier apparition immédiate du créneau dans la grille (sans rechargement)
10. Vérifier preview orange avant création définitive si applicable

**Résultat attendu** : Disponibilité créée avec pré-remplissage correct, mise à jour dynamique

---

### TEST-DISPO-005 : Création via clic sur calendrier semaine - plage horaire
**Objectif** : Créer une disponibilité en sélectionnant une plage de plusieurs heures

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Cliquer-glisser depuis "Jeudi 9h" jusqu'à "Jeudi 12h"
4. Vérifier ouverture du panel avec :
   - Date : Jeudi
   - Heure début : 09:00
   - Heure fin : 12:00
5. Remplir titre : "Matinée disponible"
6. Cocher "Récurrent - Hebdomadaire"
7. Enregistrer
8. Vérifier affichage sur tous les jeudis visibles

**Résultat attendu** : Création réussie sur plage horaire, récurrence appliquée

---

### TEST-DISPO-006 : Création via calendrier jour
**Objectif** : Créer une disponibilité depuis la vue jour

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/day/?date=<date_future>` (ex: J+3)
3. Cliquer sur la ligne "10h"
4. Vérifier ouverture panel avec pré-remplissage de la date du jour affiché
5. Remplir et enregistrer
6. Vérifier affichage immédiat dans la vue jour

**Résultat attendu** : Fonctionnement identique à vue semaine

---

### TEST-DISPO-007 : Validation - Heures invalides
**Objectif** : Tester la validation des heures de début/fin

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/availability/create/`
3. Remplir avec heure fin < heure début :
   - Heure début : "15:00"
   - Heure fin : "14:00"
4. Soumettre
5. Vérifier message d'erreur : "L'heure de fin doit être après l'heure de début"

**Résultat attendu** : Validation empêche la soumission, message clair

---

### TEST-DISPO-008 : Validation - Date spécifique manquante
**Objectif** : Vérifier que la date est requise pour disponibilité ponctuelle

**Étapes** :
1. Naviguer vers formulaire création
2. Sélectionner récurrence : "Ponctuelle"
3. Ne pas remplir la date spécifique
4. Soumettre
5. Vérifier erreur de validation

**Résultat attendu** : Erreur "Date spécifique requise"

---

## Tests d'édition de disponibilités

### TEST-DISPO-EDIT-001 : Édition disponibilité récurrente via liste
**Objectif** : Modifier une disponibilité hebdomadaire depuis la liste

**Prérequis** : Avoir créé une dispo récurrente "Lundi 9h-12h"

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/availability/`
3. Trouver la ligne "Lundi 9h-12h"
4. Cliquer sur bouton "Modifier"
5. Dans le formulaire, modifier :
   - Heure fin : 13:00 (au lieu de 12:00)
   - Titre : "Permanence du lundi - MODIFIÉ"
6. Enregistrer
7. Vérifier redirection vers liste
8. Vérifier mise à jour des informations dans la liste
9. Naviguer vers vue semaine
10. Vérifier que le créneau s'affiche maintenant jusqu'à 13h

**Résultat attendu** : Modification appliquée, visible partout

---

### TEST-DISPO-EDIT-002 : Édition via clic sur créneau dans calendrier semaine
**Objectif** : Modifier une disponibilité en cliquant dessus dans la grille

**Prérequis** : Avoir une dispo "Mardi 14h-16h"

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Cliquer sur le créneau vert "Mardi 14h-16h"
4. Vérifier ouverture du panel d'édition
5. Vérifier pré-remplissage de toutes les valeurs existantes
6. Modifier heure fin : 17:00
7. Cliquer "Enregistrer"
8. Vérifier fermeture panel
9. Vérifier mise à jour visuelle immédiate du créneau (14h-17h)

**Résultat attendu** : Édition in-place réussie

---

### TEST-DISPO-EDIT-003 : Édition via page détail
**Objectif** : Modifier depuis la vue détail d'une disponibilité

**Étapes** :
1. Naviguer vers `/calendrier/availability/<id>/`
2. Cliquer bouton "Modifier" en haut de page
3. Modifier champs
4. Enregistrer
5. Vérifier redirection vers page détail
6. Vérifier affichage des nouvelles valeurs

**Résultat attendu** : Modification réussie

---

### TEST-DISPO-EDIT-004 : Désactivation disponibilité
**Objectif** : Désactiver une disponibilité sans la supprimer

**Étapes** :
1. Éditer une disponibilité existante
2. Décocher "Actif"
3. Enregistrer
4. Naviguer vers vue semaine
5. Vérifier que le créneau n'apparaît plus (ou apparaît grisé selon implémentation)
6. Naviguer vers liste disponibilités
7. Vérifier badge "Inactif" sur la ligne

**Résultat attendu** : Disponibilité cachée mais conservée en base

---

### TEST-DISPO-EDIT-005 : Conversion récurrente → ponctuelle
**Objectif** : Changer le type de récurrence d'une disponibilité

**Étapes** :
1. Éditer une disponibilité hebdomadaire (ex: "Lundi 10h")
2. Changer récurrence de "Hebdomadaire" à "Ponctuelle"
3. Sélectionner une date spécifique : J+10
4. Enregistrer
5. Naviguer vers vue semaine actuelle
6. Vérifier que le créneau n'apparaît plus sur les lundis
7. Naviguer vers semaine de J+10
8. Vérifier présence du créneau uniquement à cette date

**Résultat attendu** : Conversion réussie

---

### TEST-DISPO-EDIT-006 : Édition avec impersonation
**Objectif** : Admin/salarié modifie la dispo d'un bénévole

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer sur une disponibilité du bénévole
4. Modifier heure ou titre
5. Enregistrer
6. Vérifier que la modification est bien enregistrée sur le calendrier du bénévole (pas de l'admin)
7. Se déconnecter et reconnecter en tant que `benevole1_test`
8. Vérifier que la modification est présente

**Résultat attendu** : Modification appliquée au bon utilisateur

---

### TEST-DISPO-EDIT-007 : Bouton "Créer un rendez-vous" depuis disponibilité
**Objectif** : Créer un RDV directement depuis une dispo existante

**Prérequis** : Dispo "Vendredi 14h-18h"

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers vue semaine
3. Cliquer sur créneau "Vendredi 14h-18h"
4. Dans le panel d'édition, vérifier présence du bouton "Créer un rendez-vous sur cette disponibilité"
5. Cliquer sur ce bouton
6. Vérifier redirection vers `/calendrier/appointments/create/?date=<vendredi>&start_time=14:00&end_time=18:00`
7. Vérifier pré-remplissage du formulaire RDV
8. Compléter avec bénéficiaire et enregistrer

**Résultat attendu** : RDV créé avec bonnes valeurs pré-remplies

---

## Tests de création de rendez-vous

### TEST-RDV-001 : Création RDV via formulaire dédié
**Objectif** : Créer un rendez-vous depuis le formulaire standard

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/appointments/create/`
3. Remplir le formulaire :
   - Bénéficiaire : Sélectionner "MARTIN Jean"
   - Date : J+5
   - Heure début : 10:00
   - Heure fin : 11:00
   - Titre : "Entretien initial"
   - Type : "Entretien"
   - Notes : "Premier contact"
4. Enregistrer
5. Vérifier redirection vers liste RDV ou détail
6. Naviguer vers vue semaine de J+5
7. Vérifier affichage du RDV en bleu à 10h-11h

**Résultat attendu** : RDV créé et visible

---

### TEST-RDV-002 : Création RDV avec bénévole assigné
**Objectif** : Assigner un bénévole (soi-même) au RDV

**Étapes** :
1. Créer un RDV selon TEST-RDV-001
2. Vérifier que le champ "Bénévole" est pré-rempli avec l'utilisateur connecté
3. Enregistrer
4. Consulter détail du RDV
5. Vérifier affichage "Avec : [Nom du bénévole]"

**Résultat attendu** : Bénévole assigné automatiquement

---

### TEST-RDV-003 : Création RDV depuis disponibilité (pré-remplissage)
**Objectif** : Créer un RDV en cliquant depuis une dispo

**Prérequis** : Dispo "Jeudi 15h-17h"

**Étapes** :
1. Suivre TEST-DISPO-EDIT-007 jusqu'à étape 6
2. Vérifier formulaire pré-rempli :
   - Date : Jeudi (de la semaine affichée)
   - Heure début : 15:00
   - Heure fin : 17:00
3. Ajouter bénéficiaire : "DUPONT Marie"
4. Ajouter titre : "Suivi mensuel"
5. Enregistrer
6. Vérifier création réussie

**Résultat attendu** : RDV créé avec pré-remplissage correct

---

### TEST-RDV-004 : Preview orange lors de création
**Objectif** : Vérifier affichage du preview avant enregistrement

**Étapes** :
1. Naviguer vers `/calendrier/appointments/create/`
2. Remplir uniquement :
   - Date : J+2
   - Heure début : 14:00
   - Heure fin : 15:00
3. Observer la zone "Preview du rendez-vous" dans le formulaire
4. Vérifier affichage d'un créneau orange avec les horaires
5. Compléter bénéficiaire et enregistrer
6. Vérifier que le créneau passe de orange (preview) à bleu (enregistré) dans la vue semaine

**Résultat attendu** : Preview visible, transition correcte

---

### TEST-RDV-005 : Preview lors d'édition de RDV avec nouvelles dates
**Objectif** : Vérifier preview quand on modifie date/heure d'un RDV existant

**Prérequis** : RDV existant "Lundi 10h-11h"

**Étapes** :
1. Éditer le RDV
2. Modifier date : de Lundi → Mardi
3. Modifier heure : 10h-11h → 14h-15h
4. Observer le formulaire
5. Vérifier affichage preview orange pour "Mardi 14h-15h"
6. Vérifier que l'ancien créneau "Lundi 10h-11h" reste visible (car RDV pas encore sauvegardé)
7. Enregistrer
8. Vérifier déplacement effectif du RDV

**Résultat attendu** : Preview lors modification, puis mise à jour correcte

---

### TEST-RDV-006 : Délai de preview 500ms
**Objectif** : Vérifier que le preview attend 500ms avant de s'afficher

**Étapes** :
1. Naviguer vers création RDV
2. Remplir rapidement date et heures
3. Observer qu'il y a un délai avant affichage du preview
4. Attendre 1 seconde
5. Vérifier que le preview apparaît

**Résultat attendu** : Délai de 500ms respecté (évite affichages multiples)

---

### TEST-RDV-007 : Validation - RDV sans bénéficiaire
**Objectif** : Empêcher création RDV sans bénéficiaire

**Étapes** :
1. Remplir formulaire RDV avec date, heure, titre
2. Laisser champ "Bénéficiaire" vide
3. Soumettre
4. Vérifier erreur : "Ce champ est obligatoire"

**Résultat attendu** : Validation bloque la soumission

---

### TEST-RDV-008 : Création avec impersonation
**Objectif** : Admin crée un RDV pour un bénévole

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer sur une dispo du bénévole
4. Cliquer "Créer un rendez-vous sur cette disponibilité"
5. Vérifier que l'URL contient `?as_user=<id_benevole1>`
6. Remplir et créer le RDV
7. Vérifier que le RDV est créé pour le bénévole (pas pour l'admin)
8. Se déconnecter et reconnecter en tant que `benevole1_test`
9. Vérifier présence du RDV dans son calendrier

**Résultat attendu** : RDV créé pour le bon utilisateur

---

## Tests d'édition de rendez-vous

### TEST-RDV-EDIT-001 : Édition RDV - modification date/heure
**Objectif** : Changer la date et l'heure d'un RDV existant

**Prérequis** : RDV "Mardi 10h-11h" avec statut "Confirmé"

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers détail du RDV ou liste RDV
3. Cliquer "Modifier"
4. Changer date : Mardi → Mercredi
5. Changer heure : 10h-11h → 15h-16h
6. Enregistrer
7. Vérifier message info : "Le rendez-vous a été modifié. Statut repassé à 'Programmé'"
8. Vérifier que le statut est maintenant "Programmé" (pas "Confirmé")
9. Naviguer vers vue semaine
10. Vérifier que le RDV apparaît bien Mercredi 15h-16h

**Résultat attendu** : RDV déplacé, statut reset à "Programmé"

---

### TEST-RDV-EDIT-002 : Édition RDV - modification bénéficiaire seul
**Objectif** : Changer le bénéficiaire sans modifier date/heure

**Prérequis** : RDV avec "MARTIN Jean" statut "Confirmé"

**Étapes** :
1. Éditer le RDV
2. Changer bénéficiaire : MARTIN Jean → DUPONT Marie
3. Ne pas toucher à date/heure
4. Enregistrer
5. Vérifier que le statut reste "Confirmé" (pas de reset)
6. Vérifier détail du RDV : bénéficiaire = DUPONT Marie

**Résultat attendu** : Bénéficiaire changé, statut inchangé

---

### TEST-RDV-EDIT-003 : Édition RDV - modification titre/notes
**Objectif** : Modifier titre et notes sans toucher date/heure/bénéficiaire

**Étapes** :
1. Éditer un RDV confirmé
2. Modifier titre : "Entretien" → "Suivi administratif"
3. Modifier notes : Ajouter texte
4. Enregistrer
5. Vérifier statut inchangé
6. Vérifier nouvelles valeurs enregistrées

**Résultat attendu** : Modifications enregistrées, statut stable

---

### TEST-RDV-EDIT-004 : Édition avec préservation de as_user
**Objectif** : Admin édite RDV d'un bénévole en impersonation

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/appointments/?as_user=<id_benevole1>`
3. Cliquer "Modifier" sur un RDV du bénévole
4. Vérifier que l'URL d'édition contient `?as_user=<id_benevole1>`
5. Modifier le RDV
6. Enregistrer
7. Vérifier retour vers liste avec `as_user` préservé
8. Vérifier modification appliquée au bénévole

**Résultat attendu** : Paramètre as_user préservé dans tout le flow

---

### TEST-RDV-EDIT-005 : Édition affichage bénévole assigné
**Objectif** : Vérifier affichage du bénévole dans formulaire édition

**Étapes** :
1. Créer un RDV avec `benevole1_test`
2. Éditer ce RDV
3. Vérifier présence d'un champ ou texte affichant "Bénévole : [Nom complet]"
4. Vérifier que ce champ est en lecture seule ou informatif

**Résultat attendu** : Bénévole assigné visible dans formulaire

---

### TEST-RDV-EDIT-006 : Date pré-remplie au bon format
**Objectif** : Vérifier que la date s'affiche correctement dans le champ date

**Prérequis** : RDV avec date 15/10/2025

**Étapes** :
1. Éditer ce RDV
2. Observer le champ `<input type="date">`
3. Vérifier que la valeur est au format `2025-10-15` (format ISO)
4. Vérifier que le navigateur affiche correctement la date dans le date picker

**Résultat attendu** : Date pré-remplie visible, pas de champ vide avec placeholder "jj/mm/aaaa"

---

## Tests de changement de statut

### TEST-STATUT-001 : Changement statut "Programmé" → "Confirmé"
**Objectif** : Confirmer un RDV futur

**Prérequis** : RDV futur (J+5) avec statut "Programmé"

**Étapes** :
1. Naviguer vers détail du RDV
2. Vérifier affichage badge "Programmé" avec icône calendrier
3. Vérifier présence du bouton "Confirmer le rendez-vous"
4. Cliquer sur le bouton
5. Vérifier redirection vers détail du RDV
6. Vérifier badge maintenant "Confirmé" avec icône check
7. Vérifier que le bouton "Confirmer" a disparu
8. Vérifier présence du bouton "Annuler le rendez-vous"

**Résultat attendu** : Statut changé à "Confirmé"

---

### TEST-STATUT-002 : Changement statut "Confirmé" → "Terminé" (RDV passé)
**Objectif** : Marquer un RDV passé comme terminé

**Prérequis** : RDV passé (J-2) avec statut "Confirmé"

**Étapes** :
1. Naviguer vers détail du RDV
2. Vérifier présence du bouton "Marquer comme terminé"
3. Vérifier absence du bouton "Confirmer" (car RDV déjà confirmé)
4. Cliquer "Marquer comme terminé"
5. Vérifier statut devient "Terminé"
6. Vérifier badge vert "Terminé" avec icône check-circle

**Résultat attendu** : RDV marqué terminé

---

### TEST-STATUT-003 : Changement statut "Confirmé" → "Absent" (RDV passé)
**Objectif** : Marquer un RDV comme absence du bénéficiaire

**Prérequis** : RDV passé avec statut "Confirmé"

**Étapes** :
1. Détail du RDV
2. Cliquer bouton "Marquer comme absent"
3. Vérifier statut devient "Absent"
4. Vérifier badge rouge "Absent" avec icône user-times

**Résultat attendu** : Statut "Absent" appliqué

---

### TEST-STATUT-004 : Changement statut "Programmé" → "Annulé"
**Objectif** : Annuler un RDV programmé

**Étapes** :
1. RDV futur statut "Programmé"
2. Cliquer "Annuler le rendez-vous"
3. Vérifier statut "Annulé"
4. Vérifier badge gris avec icône times-circle

**Résultat attendu** : RDV annulé

---

### TEST-STATUT-005 : Boutons conditionnels - RDV futur confirmé
**Objectif** : Vérifier les boutons disponibles pour un RDV futur confirmé

**Prérequis** : RDV futur (J+3) statut "Confirmé"

**Étapes** :
1. Détail du RDV
2. Vérifier présence de :
   - Bouton "Annuler le rendez-vous"
   - Bouton "Modifier"
3. Vérifier absence de :
   - Bouton "Confirmer" (déjà confirmé)
   - Bouton "Marquer comme terminé" (pas encore passé)
   - Bouton "Marquer comme absent" (pas encore passé)

**Résultat attendu** : Boutons contextuels corrects

---

### TEST-STATUT-006 : Boutons conditionnels - RDV passé confirmé
**Objectif** : Vérifier les boutons pour un RDV passé confirmé

**Prérequis** : RDV passé (J-5) statut "Confirmé"

**Étapes** :
1. Détail du RDV
2. Vérifier présence de :
   - Bouton "Marquer comme terminé"
   - Bouton "Marquer comme absent"
3. Vérifier absence de :
   - Bouton "Confirmer" (déjà confirmé)
   - Bouton "Annuler" (RDV passé, pas d'annulation)

**Résultat attendu** : Seules actions post-RDV disponibles

---

### TEST-STATUT-007 : RDV annulé - aucun bouton de statut
**Objectif** : Vérifier qu'un RDV annulé ne peut plus changer de statut

**Prérequis** : RDV statut "Annulé"

**Étapes** :
1. Détail du RDV
2. Vérifier absence de tous les boutons de changement de statut
3. Vérifier présence uniquement du bouton "Modifier" (pour édition)

**Résultat attendu** : Pas de changement de statut possible

---

### TEST-STATUT-008 : Affichage date avec jour de la semaine
**Objectif** : Vérifier formatage des dates dans détail RDV

**Étapes** :
1. Consulter détail d'un RDV avec date 15/10/2025 (mercredi)
2. Vérifier affichage :
   - Ligne 1 : "mercredi" (jour en toutes lettres)
   - Ligne 2 : "15 octobre 2025" (date complète)
   - Ligne 3 : "10:00" (heure)

**Résultat attendu** : Format date lisible et complet

---

## Tests d'impersonation

### TEST-IMPERS-001 : Création dispo en impersonation - vue semaine
**Objectif** : Admin crée une dispo pour un bénévole via clic calendrier

**Étapes** :
1. Se connecter en tant que `admin_test`
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer sur une case horaire (ex: Mardi 10h)
4. Vérifier ouverture du panel
5. Vérifier que l'URL du panel contient `as_user=<id_benevole1>`
6. Remplir et enregistrer
7. Vérifier que la dispo est créée pour `benevole1_test`
8. Se déconnecter, reconnecter en tant que `benevole1_test`
9. Vérifier présence de la dispo dans son calendrier

**Résultat attendu** : Dispo créée pour le bon utilisateur

---

### TEST-IMPERS-002 : Création dispo en impersonation - plage horaire
**Objectif** : Admin crée dispo via clic-glisser pour un bénévole

**Étapes** :
1. Admin connecté, impersrosant `benevole1_test`
2. Vue semaine avec `as_user`
3. Cliquer-glisser de Jeudi 14h à 17h
4. Vérifier panel avec `as_user` dans URL
5. Enregistrer
6. Vérifier création pour le bénévole

**Résultat attendu** : Dispo créée pour le bénévole, pas l'admin

---

### TEST-IMPERS-003 : Édition dispo en impersonation
**Objectif** : Admin modifie dispo existante d'un bénévole

**Prérequis** : `benevole1_test` a une dispo "Lundi 9h-12h"

**Étapes** :
1. Admin connecté
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer sur dispo "Lundi 9h-12h"
4. Modifier heure fin : 13h
5. Enregistrer
6. Vérifier modification appliquée au bénévole
7. Se connecter en tant que `benevole1_test`
8. Vérifier dispo maintenant 9h-13h

**Résultat attendu** : Modification correcte

---

### TEST-IMPERS-004 : Suppression dispo en impersonation
**Objectif** : Admin supprime dispo d'un bénévole

**Étapes** :
1. Admin impersrosant bénévole
2. Vue semaine avec `as_user`
3. Cliquer sur une dispo
4. Cliquer "Supprimer"
5. Confirmer
6. Vérifier suppression effective
7. Vérifier côté bénévole que la dispo a disparu

**Résultat attendu** : Suppression appliquée au bénévole

---

### TEST-IMPERS-005 : Création RDV depuis dispo en impersonation
**Objectif** : Admin crée un RDV pour un bénévole depuis sa dispo

**Étapes** :
1. Admin impersrosant `benevole1_test`
2. Vue semaine avec `as_user`
3. Cliquer sur une dispo du bénévole
4. Cliquer "Créer un rendez-vous sur cette disponibilité"
5. Vérifier URL contient `as_user`
6. Vérifier formulaire pré-rempli avec date/heure de la dispo
7. Ajouter bénéficiaire, enregistrer
8. Vérifier RDV créé pour le bénévole
9. Vérifier côté bénévole la présence du RDV

**Résultat attendu** : RDV créé pour le bénévole

---

### TEST-IMPERS-006 : Navigation préserve as_user
**Objectif** : Vérifier que le paramètre as_user est préservé dans tous les liens

**Étapes** :
1. Admin connecté
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer sur "Mes rendez-vous" dans l'en-tête
4. Vérifier URL : `/calendrier/appointments/?as_user=<id_benevole1>`
5. Cliquer sur "Mes disponibilités"
6. Vérifier URL : `/calendrier/availability/?as_user=<id_benevole1>`
7. Cliquer sur "Vue jour"
8. Vérifier URL contient `as_user`

**Résultat attendu** : Paramètre préservé dans toute la navigation

---

### TEST-IMPERS-007 : Dropdown impersonation - changement d'utilisateur
**Objectif** : Changer d'utilisateur via le dropdown

**Étapes** :
1. Admin connecté sur `/calendrier/week/?as_user=<id_benevole1>`
2. Observer dropdown en haut à droite
3. Vérifier que "Bénévole 1" est sélectionné
4. Cliquer sur dropdown
5. Sélectionner "Salarié Test"
6. Vérifier rechargement de la page avec `?as_user=<id_salarie>`
7. Vérifier affichage du calendrier du salarié
8. Vérifier titre : "Calendrier de Salarié Test"

**Résultat attendu** : Changement d'utilisateur réussi

---

### TEST-IMPERS-008 : Retour au calendrier propre
**Objectif** : Admin revient à son propre calendrier depuis impersonation

**Étapes** :
1. Admin en impersonation
2. Cliquer dropdown
3. Sélectionner "Mon calendrier" (ou premier choix = soi-même)
4. Vérifier URL sans `as_user`
5. Vérifier affichage de son propre calendrier
6. Vérifier titre : "Mon calendrier"

**Résultat attendu** : Retour au calendrier propre

---

### TEST-IMPERS-009 : Filtrage preview planning en impersonation
**Objectif** : Vérifier que le preview du planning affiche uniquement les dispos du bénévole impersonné

**Étapes** :
1. Admin connecté
2. Naviguer vers `/calendrier/week/?as_user=<id_benevole1>`
3. Cliquer pour créer un RDV depuis une dispo
4. Observer la zone "Preview du planning" dans le formulaire
5. Vérifier que seules les dispos de `benevole1_test` apparaissent
6. Vérifier absence des dispos de l'admin ou d'autres bénévoles

**Résultat attendu** : Preview filtré par utilisateur impersonné

---

## Tests d'interface et UX

### TEST-UI-001 : Vue semaine - affichage grille complète
**Objectif** : Vérifier l'affichage de la vue semaine

**Étapes** :
1. Se connecter en tant que `benevole1_test`
2. Naviguer vers `/calendrier/week/`
3. Vérifier affichage :
   - En-tête avec dates (Lun 13/10, Mar 14/10, etc.)
   - Colonne heures (8h, 9h, ..., 20h)
   - Grille cliquable
   - Boutons navigation : Semaine précédente / Aujourd'hui / Semaine suivante
4. Vérifier affichage des créneaux de disponibilité (vert)
5. Vérifier affichage des RDV (bleu)
6. Vérifier affichage des créneaux occupés (rouge)

**Résultat attendu** : Vue semaine claire et complète

---

### TEST-UI-002 : Vue jour - affichage timeline
**Objectif** : Vérifier l'affichage de la vue jour

**Étapes** :
1. Naviguer vers `/calendrier/day/`
2. Vérifier affichage :
   - Date du jour en en-tête
   - Timeline verticale (heures de 8h à 20h)
   - Boutons navigation : Jour précédent / Aujourd'hui / Jour suivant
3. Vérifier affichage des créneaux sur une seule colonne
4. Cliquer sur un créneau, vérifier ouverture panel

**Résultat attendu** : Vue jour fonctionnelle

---

### TEST-UI-003 : Vue mois - affichage calendrier mensuel
**Objectif** : Vérifier la vue mois

**Étapes** :
1. Naviguer vers `/calendrier/month/`
2. Vérifier affichage :
   - Grille calendrier avec jours du mois
   - Petits indicateurs de RDV sur chaque jour (points ou badges)
3. Cliquer sur un jour
4. Vérifier affichage détaillé des RDV de ce jour (sidebar ou modal)

**Résultat attendu** : Vue mois lisible

---

### TEST-UI-004 : Liste RDV - affichage dates complètes
**Objectif** : Vérifier formatage des dates dans liste

**Étapes** :
1. Naviguer vers `/calendrier/appointments/`
2. Observer les lignes du tableau
3. Pour chaque RDV, vérifier affichage :
   - Ligne 1 : Jour de la semaine en toutes lettres (ex: "vendredi")
   - Ligne 2 : Date complète (ex: "01 octobre 2025")
   - Ligne 3 : Heure (ex: "10:00")
4. Vérifier badges de statut avec icône ET texte

**Résultat attendu** : Dates lisibles, badges clairs

---

### TEST-UI-005 : Liste RDV - boutons d'action
**Objectif** : Vérifier style des boutons

**Étapes** :
1. Liste des RDV
2. Observer colonne "Actions"
3. Vérifier boutons :
   - "Voir" : bleu, bordure, icône œil
   - "Modifier" : vert, bordure, icône edit
   - "Annuler" ou autres : rouge, bordure
4. Vérifier taille : `px-3 py-1.5 text-xs`
5. Vérifier hover : changement de fond

**Résultat attendu** : Boutons uniformes et accessibles

---

### TEST-UI-006 : Liste disponibilités - affichage badges
**Objectif** : Vérifier badges et indicateurs dans liste dispos

**Étapes** :
1. Naviguer vers `/calendrier/availability/`
2. Observer les lignes
3. Vérifier badges :
   - Type : "Disponible" (vert) / "Occupé" (rouge) avec icône
   - Récurrence : "Récurrent" avec icône redo / "Spot" (ponctuel) avec icône star
   - Statut : "Actif" (vert) / "Inactif" (gris) avec icône
4. Vérifier boutons actions uniformes

**Résultat attendu** : Badges clairs avec icônes et texte

---

### TEST-UI-007 : Détail RDV - mise en page
**Objectif** : Vérifier mise en page de la vue détail RDV

**Étapes** :
1. Naviguer vers détail d'un RDV
2. Vérifier présence de :
   - Titre du RDV en haut
   - Badge statut avec icône et texte
   - Informations : Date (format long), Heure, Bénéficiaire, Bénévole, Type
   - Section "Notes" si présentes
   - Boutons d'action en bas : Modifier / Changer statut
3. Vérifier espacements et lisibilité

**Résultat attendu** : Page détail claire et complète

---

### TEST-UI-008 : Détail disponibilité - mise en page
**Objectif** : Vérifier page détail d'une disponibilité

**Étapes** :
1. Naviguer vers détail d'une dispo
2. Vérifier affichage :
   - Type (badge coloré)
   - Récurrence (texte + icône : "Chaque lundi" ou "Date spécifique")
   - Horaires
   - Statut (actif/inactif)
   - Titre et notes si présents
3. Vérifier boutons : Modifier / Supprimer / Retour

**Résultat attendu** : Page détail complète

---

### TEST-UI-009 : Panel latéral - apparition et fermeture
**Objectif** : Tester l'ouverture/fermeture du panel d'édition

**Étapes** :
1. Vue semaine
2. Cliquer sur une case horaire vide
3. Vérifier apparition du panel depuis la droite
4. Vérifier fond assombri (overlay)
5. Cliquer sur overlay (en dehors du panel)
6. Vérifier fermeture du panel
7. Ré-ouvrir panel
8. Cliquer sur "X" ou "Annuler"
9. Vérifier fermeture

**Résultat attendu** : Panel fluide, fermeture intuitive

---

### TEST-UI-010 : Panel - pré-remplissage heure 09h
**Objectif** : Vérifier que les heures avec 0 initial (09h, 08h) se pré-remplissent correctement

**Étapes** :
1. Vue semaine
2. Cliquer sur case "Lundi 09h"
3. Observer panel
4. Vérifier champ "Heure début" contient "09:00" (pas vide)
5. Répéter avec 08h, 23h

**Résultat attendu** : Heures toujours pré-remplies, pas de bug avec 09h

---

### TEST-UI-011 : Confirmation suppression sans popup JS
**Objectif** : Vérifier absence de `confirm()` JavaScript

**Étapes** :
1. Vue semaine
2. Cliquer sur une dispo
3. Cliquer "Supprimer"
4. Vérifier qu'il n'y a PAS de popup JavaScript natif (`window.confirm`)
5. Vérifier redirection vers page de confirmation Django ou suppression directe avec message

**Résultat attendu** : Pas de popup JS old-school

---

### TEST-UI-012 : Responsive - vue mobile
**Objectif** : Tester affichage mobile (optionnel pour Selenium, mais spécifié)

**Étapes** :
1. Redimensionner navigateur à 375px de large (iPhone)
2. Naviguer vers vue semaine
3. Vérifier affichage adapté (scroll horizontal ou vue simplifiée)
4. Vérifier boutons accessibles

**Résultat attendu** : Pas de casse d'affichage

---

## Tests de régression

### TEST-REGR-001 : Création dispo récurrente puis édition ne duplique pas
**Objectif** : S'assurer qu'éditer une dispo récurrente ne crée pas de doublons

**Étapes** :
1. Créer dispo récurrente "Lundi 10h-12h"
2. Éditer cette dispo : changer heure à 10h-13h
3. Naviguer vers liste dispos
4. Vérifier qu'il n'y a qu'une seule ligne "Lundi"
5. Vérifier horaire : 10h-13h

**Résultat attendu** : Pas de duplication

---

### TEST-REGR-002 : RDV annulé ne change plus de statut
**Objectif** : Vérifier qu'un RDV annulé est "verrouillé"

**Étapes** :
1. Créer et annuler un RDV
2. Consulter détail
3. Vérifier absence de boutons de changement de statut

**Résultat attendu** : Pas de changement possible

---

### TEST-REGR-003 : impersonation préservée après création
**Objectif** : Vérifier que `as_user` reste après création d'entité

**Étapes** :
1. Admin en impersonation (`as_user=X`)
2. Créer une dispo
3. Après soumission, vérifier URL de retour contient `as_user=X`
4. Créer un RDV
5. Vérifier même comportement

**Résultat attendu** : impersonation maintenue

---

### TEST-REGR-004 : Preview ne bloque pas soumission formulaire
**Objectif** : S'assurer que le preview n'interfère pas avec la validation

**Étapes** :
1. Créer un RDV avec preview affiché
2. Remplir tous les champs requis
3. Soumettre rapidement (avant fin du délai 500ms)
4. Vérifier que la soumission se fait correctement

**Résultat attendu** : Pas de blocage

---

## Scénarios end-to-end

### SCENARIO-E2E-001 : Parcours complet bénévole
**Objectif** : Simuler un parcours utilisateur complet

**Étapes** :
1. Connexion en tant que `benevole1_test`
2. Créer 3 disponibilités récurrentes (Lundi, Mercredi, Vendredi)
3. Créer 1 disponibilité ponctuelle pour J+10
4. Naviguer vers vue semaine, vérifier affichage
5. Créer un RDV depuis une dispo du mercredi
6. Confirmer le RDV
7. Éditer le RDV pour changer l'heure
8. Vérifier reset du statut à "Programmé"
9. Naviguer vers liste RDV, vérifier affichage
10. Se déconnecter

**Résultat attendu** : Parcours complet sans erreur

---

### SCENARIO-E2E-002 : Parcours complet admin avec impersonation
**Objectif** : Admin gère le calendrier d'un bénévole

**Étapes** :
1. Connexion en tant que `admin_test`
2. Naviguer vers vue semaine avec `as_user=<benevole1>`
3. Créer 2 dispos pour le bénévole
4. Créer un RDV pour le bénévole
5. Éditer une dispo du bénévole
6. Changer d'utilisateur via dropdown (`benevole2`)
7. Créer une dispo pour `benevole2`
8. Revenir à son propre calendrier
9. Se déconnecter
10. Se connecter en tant que `benevole1_test`
11. Vérifier présence des dispos et RDV créés par l'admin

**Résultat attendu** : Admin peut gérer plusieurs calendriers

---

### SCENARIO-E2E-003 : Cycle de vie complet d'un RDV
**Objectif** : Tester tous les changements de statut

**Prérequis** : Date système ajustable ou RDV en dates passées

**Étapes** :
1. Créer un RDV futur → Statut "Programmé"
2. Confirmer le RDV → Statut "Confirmé"
3. Éditer date/heure → Statut reset à "Programmé"
4. Confirmer à nouveau
5. (Simuler passage du temps) Date du RDV est maintenant passée
6. Marquer comme "Terminé" → Statut "Terminé"

**Résultat attendu** : Workflow complet fonctionne

---

## Conclusion

Ce document couvre l'ensemble des fonctionnalités de l'application Calendrier avec plus de 80 tests spécifiés. Chaque test est rédigé de manière à pouvoir être automatisé avec Selenium/Playwright, avec :
- Des prérequis clairs
- Des étapes numérotées
- Des résultats attendus vérifiables
- Des cas de permissions, création, édition, suppression, impersonation, UI/UX

Les tests couvrent :
- ✅ Permissions et accès (6 tests)
- ✅ Création de disponibilités (8 tests)
- ✅ Édition de disponibilités (7 tests)
- ✅ Création de rendez-vous (8 tests)
- ✅ Édition de rendez-vous (6 tests)
- ✅ Changements de statut (8 tests)
- ✅ impersonation (9 tests)
- ✅ Interface et UX (12 tests)
- ✅ Régression (4 tests)
- ✅ Scénarios E2E (3 tests)

**Total : 71 tests unitaires + 3 scénarios E2E = 74 cas de test**

Ces spécifications peuvent être utilisées pour :
1. Développement de tests automatisés Selenium/Playwright
2. Tests manuels de recette
3. Documentation fonctionnelle de référence
4. Onboarding de nouveaux développeurs
