# Guide de Contribution - Vyzio Ads

Merci de votre intérêt pour contribuer à Vyzio Ads ! 🎉

## 📋 Table des matières

- [Code de Conduite](#code-de-conduite)
- [Comment Contribuer](#comment-contribuer)
- [Workflow Git](#workflow-git)
- [Conventions de Code](#conventions-de-code)
- [Pull Requests](#pull-requests)
- [Signaler un Bug](#signaler-un-bug)
- [Proposer une Fonctionnalité](#proposer-une-fonctionnalité)

## Code de Conduite

Ce projet adhère à un [Code de Conduite](CODE_OF_CONDUCT.md). En participant, vous vous engagez à respecter ce code.

## Comment Contribuer

### 1. Fork et Clone

```bash
# Fork le repo sur GitHub, puis clone localement
git clone https://github.com/VOTRE_USERNAME/Vyzio_website.git
cd Vyzio_website/vyzio_ads

# Ajouter le repo upstream
git remote add upstream https://github.com/Kenneth-Sangli/Vyzio_website.git
```

### 2. Configuration de l'environnement

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer les hooks pre-commit
pre-commit install

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos variables

# Appliquer les migrations
python manage.py migrate
```

### 3. Créer une branche

```bash
# Mettre à jour depuis upstream
git fetch upstream
git checkout develop
git merge upstream/develop

# Créer votre branche de feature
git checkout -b feature/ma-nouvelle-feature
```

## Workflow Git

### Branches

| Branche | Description |
|---------|-------------|
| `main` | Production - code stable, déployé |
| `develop` | Intégration - prochaine release |
| `feature/*` | Nouvelles fonctionnalités |
| `bugfix/*` | Corrections de bugs |
| `hotfix/*` | Corrections urgentes en prod |
| `release/*` | Préparation de release |

### Convention de Commits (Conventional Commits)

Format: `<type>(<scope>): <description>`

**Types:**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage (pas de changement de code)
- `refactor`: Refactorisation
- `perf`: Amélioration de performance
- `test`: Ajout de tests
- `chore`: Maintenance

**Exemples:**
```bash
feat(auth): ajouter vérification email
fix(listings): corriger pagination des résultats
docs(readme): mettre à jour instructions d'installation
test(payments): ajouter tests webhooks Stripe
```

### Workflow de Feature

```bash
# 1. Créer la branche
git checkout develop
git pull upstream develop
git checkout -b feature/nom-de-la-feature

# 2. Développer avec des commits atomiques
git add .
git commit -m "feat(scope): description courte"

# 3. Rebaser sur develop si nécessaire
git fetch upstream
git rebase upstream/develop

# 4. Pousser et créer la PR
git push origin feature/nom-de-la-feature
```

## Conventions de Code

### Python / Django

- **Style**: PEP 8, formaté avec Black
- **Imports**: Organisés avec isort
- **Docstrings**: Google style
- **Tests**: pytest avec couverture minimum 80%

```python
# Exemple de docstring
def calculate_seller_rating(seller_id: uuid.UUID) -> Decimal:
    """
    Calcule la note moyenne d'un vendeur.
    
    Args:
        seller_id: UUID du vendeur
        
    Returns:
        Note moyenne sur 5, ou 0 si aucun avis
        
    Raises:
        SellerNotFoundError: Si le vendeur n'existe pas
    """
    pass
```

### Linting

Le projet utilise pre-commit avec:
- **Black**: Formatage automatique
- **isort**: Tri des imports
- **Flake8**: Vérification PEP 8
- **Bandit**: Analyse de sécurité

```bash
# Vérifier manuellement
pre-commit run --all-files

# Ou individuellement
black .
isort .
flake8 .
```

### Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=apps --cov-report=html

# Tests spécifiques
pytest apps/users/tests/
pytest -k "test_login"
```

## Pull Requests

### Checklist avant PR

- [ ] Code formaté (Black, isort)
- [ ] Pas d'erreurs Flake8/Bandit
- [ ] Tests passent
- [ ] Couverture >= 80%
- [ ] Documentation mise à jour
- [ ] Commits suivent Conventional Commits
- [ ] PR liée à une Issue

### Template PR

Votre PR doit inclure:
1. **Description** du changement
2. **Type** de changement (feature, fix, etc.)
3. **Tests** ajoutés/modifiés
4. **Screenshots** si changement UI
5. **Issue** liée (#123)

### Review Process

1. Au moins 1 reviewer approuve
2. CI passe (lint + tests)
3. Pas de conflits avec `develop`
4. Squash & merge recommandé

## Signaler un Bug

Utilisez le template d'issue "Bug Report" avec:

1. **Description** claire du bug
2. **Étapes** pour reproduire
3. **Comportement attendu**
4. **Comportement actuel**
5. **Environnement** (OS, Python, navigateur)
6. **Screenshots/Logs** si applicable

## Proposer une Fonctionnalité

Utilisez le template d'issue "Feature Request" avec:

1. **Problème** que la feature résout
2. **Solution** proposée
3. **Alternatives** considérées
4. **Contexte** additionnel

## Definition of Done (DoD)

Une tâche est considérée "Done" quand:

- [ ] Code implémenté et fonctionnel
- [ ] Tests unitaires écrits et passent
- [ ] Tests d'intégration si nécessaire
- [ ] Documentation mise à jour
- [ ] Code review approuvée
- [ ] CI/CD vert
- [ ] Mergé dans `develop`

## Besoin d'aide ?

- 📧 Email: support@vyzio.com
- 💬 Discussions: [GitHub Discussions](https://github.com/Kenneth-Sangli/Vyzio_website/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/Kenneth-Sangli/Vyzio_website/issues)

---

Merci encore pour votre contribution ! 🙏
