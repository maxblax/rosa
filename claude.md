# CLAUDE.md - rosa Project Development Guide

## 🎯 Project Scope
**rosa (Réseau Ouvert de Solidarité et d'Assistance)** is an open-source Django + HTMX web application designed for associations that provide social aid. It focuses on simplicity, maintainability, and forkability.

### Mission Statement
rosa est une application web open-source destinée aux associations d'aide sociale (associations de quartier, ONG locales, structures caritatives). Elle permet :
- la gestion des bénéficiaires (suivi des personnes aidées)
- la gestion des interventions et aides (alimentaires, financières, sociales, administratives)
- le suivi statistique et administratif (rapports, synthèses, indicateurs)
- la gestion des bénévoles et utilisateurs (authentification, rôles, permissions)

L'application doit être simple à déployer, maintenable, et réutilisable par d'autres associations grâce à un code clair et bien structuré.

### Tech Stack
- **Backend**: Django 5 + django-htmx + TailwindCSS
- **Frontend**: Django templates + HTMX (+ optirosal AlpineJS)
- **Database**: PostgreSQL
- **Tooling**: uv for virtualenv & dependency management
- **Auth**: Django auth natif (avec rôles : admin, bénévole, invité)
- **Style**: Clean code, pragmatic, minimal dependencies

---

## 🏗️ Project Structure & Architecture

### Django Apps Organization
```
rosa/                    # Main Django project
├── beneficiaries/      # Core beneficiary management
├── users/              # Authentication & user management
├── templates/          # Global templates
├── static/             # Static assets
└── manage.py
```

### Database Design Patterns
- **Beneficiary**: Core entity with persrosal info, housing, family status
- **FinancialSnapshot**: Time-based financial data (monthly snapshots)
- **Interaction**: Event logging with beneficiaries
- **Child**: Related entity for dependents

### Key Model Patterns
1. **Timestamped Models**: All models have `created_at` and `updated_at`
2. **Choices as Constants**: Use `CHOICES` tuples for dropdowns
3. **Related Names**: Always use descriptive `related_name` attributes
4. **Property Methods**: Use `@property` for computed fields
5. **French Localization**: All verbose names and help text in French

---

## 💻 Development Rules

### Code Style
- Follow PEP8 for Python
- Prefer class-based views when clear, function-based when simpler
- Keep templates modular, use partials with HTMX
- Use TailwindCSS utility classes directly in templates

### Architecture
- Single Django project repo
- Use apps for clear separation (users, beneficiaries, aids, stats, etc.)
- Stick to Django forms + crispy-forms for UX

### Testing
- Unit tests for models and views
- HTMX endpoints tested as Django views

### Git Workflow
- Main branch = production
- Feature branches for dev
- Use conventirosal commits (feat:, fix:, refactor:)

### Server Running
- No need to restart the server, assume the server is running with `python manage.py runserver` on port 5678 on a separate user terminal
- Code refresh is automatic after every change

---

## 🤖 LLM Assistant Guidance
- Generate full code files when requested (FC mode)
- Generate snippets only when asked (CC mode)
- Optimize for Django+HTMX patterns, no React/DRF unless explicitly asked
- Always include HTMX integration in templates when relevant
- Prefer vibe coding workflows: minimal boilerplate, iterate fast

---

## 💻 Coding Standards & Style

### Django Patterns
```python
# ✅ Good: Class-based views for CRUD operations
class BeneficiaryCreateView(CreateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'beneficiaries/create.html'

# ✅ Good: Function-based views for specific logic
def financial_snapshot_create_view(request, pk):
    # Complex logic that doesn't fit CBV pattern
```

### Form Design Patterns
1. **All Fields Optirosal by Default**: Except essential fields (first_name, last_name)
2. **Organized Field Groups**: Use methods like `get_revenue_categories()`
3. **TailwindCSS Classes**: Apply consistent styling via form widgets
4. **Dynamic Initial Values**: Clear zero values, show as empty/null

### Model Design Rules
```python
# ✅ Good: Descriptive choices with French labels
HOUSING_STATUS_CHOICES = [
    ('CADA', 'CADA'),
    ('CAO', 'CAO'),
    ('CHRS', 'CHRS'),
    # ...
]

# ✅ Good: Computed properties for business logic
@property
def total_revenus(self):
    revenus = [self.rsa_prime_activite or 0, ...]
    return sum(revenus)
```

### URL Patterns
- Use namespaced URLs: `'beneficiaries:detail'`
- RESTful patterns: `list/`, `create/`, `<pk>/`, `<pk>/edit/`
- Nested resources: `<beneficiary_pk>/interactions/<pk>/`

---

## 🎨 Frontend & Template Patterns

### Template Organization
```
templates/
├── base.html                    # Main layout with TailwindCSS
├── beneficiaries/
│   ├── list.html               # List view
│   ├── detail.html             # Detail view
│   ├── create.html             # Create form
│   ├── edit.html               # Edit form
│   └── partials/               # HTMX fragments
│       └── search_results.html
```

### HTMX Integration Patterns
1. **Search Autocomplete**: Use `hx-get` with `HX-Request` header detection
2. **Form Fragments**: Render partials for dynamic form sections
3. **Progressive Enhancement**: Always provide non-JS fallbacks

### CSS Framework Usage
- **TailwindCSS**: Primary styling framework
- **Form Classes**: Consistent input styling across all forms
- **Responsive Design**: Mobile-first approach
- **Utility-First**: Prefer Tailwind utilities over custom CSS

### Form Styling Standards (User Preferences)
- **Bordures visibles**: Tous les champs de saisie DOIVENT avoir des bordures claires
- **Classes CSS standards**: `w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500`
- **Champs texte larges**: Les textarea pour descriptions/commentaires doivent avoir plus de lignes (4-6 lignes minimum)
- **Focus states**: Anneau bleu au focus pour l'accessibilité et l'esthétique
- **Cohérence**: Tous les formulaires (Bénéficiaire, Interaction, Snapshot) doivent suivre le même style

---

## 🔄 Business Logic Patterns

### Financial Data Management
- **Monthly Snapshots**: One financial snapshot per month max
- **Non-Destructive Updates**: Edit current month, archive previous
- **Zero Handling**: Display empty instead of 0.00 for better UX
- **Categorized Fields**: Group revenue/charges by logical categories

### Interaction Tracking
- **User Attribution**: Track which user created interactions
- **Flexible Typing**: Multiple interaction types with icons
- **Follow-up System**: Built-in task tracking with dates
- **Financial Linking**: Optirosal snapshot attachment per interaction

### Search & Filtering
```python
# Standard search pattern across the app
queryset.filter(
    Q(first_name__icontains=query) |
    Q(last_name__icontains=query) |
    Q(email__icontains=query)
)
```

---

## 📝 Form Handling Conventions

### Form Processing Patterns
1. **Transaction Atomicity**: Use `@transaction.atomic()` for multi-model saves
2. **Graceful Degradation**: Never block main actions for optirosal data
3. **User Feedback**: Always provide success/error messages
4. **Redirect After POST**: Follow PRG pattern consistently

### Formset Management
```python
# Pattern for handling child objects
ChildFormSet = formset_factory(
    ChildForm,
    extra=0,
    can_delete=True,
    min_num=0,
    max_num=10
)
```

---

## 🚀 Development Workflow

### Local Development
- **Server**: `python manage.py runserver` on port 5678
- **Auto-reload**: Code changes refresh automatically
- **Database**: PostgreSQL with local credentials
- **Environment**: French locale (`fr-fr`, `Europe/Paris`)

### Code Organization Principles
1. **Single Responsibility**: Each app handles one domain
2. **Clear Naming**: Descriptive variable and function names
3. **Documentation**: Docstrings for complex methods
4. **Modularity**: Reusable components and utilities

### Testing Strategy
- **Playwright**: E2E testing for critical user flows
- **Django Tests**: Unit tests for models and views
- **Manual Testing**: UI/UX validation during development

---

## 🔒 Security & Data Protection

### Authentication & Authorization
- **Django Auth**: Use built-in authentication system
- **Role-Based Access**: Admin, Bénévole, Invité levels (future)
- **Session Security**: Standard Django CSRF protection

### Data Privacy Patterns
- **Minimal Data**: Only collect necessary information
- **Audit Trail**: Track who modified what and when
- **Retention Policy**: 7-year data retention before deletion
- **Access Control**: Restrict data based on user roles

---

## 📊 Performance & Optimization

### Database Optimization
```python
# ✅ Always use select_related/prefetch_related
queryset.select_related().prefetch_related('financial_snapshots')

# ✅ Limit querysets appropriately
context['interactions'] = self.object.interactions.all()[:10]
```

### Template Optimization
- **Minimal Queries**: Fetch related data in views, not templates
- **Pagination**: Use `paginate_by` for large lists
- **Lazy Loading**: Consider for heavy financial data

---

## 📋 MVP Functirosalities

### 1. Authentification & rôles
- Login / Logout / Register
- Rôles :
  - **Admin** : tout accès + gestion utilisateurs
  - **Bénévole** : accès aux bénéficiaires et aides
  - **Invité** (optionnel) : lecture seule

### 2. Gestion des bénéficiaires
- CRUD bénéficiaires (nom, prénom, date naissance, coordonnées, situation)
- Historique des interactions/aides liées à un bénéficiaire
- Recherche simple par nom/email

### 3. Gestion des aides
- CRUD des aides attribuées (type, date, quantité, notes)
- Liaison à un bénéficiaire
- Visualisation de l'historique d'un bénéficiaire

### 4. Statistiques
- Nombre de bénéficiaires aidés par période
- Volume d'aides distribuées (par type, par période)
- Export CSV (rapports simples)

### 5. Administration
- Gestion des utilisateurs/bénévoles
- Paramétrage de base (catégories d'aides)

---

## 👥 User Roles & Access Control

### Three-Level Access System (From Client Meeting)
1. **Bénévoles entretiens (O1)**: Can search, create, and modify records
2. **Bénévoles gouvernance (O2)**: Limited to anonymized report access
3. **Salariés (O3)**: Full administrative rights

### Key Requirements
- **Individual logins** for tracking actions
- **Restricted access levels** to prevent unauthorized modifications
- **Audit logs** to record changes and access attempts
- **Confidentiality protection** for sensitive beneficiary data

### Alert System (Color-Coded)
- **Green**: Standard assistance
- **Orange**: Situation requiring close monitoring
- **Red**: Critical situation requiring intervention (domestic violence, homelessness)

### Data Entry Rules
- **Standardized name formatting**: Last names in uppercase, first names in lowercase
- **Age calculation**: Derived from birthdate for dynamic tracking
- **Household relationships**: Explicit linkages between family members
- **Duplicate prevention**: Technical safeguards against manual entry errors

---

## 🧩 Extension Points & Future Features

### Planned Enhancements
- **Stock Management**: Food/supply inventory tracking (gestion des stocks)
- **Financial donations**: Monetary donation tracking (suivi des dons financiers)
- **Volunteer Scheduling**: Time management system (planning des bénévoles)
- **Public API**: REST API for external integrations
- **Multi-language**: i18n beyond French

### Architecture Considerations
- **Modular Design**: Easy to add new apps/features
- **Clean Interfaces**: Well-defined model relationships
- **Extensible Forms**: Categories can be easily expanded
- **HTMX Ready**: Frontend prepared for dynamic interactions

---

## 🎯 Key Design Principles

### Core Philosophy (Contraintes & philosophie)
- **Simplicité d'installation**: un seul repo, uv venv, migrate, runserver
- **Open-source réutilisable**: code clair, documentation minimale (README complet)
- **Pas de dépendances lourdes**: pas de React, pas de DRF
- **Respect vie privée**: données sensibles protégées (usage Django sessions/CSRF)

### Development Principles
1. **Pragmatic over Perfect**: Choose simple solutions that work
2. **User-Centric**: Prioritize volunteer/staff usability
3. **Data Integrity**: Ensure consistent, reliable information
4. **Maintainable Code**: Future developers should understand easily
5. **Open Source**: Code quality suitable for community contribution

### UX Design Guidelines
- **Sobre, lisible, responsive**: mobile-friendly via Tailwind
- **Navigation claire**: Dashboard, Bénéficiaires, Aides, Stats, Utilisateurs
- **Pas de design complexe**: priorité à l'ergonomie
- **User comfort**: Importance pour l'utilisateur final de se sentir à l'aise avec le logiciel

---

## 🛠️ Common Development Tasks

### Adding a New Field to Beneficiary
1. Add field to `models.py` with appropriate choices/validators
2. Update `forms.py` with field and styling
3. Add migration: `python manage.py makemigrations`
4. Update templates to display the field
5. Test the complete flow

### Creating a New App
1. `python manage.py startapp appname`
2. Add to `INSTALLED_APPS` in settings
3. Create models following existing patterns
4. Add URL patterns with namespace
5. Create templates following directory structure

### HTMX Integration
1. Add `HX-Request` header detection in views
2. Create partial templates in `partials/` directory
3. Use appropriate HTMX attributes in templates
4. Test both JS and non-JS functirosality

---

*This file serves as the authoritative guide for rosa development patterns and should be updated as the project evolves.*