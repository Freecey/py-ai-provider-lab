# py-ai-provider-lab

Application desktop Python/Tkinter pour configurer, tester et historiser plusieurs providers d'IA (OpenAI, Anthropic, MiniMax, Alibaba, OpenRouter, Z.ai) sur les modalités texte, image, audio et vidéo.

## Prérequis

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

### GUI (interface graphique)
```bash
python -m app.main
```

### CLI
```bash
python -m app.main --cli providers list
python -m app.main --cli providers add --name OpenAI --url https://api.openai.com/v1
python -m app.main --cli run text --credential 1 --model 1 --prompt "Hello" --output json
```

### Mode sandbox (aucun appel réseau)
```bash
APP_SANDBOX_MODE=true python -m app.main
```

ou dans `config.ini` :
```ini
[app]
sandbox_mode = true
```

## Tests

```bash
python -m pytest app/tests/ -v
```

## Structure

```
app/
  main.py          # point d'entrée GUI/CLI
  cli.py           # CLI argparse
  config/          # settings, constantes
  models/          # dataclasses métier + résultats
  services/        # logique applicative
  providers/       # adaptateurs par provider
  storage/         # SQLite, migrations, repositories
  ui/              # GUI Tkinter
  utils/           # crypto, logger, http_client, formatters
  tests/           # tests unitaires
```

## Documentation

- [CLI_GUIDE.md](doc/CLI_GUIDE.md) — toutes les commandes avec exemples
- [ARCHITECTURE.md](doc/ARCHITECTURE.md) — architecture technique
- [SKILL.md](doc/SKILL.md) — utilisation par agent IA
