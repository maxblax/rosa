# Tests de validation des corrections - Rapport de bugs

## Prérequis
1. Serveur Django en cours d'exécution : `uv run python manage.py runserver 5678`
2. Migrations appliquées : `uv run python manage.py migrate`
3. Utilisateur admin créé pour se connecter

## Tests à effectuer

### ✅ Bug #1: Auto-population de la date de naissance des enfants

**Fichier modifié:** `beneficiaries/views.py:117`

**Étapes de test:**
1. Connectez-vous à l'application
2. Allez dans la liste des bénéficiaires
3. Sélectionnez un bénéficiaire qui a des enfants avec des dates de naissance
4. Cliquez sur "Modifier"
5. Vérifiez que le formulaire affiche la section "Enfants à Charge"
6. **Validation:** Les champs "Date de naissance" des enfants doivent être pré-remplis avec les bonnes dates

**Résultat attendu:** Les dates de naissance sont visibles et éditables dans les champs de type date

---

### ✅ Bug #2: Navigation entre semaines dans le calendrier global

**Fichier modifié:** `templates/calendar/global.html:19-30`

**Étapes de test:**
1. Connectez-vous avec un compte admin ou employé
2. Accédez au calendrier global (menu Calendrier > Vue Globale)
3. Cliquez sur le bouton "←" (semaine précédente)
4. **Validation:** Le calendrier affiche bien la semaine précédente
5. Cliquez sur le bouton "→" (semaine suivante)
6. **Validation:** Le calendrier affiche bien la semaine suivante
7. Cliquez sur "Cette semaine"
8. **Validation:** Le calendrier revient à la semaine actuelle

**Résultat attendu:** La navigation fonctionne correctement sans erreur

---

### ✅ Amélioration #1: Champ Nationalité

**Fichiers modifiés:**
- `beneficiaries/models.py`
- `beneficiaries/forms.py`
- `templates/beneficiaries/create.html`
- `templates/beneficiaries/edit.html`
- `templates/beneficiaries/detail.html`
- Migration: `0008_beneficiary_nationality.py`

**Étapes de test:**

#### Test 1: Création d'un nouveau bénéficiaire
1. Allez dans Bénéficiaires > Nouveau Bénéficiaire
2. **Validation:** Un champ "Nationalité" est visible avec 3 options :
   - Française
   - Union Européenne
   - Hors Union Européenne
3. Remplissez les champs obligatoires et sélectionnez une nationalité
4. Enregistrez
5. **Validation:** Le bénéficiaire est créé avec la nationalité choisie

#### Test 2: Affichage dans la vue détail
1. Ouvrez le profil du bénéficiaire créé
2. **Validation:** La nationalité s'affiche dans les informations personnelles

#### Test 3: Modification
1. Cliquez sur "Modifier"
2. **Validation:** Le champ Nationalité est présent et pré-rempli
3. Modifiez la nationalité
4. Enregistrez
5. **Validation:** La modification est prise en compte

---

### ✅ Amélioration #2: Case RGPD pour le consentement

**Fichiers modifiés:**
- `beneficiaries/models.py` (ajout de `gdpr_consent` et `gdpr_consent_date`)
- `beneficiaries/forms.py`
- `beneficiaries/views.py` (logique d'enregistrement de la date)
- `templates/beneficiaries/create.html`
- Migration: `0009_beneficiary_gdpr_consent_and_more.py`

**Étapes de test:**

#### Test 1: Affichage de la section RGPD
1. Allez dans Bénéficiaires > Nouveau Bénéficiaire
2. **Validation:** En haut du formulaire, il y a une section bleue "Protection des données personnelles"
3. **Validation:** Une checkbox "Consentement RGPD" est visible avec le texte d'aide
4. **Validation:** La checkbox a une icône de bouclier (fas fa-shield-alt)

#### Test 2: Obligation du consentement
1. Essayez de créer un bénéficiaire sans cocher la case RGPD
2. **Validation:** Le formulaire affiche une erreur indiquant que le consentement est obligatoire

#### Test 3: Enregistrement du consentement
1. Cochez la case RGPD
2. Remplissez les autres champs obligatoires
3. Enregistrez
4. Vérifiez dans la base de données ou l'admin Django que :
   - `gdpr_consent` = True
   - `gdpr_consent_date` contient la date/heure de création

---

### ✅ Amélioration #3: Champ d'adressage pour statistiques

**Fichiers modifiés:**
- `beneficiaries/models.py` (ajout de `referral_source`)
- `beneficiaries/forms.py`
- `templates/beneficiaries/create.html`
- Migration: `0010_beneficiary_referral_source.py`

**Étapes de test:**

#### Test 1: Présence du champ
1. Allez dans Bénéficiaires > Nouveau Bénéficiaire
2. Faites défiler jusqu'à la section "Interlocuteur privilégié"
3. **Validation:** Juste avant, il y a un champ "Adressé par" marqué comme (facultatif)
4. **Validation:** Le placeholder indique "Ex: Croix-Rouge, assistant social, bouche à oreille"

#### Test 2: Enregistrement facultatif
1. Créez un bénéficiaire SANS remplir le champ "Adressé par"
2. **Validation:** Le bénéficiaire est créé sans erreur
3. Créez un autre bénéficiaire EN remplissant "Adressé par" (ex: "Croix-Rouge")
4. **Validation:** L'information est bien enregistrée

#### Test 3: Utilité pour les statistiques
1. Dans l'admin Django ou via une requête, vérifiez qu'on peut filtrer/grouper par `referral_source`
2. **Validation:** Le champ peut servir pour générer des statistiques sur les sources de référencement

---

## Résumé des migrations à appliquer

```bash
uv run python manage.py migrate beneficiaries
```

**Migrations créées:**
- `0008_beneficiary_nationality.py` - Ajoute le champ nationalité
- `0009_beneficiary_gdpr_consent_and_more.py` - Ajoute les champs RGPD
- `0010_beneficiary_referral_source.py` - Ajoute le champ d'adressage

---

## Checklist finale

- [ ] Bug #1: Dates de naissance des enfants pré-remplies
- [ ] Bug #2: Navigation calendrier global fonctionnelle
- [ ] Amélioration #1: Champ Nationalité présent et fonctionnel
- [ ] Amélioration #2: Consentement RGPD obligatoire à la création
- [ ] Amélioration #3: Champ "Adressé par" facultatif présent
- [ ] Toutes les migrations appliquées sans erreur
- [ ] Aucune régression sur les fonctionnalités existantes

---

## Notes importantes

- Le champ "Reste à vivre journalier" n'a PAS été implémenté car il nécessite des modifications substantielles du modèle financier et de la logique de calcul
- Tous les nouveaux champs respectent les conventions du projet (TailwindCSS, labels français, help_text)
- Le consentement RGPD enregistre automatiquement la date/heure lors de la première validation
