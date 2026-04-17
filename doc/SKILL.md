# SKILL — py-ai-provider-lab CLI Agent Guide

Ce document décrit comment un agent IA peut piloter l'application via son interface CLI.

## Invocation

```bash
python -m app.main --cli <command> [args]
```

## Commandes déterministes (recommandées pour agents)

Toujours utiliser `--output json` pour des sorties parsables.

### Découverte

```bash
# Lister les providers disponibles
python -m app.main --cli providers list --output json

# Lister les credentials d'un provider
python -m app.main --cli credentials list --provider <id> --output json

# Lister les modèles disponibles
python -m app.main --cli models list --provider <id> --output json

# Vérifier la santé des providers
python -m app.main --cli health --output json
```

### Test texte

```bash
python -m app.main --cli run text \
  --credential <credential_id> \
  --model <model_id> \
  --prompt "Résume ce texte : ..." \
  --max-tokens 500 \
  --output json
```

**Sortie attendue :**
```json
{
  "id": 1,
  "status": "success",
  "response_raw": "...",
  "latency_ms": 1200,
  "cost_estimated": null
}
```

### Test image

```bash
python -m app.main --cli run image \
  --credential <id> --model <id> \
  --prompt "A futuristic city at sunset" \
  --output json
```

### Historique

```bash
# Derniers 10 tests
python -m app.main --cli history list --limit 10 --output json

# Exporter en CSV
python -m app.main --cli history export --format csv --output results.csv
```

## Format des IDs

Les IDs sont des entiers auto-incrémentés. Toujours récupérer les IDs via `list` avant d'appeler `show`, `run`, etc.

## Gestion des erreurs

| Exit code | Signification | Action recommandée |
|-----------|---------------|--------------------|
| 0 | Succès | Lire stdout |
| 1 | Erreur métier | Vérifier les paramètres (credential_id, model_id) |
| 2 | Erreur réseau | Retry après délai |
| 3 | Config manquante | Vérifier config.ini ou variables d'environnement |
| 4 | Entrée invalide | Corriger les arguments |

## Workflow type pour un agent

```bash
# 1. Vérifier quels providers sont actifs
python -m app.main --cli providers list --active-only --output json

# 2. Choisir un credential valide
python -m app.main --cli credentials list --provider 1 --output json

# 3. Tester la connexion
python -m app.main --cli credentials test 1 --output json

# 4. Lancer un test
python -m app.main --cli run text --credential 1 --model 3 \
  --prompt "Hello" --output json

# 5. Consulter l'historique
python -m app.main --cli history list --limit 1 --output json
```

## Variables d'environnement

| Variable | Effet |
|----------|-------|
| `APP_SANDBOX_MODE=true` | Mode mock, aucun appel réseau |
| `APP_LOG_LEVEL=DEBUG` | Logs détaillés |
| `APP_DATA_DIR=/tmp/test` | Base SQLite dans /tmp/test |
| `APP_CRYPTO_PASSPHRASE=secret` | Passphrase de chiffrement |
