# Architecture — py-ai-provider-lab

## Vue d'ensemble des couches

```
┌─────────────────────────────────────────┐
│  Interface (CLI / GUI Tkinter)          │ app/cli.py · app/ui/
│  (aucune logique métier ici)            │
├─────────────────────────────────────────┤
│  Services                               │ app/services/
│  ProviderService · CredentialService    │
│  ModelService · TestService             │
│  HistoryService · ExportService         │
├─────────────────────────────────────────┤
│  Providers (adaptateurs)                │ app/providers/
│  BaseProvider (ABC)                     │
│  Mock · OpenAI · Anthropic              │
│  OpenRouter · Alibaba · MiniMax · Z.ai  │
├─────────────────────────────────────────┤
│  Storage                                │ app/storage/
│  Database (SQLite + migrations)         │
│  Repositories (un par entité)           │
│  Crypto (AES-256-GCM)                   │
├─────────────────────────────────────────┤
│  Modèles / entités                      │ app/models/
│  Provider · Credential · Model          │
│  TestRun · AsyncTask · Preset · ...     │
└─────────────────────────────────────────┘
```

## Règles d'architecture

1. **Aucune logique métier dans les vues** — les vues appellent exclusivement les services
2. **Aucun appel réseau dans le thread principal** — toujours via `threading.Thread`
3. **Chaque `run_*` crée un `TestRun`** même en cas d'échec
4. **Les secrets** sont chiffrés en base (AES-256-GCM), jamais loggués, masqués dans l'UI

## Ajout d'un provider

1. Créer `app/providers/myprovider.py` héritant de `BaseProvider` (ou `OpenAICompatProvider`)
2. Définir `slug = "myprovider"`
3. Implémenter `test_connection`, `list_models`, `run_text` (minimum)
4. Enregistrer dans `app/providers/__init__.py` : `register("myprovider", MyProvider)`
5. Insérer le provider en base via le seed ou le CLI

## Ajout d'une modalité

1. Ajouter la méthode dans `BaseProvider` (ex: `run_embeddings`)
2. L'implémenter dans les providers concernés
3. Ajouter le cas dans `TestService`
4. Ajouter les commandes CLI dans `app/cli/run.py`
5. Ajouter le panneau de paramètres dans `TestLabView._build_params`

## Async (Tkinter thread-safe)

Les appels réseau se font dans un `threading.Thread` dédié.
Les résultats remontent via `app.schedule(callback)` qui utilise une `queue.Queue`
drainée par `root.after(50, ...)` dans le thread principal.

## Migrations SQLite

Les fichiers `app/storage/migrations/*.sql` sont appliqués en ordre numérique.
La table `schema_version` trace la version courante.
Pour ajouter une migration : créer `002_description.sql` avec les DDL nécessaires.
