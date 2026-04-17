# CLI Guide — py-ai-provider-lab

## Invocation

```bash
python -m app.main --cli <command> [options]
```

> Note : `python app/main.py --cli ...` fonctionne aussi depuis la racine du projet.

## Exit codes

| Code | Signification |
|------|---------------|
| 0 | Succès |
| 1 | Erreur métier (credential invalide, modèle introuvable…) |
| 2 | Erreur réseau / timeout |
| 3 | Erreur de configuration |
| 4 | Entrée invalide |

## Commandes

### providers

```bash
# Lister
python -m app.main --cli providers list [--output json|table|plain] [--active-only]

# Afficher
python -m app.main --cli providers show <id> [--output json]

# Ajouter
python -m app.main --cli providers add --name <nom> --url <url> [--auth api_key|bearer|oauth2|custom]

# Modifier
python -m app.main --cli providers edit <id> [--name <nom>] [--url <url>] [--active true|false]

# Supprimer
python -m app.main --cli providers delete <id>
```

**Exemple JSON :**
```json
[
  {
    "id": 1,
    "name": "OpenAI",
    "slug": "openai",
    "active": true,
    "base_url": "https://api.openai.com/v1",
    "auth_type": "api_key"
  }
]
```

### credentials

```bash
python -m app.main --cli credentials list [--provider <id>] [--output json]
python -m app.main --cli credentials show <id>
python -m app.main --cli credentials add --provider <id> --name <nom> [--api-key <clé>]
python -m app.main --cli credentials edit <id> [--name <nom>] [--api-key <clé>] [--active true|false]
python -m app.main --cli credentials delete <id>
python -m app.main --cli credentials test <id>    # teste la connexion, met à jour la validité
```

### models

```bash
python -m app.main --cli models list [--provider <id>] [--type text|image|audio|video] [--output json] [--all]
python -m app.main --cli models show <id>
python -m app.main --cli models add --provider <id> --name <nom_technique> [--display-name <nom>] [--type text]
python -m app.main --cli models sync --provider <id> --credential <id>   # synchronise depuis l'API
```

### run

```bash
# Texte
python -m app.main --cli run text --credential <id> --model <id> --prompt "Hello" \
  [--system "Tu es un assistant"] [--temperature 0.7] [--max-tokens 1000] \
  [--stream] [--output json]

# Image
python -m app.main --cli run image --credential <id> --model <id> --prompt "Un chat sur Mars" \
  [--size 1024x1024]

# Audio
python -m app.main --cli run audio --credential <id> --model <id> --file audio.mp3 \
  --op transcription|speech|translation
```

**Exemple sortie JSON (texte) :**
```json
{
  "id": 42,
  "modality": "text",
  "status": "success",
  "response_raw": "Bonjour ! Comment puis-je vous aider ?",
  "latency_ms": 1234,
  "cost_estimated": null,
  "created_at": "2026-04-17T10:00:00"
}
```

### history

```bash
python -m app.main --cli history list [--provider <id>] [--model <id>] [--status success|error] \
  [--limit 20] [--output json|table|plain]
python -m app.main --cli history show <id>
python -m app.main --cli history export --format json|csv [--output fichier.json]
```

### health

```bash
python -m app.main --cli health [--provider <id>] [--output json]
```

**Exemple :**
```json
[{"provider_id": 1, "status": "ok", "latency_ms": 245, "message": "OK"}]
```

### config

```bash
python -m app.main --cli config export [--output config_backup.json]
python -m app.main --cli config import --file config_backup.json
```

## Options globales

```bash
--debug    # Active les logs HTTP détaillés (stderr)
--help     # Aide sur la commande
```

## Workflow automatisé (agent IA)

```bash
# 1. Créer le provider
python -m app.main --cli providers add --name Mock --url "" --output json

# 2. Créer un credential
python -m app.main --cli credentials add --provider 1 --name "Mock Cred" --output json

# 3. Synchroniser les modèles
python -m app.main --cli models sync --provider 1 --credential 1 --output json

# 4. Lancer un test texte
python -m app.main --cli run text --credential 1 --model 1 --prompt "Test" --output json

# 5. Consulter l'historique
python -m app.main --cli history list --limit 5 --output json
```
