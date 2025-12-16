# Intégration Sentry (monitoring des erreurs)

1. Créez un compte Sentry.io et un projet pour votre backend.
2. Ajoutez la dépendance dans `requirements.txt` :
   sentry-sdk
3. Ajoutez ce code dans `config/settings/base.py` (ou settings.py) :

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.5,  # Ajustez selon besoin
    send_default_pii=True,
)

4. Ajoutez la variable d’environnement SENTRY_DSN dans Render.

---

# Health Check

- L’endpoint `/api/health/` doit retourner `{"status": "ok"}`.
- Configurez Render pour vérifier cet endpoint.

---

# Alerting

- Configurez Sentry pour envoyer des alertes email/slack en cas d’erreur critique.
- Ajoutez un monitoring Render (alertes sur downtime).

---

# Stockage Cloudinary

- Les variables Cloudinary sont déjà gérées dans `render.yaml`.
- Pour S3, ajoutez les clés AWS dans Render et configurez Django avec `django-storages`.

---

# Secrets & Variables d’environnement

- Ajoutez toutes les clés sensibles dans le dashboard Render (jamais en dur dans le code).
- Utilisez `os.environ.get("KEY")` ou `decouple.config("KEY")` dans le code.

---

# Documentation

- Documentez la procédure de déploiement et CI/CD dans `docs/deployment.md`.
