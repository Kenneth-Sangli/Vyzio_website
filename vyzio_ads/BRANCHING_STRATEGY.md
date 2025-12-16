# Stratégie de Branches - Vyzio Ads

## 🌳 Vue d'ensemble

Ce projet utilise une stratégie de branches **Git Flow** adaptée pour maintenir un code stable en production tout en permettant un développement continu.

```
main (production)
  │
  ├── hotfix/critical-bug ────────────────────────────────┐
  │                                                        │
develop (integration)                                      │
  │                                                        │
  ├── feature/user-auth ──────────┐                       │
  │                                │                       │
  ├── feature/listings-crud ──────┤── merge ──> develop   │
  │                                │                       │
  ├── bugfix/login-error ─────────┘                       │
  │                                                        │
  └── release/v1.0.0 ──────────────────────> main <───────┘
```

## 📌 Branches Principales

### `main` (Production)
- **Rôle**: Code en production, stable et déployé
- **Protection**: 
  - ✅ Requiert PR approuvée
  - ✅ CI doit passer
  - ✅ Pas de push direct
- **Déploiement**: Automatique vers production

### `develop` (Intégration)
- **Rôle**: Branche d'intégration pour la prochaine release
- **Protection**: 
  - ✅ Requiert PR approuvée
  - ✅ CI doit passer
- **Déploiement**: Automatique vers staging

## 🔀 Branches de Travail

### `feature/*`
- **Usage**: Nouvelles fonctionnalités
- **Créée depuis**: `develop`
- **Merge vers**: `develop`
- **Nommage**: `feature/nom-descriptif`
- **Exemples**:
  ```
  feature/user-registration
  feature/stripe-integration
  feature/search-filters
  ```

### `bugfix/*`
- **Usage**: Corrections de bugs non-critiques
- **Créée depuis**: `develop`
- **Merge vers**: `develop`
- **Nommage**: `bugfix/description-courte`
- **Exemples**:
  ```
  bugfix/login-validation
  bugfix/pagination-offset
  ```

### `hotfix/*`
- **Usage**: Corrections urgentes en production
- **Créée depuis**: `main`
- **Merge vers**: `main` ET `develop`
- **Nommage**: `hotfix/description-courte`
- **Exemples**:
  ```
  hotfix/security-patch
  hotfix/payment-crash
  ```

### `release/*`
- **Usage**: Préparation d'une nouvelle version
- **Créée depuis**: `develop`
- **Merge vers**: `main` ET `develop`
- **Nommage**: `release/vX.Y.Z`
- **Exemples**:
  ```
  release/v1.0.0
  release/v1.1.0
  ```

## 📋 Workflows

### Nouvelle Fonctionnalité

```bash
# 1. Mettre à jour develop
git checkout develop
git pull origin develop

# 2. Créer la branche feature
git checkout -b feature/ma-fonctionnalite

# 3. Développer...
git add .
git commit -m "feat(scope): description"

# 4. Rebaser si nécessaire
git fetch origin
git rebase origin/develop

# 5. Pousser et créer PR
git push origin feature/ma-fonctionnalite
# Créer PR vers develop sur GitHub
```

### Correction de Bug

```bash
# 1. Créer la branche depuis develop
git checkout develop
git pull origin develop
git checkout -b bugfix/mon-bug

# 2. Corriger et commiter
git add .
git commit -m "fix(scope): description"

# 3. Pousser et créer PR
git push origin bugfix/mon-bug
```

### Hotfix Urgent

```bash
# 1. Créer depuis main
git checkout main
git pull origin main
git checkout -b hotfix/bug-critique

# 2. Corriger
git add .
git commit -m "fix(critical): description"

# 3. Pousser et créer PR vers main
git push origin hotfix/bug-critique

# 4. Après merge dans main, merge aussi dans develop
git checkout develop
git merge main
git push origin develop
```

### Release

```bash
# 1. Créer la branche release
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# 2. Bump version, changelog, derniers ajustements
# ...

# 3. Pousser et créer PR vers main
git push origin release/v1.0.0

# 4. Après merge dans main:
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 5. Merge aussi dans develop
git checkout develop
git merge main
git push origin develop
```

## 🏷️ Versioning (SemVer)

Format: `vMAJOR.MINOR.PATCH`

- **MAJOR**: Changements incompatibles avec versions précédentes
- **MINOR**: Nouvelles fonctionnalités rétrocompatibles
- **PATCH**: Corrections de bugs rétrocompatibles

Exemples:
- `v1.0.0` → `v1.0.1` : Correction de bug
- `v1.0.0` → `v1.1.0` : Nouvelle fonctionnalité
- `v1.0.0` → `v2.0.0` : Breaking change

## 🔒 Règles de Protection

### `main`
```yaml
- Requiert pull request avant merge
- Requiert 1 approbation minimum
- Requiert que les checks CI passent
- Requiert que les branches soient à jour
- Pas de push direct autorisé
- Pas de force push
```

### `develop`
```yaml
- Requiert pull request avant merge
- Requiert 1 approbation minimum
- Requiert que les checks CI passent
```

## 📊 Diagramme de Flux

```
                    main ─────────────────────────────────────────────────►
                      │                    ▲              ▲
                      │                    │              │
                      │               [release]      [hotfix]
                      │                    │              │
                      ▼                    │              │
    develop ◄─────────┼────────────────────┼──────────────┼────────────────►
         ▲            │                    ▲              ▲
         │            │                    │              │
    [feature]    [feature]            [feature]     [feature]
         │            │                    │              │
         └────────────┴────────────────────┴──────────────┘
```

## ✅ Checklist PR

Avant de créer une PR:

- [ ] Branch à jour avec la branche cible
- [ ] Commits suivent Conventional Commits
- [ ] Tests passent localement
- [ ] Code formaté (black, isort)
- [ ] Pas d'erreurs de lint
- [ ] Documentation mise à jour si nécessaire

## 🤔 FAQ

**Q: Dois-je rebaser ou merger ?**
R: Préférez `rebase` pour les features, `merge` pour les releases/hotfixes.

**Q: Que faire si ma PR a des conflits ?**
R: Rebasez votre branche sur la branche cible et résolvez les conflits localement.

**Q: Puis-je pousser directement sur develop ?**
R: Non, toutes les modifications passent par des PRs.
