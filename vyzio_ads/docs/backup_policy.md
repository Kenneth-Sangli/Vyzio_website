# Politique de sauvegarde, rétention et restauration des données

## 1. Objectif
Assurer la sécurité, la disponibilité et la conformité RGPD des données applicatives (base de données et médias).

## 2. Sauvegarde (Backup)
- **Base SQLite (local/dev)** :
  - Un script PowerShell permet d'effectuer un dump quotidien de la base (`db.sqlite3`) dans le dossier `backups/`.
  - Les 30 dernières sauvegardes sont conservées, les plus anciennes sont supprimées automatiquement.
- **Base PostgreSQL (prod/ligne)** :
  - Utiliser `pg_dump` pour exporter la base.
  - Stocker les dumps sur un stockage sécurisé (cloud, S3, etc.).
  - Automatiser via cron (Linux) ou tâche planifiée (Windows).
- **Fichiers médias** :
  - Les médias sont stockés sur Cloudinary (redondance assurée par le fournisseur).

## 3. Rétention
- **Durée de conservation** : 30 jours pour les dumps locaux.
- **Rotation** : Suppression automatique des dumps les plus anciens.
- **Logs applicatifs** : Rotation automatique (5 fichiers de 5 Mo).

## 4. Restauration
- **SQLite** : `sqlite3 db.sqlite3 < backup_YYYYMMDD.sql`
- **PostgreSQL** : `psql -U <user> -d <dbname> -f backup_YYYYMMDD.sql`
- Tester régulièrement la restauration sur un environnement de préproduction.

## 5. RGPD
- Endpoints d'export et suppression des données utilisateur en place.
- Les sauvegardes sont à usage interne, non partagées avec des tiers.

## 6. Script de sauvegarde automatique (SQLite)
Voir `../scripts/backup_sqlite.ps1` pour automatiser la sauvegarde locale.

---

**À terme, pour PostgreSQL en production, prévoir :**
- Un script similaire utilisant `pg_dump`.
- Un stockage cloud sécurisé.
- Un monitoring des sauvegardes et des restaurations régulières.
