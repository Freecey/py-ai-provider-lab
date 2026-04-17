# py-ai-provider-lab Skill

**Name:** `py-ai-provider-lab`
**Description:** Test AI provider APIs (OpenAI, Anthropic, MiniMax, Alibaba, OpenRouter, Z.ai) across text/image/audio/video modalities via CLI. Stores all results in SQLite with cost tracking and history.

## Prerequisites

```bash
cd ~/path/to/py-ai-provider-lab
pip install -r requirements.txt
```

Set env vars if needed:
```bash
export APP_CRYPTO_PASSPHRASE="your-passphrase"  # for encrypted credentials
export APP_SANDBOX_MODE=true                      # mock mode, no real API calls
export APP_DATA_DIR=/tmp/test                     # custom DB location
```

## Invocation

```bash
python -m app.main --cli <command> [args]
```

Always use `--output json` for machine-readable output.

---

## Workflow

### 1. Discover available providers

```bash
python -m app.main --cli providers list --output json
```

Returns array of `{id, name, slug, active, base_url}`.

### 2. Verify credentials exist

```bash
python -m app.main --cli credentials list --provider <provider_id> --output json
```

### 3. Test connectivity

```bash
python -m app.main --cli credentials test <credential_id> --output json
```

Expected: `{"success": true, "latency_ms": 320, "message": "OK"}`

### 4. List models for a provider

```bash
python -m app.main --cli models list --provider <provider_id> --output json
```

Returns array of `{id, technical_name, display_name, type, active}`.

### 5. Run a text test

```bash
python -m app.main --cli run text \
  --credential <credential_id> \
  --model <model_id> \
  --prompt "Résume ce texte : ..." \
  --system "Tu es un assistant utile." \
  --temperature 0.7 \
  --max-tokens 500 \
  --output json
```

### 6. Run an image generation test

```bash
python -m app.main --cli run image \
  --credential <credential_id> \
  --model <model_id> \
  --prompt "A futuristic city at sunset" \
  --size 1024x1024 \
  --output json
```

### 7. Run an audio transcription test

```bash
python -m app.main --cli run audio \
  --credential <credential_id> \
  --model <model_id> \
  --file /path/to/audio.mp3 \
  --output json
```

### 8. Check history

```bash
# Last 10 runs
python -m app.main --cli history list --limit 10 --output json

# Show a specific run
python -m app.main --cli history show <run_id> --output json

# Export to CSV
python -m app.main --cli history export --format csv --output results.csv
```

### 9. Health check all providers

```bash
python -m app.main --cli health --output json
```

---

## Output Format

All `--output json` commands return parsable JSON.

**`run text` success:**
```json
{
  "id": 42,
  "status": "success",
  "modality": "text",
  "response_raw": "Voici un résumé...",
  "latency_ms": 1240,
  "cost_estimated": null,
  "created_at": "2026-04-17T10:23:00"
}
```

**`run text` error:**
```json
{
  "id": 43,
  "status": "error",
  "error_message": "HTTP 401: Unauthorized",
  "latency_ms": 210
}
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Read stdout |
| 1 | Business error | Check parameters (credential_id, model_id) |
| 2 | Network error | Retry after delay |
| 3 | Config missing | Check config.ini or env vars |
| 4 | Invalid input | Fix arguments |

---

## Managing Credentials (via CLI)

```bash
# Add a credential
python -m app.main --cli credentials add \
  --provider <provider_id> \
  --name "openai-prod" \
  --api-key "sk-..." \
  --output json

# Edit (rotate key)
python -m app.main --cli credentials edit <id> \
  --api-key "sk-new-key" \
  --output json

# Delete
python -m app.main --cli credentials delete <id>
```

---

## Managing Models

```bash
# Add a model manually
python -m app.main --cli models add \
  --provider <provider_id> \
  --name "gpt-4o" \
  --display-name "GPT-4o" \
  --output json

# Sync models from provider API
python -m app.main --cli models sync --provider <provider_id> --output json
```

---

## Config Import/Export

```bash
# Export configuration (no secrets)
python -m app.main --cli config export --output config_backup.json

# Import configuration
python -m app.main --cli config import config_backup.json
```

---

## Providers Available

| Slug | Provider | Modalities |
|------|----------|-----------|
| `mock` | MockProvider | text, image, audio |
| `openai` | OpenAI | text, image |
| `anthropic` | Anthropic | text |
| `openrouter` | OpenRouter | text |
| `alibaba` | Alibaba DashScope | text |
| `minimax` | MiniMax | text, video (async) |
| `zai` | Z.ai | text (partial) |

---

## Sandbox / Mock Mode

Set `APP_SANDBOX_MODE=true` to run without real API calls. MockProvider returns deterministic fake responses with simulated latency.

```bash
APP_SANDBOX_MODE=true python -m app.main --cli run text \
  --credential 1 --model 1 \
  --prompt "Hello" --output json
```

---

## Agent Tips

- Always call `providers list` then `credentials list --provider <id>` before `run` — IDs are auto-incremented integers
- Use `credentials test <id>` to verify connectivity before bulk runs
- Use `run_multi` pattern: iterate over credential/model pairs, call `run text` for each
- For video generation (MiniMax): `run video` returns `status: "pending"` with an async task — poll `history show <run_id>` until `status: "success"`
- Results are always persisted in SQLite even on failure — use `history list` for auditing
