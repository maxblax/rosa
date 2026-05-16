# Validation manuelle — minitunnel bugs/améliorations post-démo

Commits de la session (du plus récent au plus ancien) :

| Hash | Item | Type |
|---|---|---|
| `dc284a2` | test: loosen placeholder check | maintenance test |
| `ac7c4d8` | section 3.2 — bouton Éditer interactions | UX |
| `e3c6bfb` | section 3.1 — tooltips acronymes aides | UX |
| `5b52f01` | 2.5 — disponibilités sans date de fin | feature |
| `6397d80` | 2.4 — clarifier "Loyer résiduel" | feature |
| `d48aa02` | 2.3 — membres adultes foyer | feature |
| `a6c606e` | 2.2 — sélection multiple besoins | feature |
| `005fb55` | 2.1 — réordonner profil/alerte | UX |
| `003edf2` | bug 1.4 étendu — dates tolérantes partout | fix |
| `2152031` | bug 1.4 — dates JJ/MM/AAAA bénéficiaires | fix |
| `e0bce1f` | bug 1.3 — upsert mensuel snapshot | fix |
| `3014cc4` | bug 1.2 — parsing décimal tolérant | fix |
| `89da8be` | bug 1.1 — Entrée ne soumet plus | fix |

Tous les tests Playwright passent (12 scripts dans `tests_playwright/`). On lance avec `./.venv/bin/python tests_playwright/<test>.py` après s'être assuré que le serveur tourne sur 5678 (mot de passe admin reseté à `admin123!`).

---

## Checklist de validation manuelle

### Bugs 1.x (section 1 du markdown)

#### 1.1 — Entrée ne soumet plus
- [ ] Page `Nouveau bénéficiaire` : remplir un champ texte, presser **Entrée** → le formulaire ne se soumet **pas** (pas de doublon Ramirez).
- [ ] Même page : cliquer le bouton **« Créer le bénéficiaire »** → soumission OK.
- [ ] Liste bénéficiaires : barre de recherche, taper un nom et **Entrée** → la recherche se lance bien (forms GET exemptés).
- [ ] Dans un textarea (description d'interaction), **Entrée** → saut de ligne normal (pas de submit).

#### 1.2 — Parsing financier
- [ ] Snapshot financier : taper `1 200,50` dans **RSA** → accepté, enregistre **1200.50**.
- [ ] Tester aussi `1,234.56`, `1200,50`, `1200` → tous acceptés.

#### 1.3 — Graphique financier doublons mois
- [ ] Créer une 1ʳᵉ interaction avec données financières → un snapshot créé pour le mois courant.
- [ ] Créer une 2ᵉ interaction le même mois avec d'autres valeurs → **un seul** snapshot pour ce mois (la 2ᵉ a écrasé la 1ʳᵉ). Le graphique n'affiche pas 2× le même mois.

#### 1.4 — Dates JJ/MM/AAAA (bénéficiaires)
- [ ] Création bénéficiaire : taper `17/03/2008` dans **Date de naissance** → accepté.
- [ ] Édition bénéficiaire : la date de naissance s'affiche au format `JJ/MM/AAAA`, modifiable.
- [ ] Enfants dynamiques (ajouter un enfant) : champ date `JJ/MM/AAAA`.
- [ ] Snapshot/interaction : champ « Date de suivi » `JJ/MM/AAAA`.

#### 1.4 étendu — Dates partout
- [ ] `Calendrier > Nouveau rendez-vous` : appointment_date en `JJ/MM/AAAA`. Le sélecteur de bénévoles disponibles HTMX continue de fonctionner (testé : il déclenche au blur du champ).
- [ ] `Calendrier > Nouvelle disponibilité` : specific_date, valid_from, valid_until tous en `JJ/MM/AAAA`.
- [ ] `Bénévoles > Nouveau bénévole` : birth_date et join_date en `JJ/MM/AAAA`.
- [ ] `Dons > Nouveau don` : date en `JJ/MM/AAAA`.

---

### Améliorations 2.x

#### 2.1 — Ordre des champs
- [ ] Création bénéficiaire : **Profil spécifique** et **Niveau d'alerte** sont **en bas du formulaire**, juste au-dessus du bouton « Créer », sous le titre « Synthèse de l'entretien ».
- [ ] Édition bénéficiaire : même chose. Les champs ne sont plus bloquants en haut.

#### 2.2 — Sélection multiple des besoins
- [ ] Nouvelle interaction : « Besoins exprimés » apparaît en checkboxes (plus en dropdown).
- [ ] Cocher **Alimentaire** + **Vestimentaire** → soumettre → la fiche détail de l'interaction affiche **deux puces** colorées (Alimentaire, Vestimentaire).
- [ ] Édition d'une interaction existante : les besoins déjà cochés sont pré-cochés.
- [ ] La section « Précisez le besoin » apparaît dès qu'**au moins une** case est cochée.

#### 2.3 — Membres adultes du foyer
- [ ] Édition bénéficiaire : nouvelle section « Membres adultes du foyer » avec bouton **« Ajouter un adulte »**.
- [ ] Cliquer ajoute une carte (civilité, prénom, nom, lien familial, date de naissance, observations).
- [ ] Soumettre → la fiche détail bénéficiaire affiche les adultes en cartes violettes (à droite des enfants).
- [ ] Re-modifier : les adultes sont préchargés et modifiables.

#### 2.4 — Loyer (montant total)
- [ ] Snapshot financier : le champ s'appelle désormais **« Loyer (montant total) »**.
- [ ] Sous le champ, le texte d'aide précise « Saisir le montant total du loyer. Les APL sont à saisir comme un revenu… ».
- [ ] Une petite icône **ⓘ** au survol affiche le même texte.

#### 2.5 — Disponibilité sans date de fin
- [ ] Calendrier > Nouvelle disponibilité, type récurrence **Hebdomadaire** : la case **« Sans date de fin »** est cochée par défaut.
- [ ] Cocher la case → le champ « Valide jusqu'au » devient grisé (disabled) et vide.
- [ ] Taper une date dans « Valide jusqu'au » → la case se décoche automatiquement.
- [ ] Soumettre avec case cochée → en base `valid_until = NULL` (à vérifier dans le détail / un export).

---

### Section 3 — Points à confirmer

#### 3.1 — Tooltips/help_text acronymes
- [ ] Snapshot financier : chaque libellé d'aide avec acronyme a une icône **ⓘ** à droite du label.
- [ ] Sous chaque champ, le texte d'aide est affiché en gris (visible direct, pas besoin de survoler).
- [ ] Couverture minimale : **RSA** (CAF), **AAH/PI**, **APL**, **PAJE**, **AF**, **CF**, **ASF**, **APE**, **IJ CPAM/MSA**, **France Travail**, **Retraite/ASPA**, **ADA**, **Garantie Jeunes (MLJ)**, **CSS**, **Loyer (montant total)**.

#### 3.2 — Bouton Éditer sur interactions
- [ ] Fiche bénéficiaire, colonne de droite « Dernières Interactions » : chaque ligne d'interaction a une mention **« Éditer »** avec icône stylo à droite de la date.
- [ ] Cliquer dessus ouvre directement la page d'édition de l'interaction.

---

## Points hors scope ou laissés ouverts (à valider si pertinent)

1. **Handler Enter global (bug 1.1)** : couvre TOUS les forms POST de l'app, pas que beneficiaries. Tester rapidement les écrans bénévoles/calendrier/dons pour s'assurer qu'aucun n'avait un usage volontaire d'Enter = submit. Échappatoire : ajouter `data-allow-enter-submit="true"` sur le form ou l'input concerné.
2. **Parsing tolérant (bug 1.2)** : seul `FinancialSnapshotForm` en bénéficie. `InteractionForm.financial_aid_amount` reste en input numérique standard — à étendre si l'usage le demande.
3. **Pas de contrainte DB d'unicité (beneficiary, year, month)** sur `FinancialSnapshot` (bug 1.3). L'upsert est applicatif, donc fragile à la concurrence (deux requêtes simultanées). Race condition jugée improbable en pratique.
4. **HTMX appointment_date (bug 1.4 étendu)** : le déclencheur HTMX `change` sur le champ date passe maintenant au blur (au lieu de chaque sélection du picker). À vérifier que l'UX de chargement des bénévoles disponibles reste fluide.
5. **2.2 — primary_need** : la donnée est stockée en CSV dans la colonne existante (`max_length=200`). Si vous voulez à terme passer en table de jointure ou en `ArrayField` PostgreSQL pour des stats plus propres, c'est une refacto séparée.
6. **2.3 — pas d'ajout d'adulte sur la page create** : seulement sur l'édition. Le scope spec disait que c'est en revenant sur le profil qu'on ajoute les autres adultes. À confirmer si vous voulez aussi le proposer dès la création.
7. **2.5 — case cochée par défaut sur création** : conséquence de `not form.valid_until.value` en première visite. À l'édition d'un slot existant avec date de fin, la case est décochée. C'est cohérent avec « par défaut, récurrence sans fin », à valider que cette default vous va.

---

## Comment lancer les tests automatisés

```bash
# Serveur Django sur le port 5678 (terminal séparé)
./.venv/bin/python manage.py runserver 5678

# Tous les tests Playwright (depuis racine projet)
for t in tests_playwright/test_*.py; do
  echo "=== $t ==="; ./.venv/bin/python "$t"
done
```

Le superuser de test est `admin / admin123!` (mot de passe reseté pendant la session).
