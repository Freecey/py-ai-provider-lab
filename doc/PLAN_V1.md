# Plan de développement — py-ai-provider-lab
# Basé sur CDC_V1.md

---

## Principes directeurs

* Chaque phase produit quelque chose de **fonctionnel et testable**
* La couche métier est toujours développée **avant** les interfaces (CLI et GUI consomment les services)
* Le CLI est développé **avant** la GUI — il sert de validation de la couche métier
* Aucune interface ne contient de logique métier
* Chaque provider est intégré de façon **incrémentale** : d'abord le squelette, puis les modalités

---

## Vue d'ensemble des phases

| Phase | Contenu | Prérequis |
|---|---|---|
| 0 | Setup, structure, config | — |
| 1 | Modèles de données + persistance | 0 |
| 2 | Provider abstraction + Mock + OpenAI | 1 |
| 3 | Services métier core | 2 |
| 4 | CLI core | 3 |
| 5 | GUI squelette + navigation | 3 |
| 6 | GUI sections CRUD | 5 |
| 7 | Test Lab (GUI + CLI) | 4, 6 |
| 8 | Historique + Notation | 7 |
| 9 | Providers supplémentaires | 3 |
| 10 | Tests + QA + documentation | toutes |

---

## Phase 0 — Setup et infrastructure

**Objectif :** projet lançable, structure en place, config chargée.

### 0.1 Structure du projet

Créer l'arborescence complète :

```
app/
  main.py
  cli.py
  ui/
    __init__.py
    app_window.py
    widgets/
    views/
      dashboard.py
      providers.py
      credentials.py
      models.py
      testlab.py
      history.py
      compare.py
      settings.py
  models/
    __init__.py
    provider.py
    credential.py
    model.py
    preset.py
    test_run.py
    async_task.py
    prompt_template.py
  services/
    __init__.py
    provider_service.py
    credential_service.py
    model_service.py
    test_service.py
    history_service.py
    export_service.py
  providers/
    __init__.py
    base.py
    mock.py
    openai_compat.py
    openai.py
    anthropic.py
    minimax.py
    openrouter.py
    zai.py
    alibaba.py
  storage/
    __init__.py
    db.py
    migrations/
      001_initial.sql
    repositories/
      provider_repo.py
      credential_repo.py
      model_repo.py
      preset_repo.py
      test_run_repo.py
      async_task_repo.py
      prompt_template_repo.py
  utils/
    __init__.py
    crypto.py
    logger.py
    http_client.py
    formatters.py
  config/
    __init__.py
    settings.py
    constants.py
  tests/
    __init__.py
    test_storage.py
    test_services.py
    test_providers.py
config.ini
requirements.txt
README.md
```

### 0.2 Configuration

- Implémenter `config/settings.py` : chargement `config.ini` + surcharge par variables d'environnement
- Paramètres : `data_dir`, `log_level`, `theme`, `lang`, `network_timeout`, `sandbox_mode`
- Créer `config.ini` avec valeurs par défaut documentées

### 0.3 Logger

- `utils/logger.py` : wrapper autour de `logging` standard
- Niveaux configurables, format horodaté
- Masquage automatique des patterns secrets dans les messages (`***`)

### 0.4 Dépendances

Figer `requirements.txt` MVP :

```
requests>=2.31
cryptography>=42.0
pytest>=8.0
```

*(Tkinter est inclus dans Python standard — pas de dépendance externe)*

---

## Phase 1 — Modèles de données et persistance

**Objectif :** schéma SQLite en place, repositories fonctionnels, migrations versionnées.

### 1.1 Entités métier (dataclasses)

Implémenter dans `models/` :

**`Provider`**
```
id, name, slug, active, base_url, endpoints (JSON),
api_version, auth_type, custom_headers (JSON),
timeout_global, timeout_per_modality (JSON),
retry_count, retry_delay, retry_backoff,
proxy, notes, extra_fields (JSON),
created_at, updated_at
```

**`Credential`**
```
id, provider_id, name, active, validity,
api_key (encrypted), bearer_token (encrypted),
oauth_access_token (encrypted), oauth_refresh_token (encrypted),
oauth_client_id, oauth_client_secret (encrypted),
oauth_scopes, oauth_auth_url, oauth_token_endpoint,
oauth_expires_at, org_id, project_id, notes,
created_at, updated_at
```

**`Model`**
```
id, provider_id, technical_name, display_name,
type (text/image/audio/video/multimodal/embedding/other),
active, favorite, rating,
context_max, cost_input, cost_output, currency,
rpm_limit, tpm_limit,
tags (JSON), notes, extra (JSON),
created_at, updated_at
```

**`ModelCapability`**
```
id, model_id, capability
(chat / reasoning / vision / image_gen / video_gen /
video_understanding / transcription / speech /
embeddings / tool_calling / json_output / streaming)
```

**`Preset`**
```
id, name, modality, model_id (nullable),
params (JSON), created_at, updated_at
```

**`TestRun`**
```
id, provider_id, credential_id, model_id,
modality, params (JSON), request_payload (JSON),
response_raw (TEXT), response_files (JSON),
latency_ms, cost_estimated, currency,
status (success/error/pending/cancelled),
error_message, rating, rating_notes,
created_at
```

**`AsyncTask`**
```
id, test_run_id, provider_task_id,
status (pending/running/done/failed),
poll_interval_s, timeout_s, last_polled_at,
result (JSON), error, created_at, updated_at
```

**`PromptTemplate`**
```
id, title, content, modality, category, tags (JSON),
created_at, updated_at
```

### 1.2 Schéma SQLite et migrations

- `storage/db.py` : connexion SQLite, exécution des migrations au démarrage
- `storage/migrations/001_initial.sql` : création de toutes les tables + table `schema_version`
- Mécanisme de migration séquentielle (lecture de `schema_version`, application des fichiers manquants)

### 1.3 Repositories

Un repository par entité, interface commune :

```python
class BaseRepository:
    def get_by_id(self, id) -> Entity | None
    def list(self, **filters) -> list[Entity]
    def create(self, entity) -> Entity
    def update(self, entity) -> Entity
    def delete(self, id) -> bool
```

Chaque repository implémente les requêtes spécifiques (ex : `CredentialRepository.list_by_provider(provider_id)`).

### 1.4 Chiffrement des secrets

- `utils/crypto.py` : chiffrement/déchiffrement AES-256-GCM
- Clé dérivée d'une passphrase (PBKDF2) ou via `keyring` OS si disponible
- Interface : `encrypt(plaintext) -> str` / `decrypt(ciphertext) -> str`
- Les repositories appellent crypto de façon transparente pour les champs sensibles

### 1.5 Données initiales

- Insérer les 6 providers de référence avec leurs métadonnées de base
- Insérer les prompts templates standards (résumé, extraction JSON, traduction, classification, génération image, transcription)
- Insérer le provider Mock

---

## Phase 2 — Abstraction provider + premiers adaptateurs

**Objectif :** `BaseProvider` défini, Mock fonctionnel, OpenAI texte fonctionnel.

### 2.1 BaseProvider

```python
class BaseProvider(ABC):
    @abstractmethod
    def test_connection(self, credentials: Credential) -> ConnectionResult
    @abstractmethod
    def list_models(self, credentials: Credential) -> list[ModelInfo]
    def run_text(self, credentials, model, params) -> TextResult
    def run_image(self, credentials, model, params) -> ImageResult
    def run_audio(self, credentials, model, params) -> AudioResult
    def run_video(self, credentials, model, params) -> VideoResult | AsyncTaskRef
    def poll_task(self, credentials, task_ref) -> TaskStatus
    def normalize_capabilities(self, raw) -> ModelCapabilities
```

- Méthodes non obligatoires lèvent `NotImplementedError` avec message explicite
- `ConnectionResult`, `TextResult`, `ImageResult`, `AudioResult`, `VideoResult`, `AsyncTaskRef`, `TaskStatus` : dataclasses normalisées dans `models/`

### 2.2 HTTP client commun

- `utils/http_client.py` : wrapper `requests` avec retry, timeout, logging des requêtes/réponses
- Masquage automatique des headers `Authorization` dans les logs
- Capture systématique : URL, méthode, payload, headers, code retour, durée, réponse brute

### 2.3 MockProvider

- Modèles fictifs : `mock-text-v1`, `mock-image-v1`, `mock-audio-v1`
- Réponses prédéfinies paramétrables
- Latence simulée configurable
- Toujours disponible, ne nécessite pas de credentials

### 2.4 OpenAI-compatible (générique)

- `providers/openai_compat.py` : implémente `run_text` sur base d'une URL et d'une API key arbitraires
- Sert de base pour OpenAI, OpenRouter, et toute API compatible

### 2.5 OpenAI

- Hérite de `openai_compat.py`
- `test_connection` : appel `/models`
- `list_models` : parse et normalise la réponse
- `run_text` : chat completion avec tous les paramètres du CDC §10
- Streaming via `stream=True` + callback

### 2.6 Anthropic

- `run_text` : messages API
- `list_models` : liste statique ou API si disponible
- Streaming supporté

---

## Phase 3 — Services métier

**Objectif :** toute la logique métier encapsulée, testable indépendamment de l'interface.

### 3.1 ProviderService

```python
list_providers(active_only=False) -> list[Provider]
get_provider(id) -> Provider
create_provider(data) -> Provider
update_provider(id, data) -> Provider
delete_provider(id) -> bool
health_check(provider_id, credential_id) -> HealthStatus
health_check_all() -> dict[id, HealthStatus]
```

### 3.2 CredentialService

```python
list_credentials(provider_id=None) -> list[Credential]
get_credential(id) -> Credential
create_credential(data) -> Credential
update_credential(id, data) -> Credential
delete_credential(id) -> bool
duplicate_credential(id) -> Credential
test_connection(credential_id) -> ConnectionResult
refresh_oauth_token(credential_id) -> Credential
```

### 3.3 ModelService

```python
list_models(provider_id=None, type=None, active_only=True) -> list[Model]
get_model(id) -> Model
create_model(data) -> Model
update_model(id, data) -> Model
delete_model(id) -> bool
sync_models(provider_id, credential_id) -> SyncResult
rate_model(model_id, rating) -> Model
```

### 3.4 TestService

```python
run_text(credential_id, model_id, params) -> TestRun
run_image(credential_id, model_id, params) -> TestRun
run_audio(credential_id, model_id, params, file_path) -> TestRun
run_video(credential_id, model_id, params) -> TestRun | AsyncTaskRef
poll_async_task(task_id) -> TaskStatus
cancel_async_task(task_id) -> bool
run_multi(credential_model_pairs, modality, params) -> list[TestRun]
```

Chaque `run_*` :
1. résout le provider adapter
2. prépare les paramètres
3. exécute dans un thread (appelé depuis le service, non bloquant si callback fourni)
4. crée et persiste un `TestRun`
5. retourne le résultat ou une référence de tâche async

### 3.5 HistoryService

```python
list_runs(filters) -> list[TestRun]
get_run(id) -> TestRun
rate_run(id, rating, notes) -> TestRun
delete_run(id) -> bool
replay_run(id) -> TestRun
export_runs(filters, format) -> str | bytes
```

### 3.6 ExportService

```python
export_history(runs, format) -> str         # json ou csv
export_config(include_providers, include_models) -> dict  # sans secrets
import_config(data) -> ImportResult
```

---

## Phase 4 — CLI

**Objectif :** toutes les commandes core fonctionnelles, `--output json` opérationnel.

### 4.1 Structure CLI

- `cli.py` : point d'entrée, parser `argparse` avec sous-commandes
- Chaque groupe de commandes dans un module : `cli/providers.py`, `cli/credentials.py`, etc.
- Formatter de sortie centralisé : `table` (tabulate ou manuel), `json` (json.dumps), `plain`
- Gestion des exit codes : 0/1/2/3/4 (voir CDC §17)

### 4.2 Commandes à implémenter (dans l'ordre)

```
# Providers
app providers list [--output json|table|plain]
app providers show <id>
app providers add --name <n> --url <url> [--auth api_key|bearer|oauth2|custom]
app providers edit <id> [--name] [--url] [--active true|false]
app providers delete <id>

# Credentials
app credentials list [--provider <id>] [--output ...]
app credentials show <id>
app credentials add --provider <id> --name <n> [--api-key <k>]
app credentials edit <id> [options]
app credentials delete <id>
app credentials test <id>

# Models
app models list [--provider <id>] [--type text|image|audio|video] [--output ...]
app models show <id>
app models add --provider <id> --name <n> --type <t>
app models sync --provider <id> --credential <id>

# Tests
app run text --credential <id> --model <id> --prompt <text> [--system <text>] [--temperature 0.7] [--max-tokens 1000] [--output json]
app run image --credential <id> --model <id> --prompt <text> [--size 1024x1024]
app run audio --credential <id> --model <id> --file <path> --op transcription|speech|translation

# Historique
app history list [--provider <id>] [--model <id>] [--status success|error] [--limit 20] [--output ...]
app history show <id>
app history export --format json|csv [--output <file>]

# Config
app config export [--output <file>]
app config import --file <path>

# Santé
app health [--provider <id>] [--output ...]
```

### 4.3 Mode debug CLI

Flag global `--debug` : active les logs HTTP détaillés sur stderr.

---

## Phase 5 — GUI squelette

**Objectif :** fenêtre principale fonctionnelle, navigation entre sections, barre de statut.

### 5.1 AppWindow

- `ui/app_window.py` : fenêtre principale Tkinter
- Panneau latéral avec boutons de navigation
- Zone centrale : frame swappable selon la section active
- Barre de statut en bas (message + indicateur activité)
- Redimensionnable, taille minimale définie

### 5.2 Navigation

- 8 sections : Dashboard, Providers, Credentials, Models, Test Lab, History, Compare, Settings
- Chargement lazy des vues (instanciation à la première visite)

### 5.3 Zone logs

- Panel rétractable en bas (ou onglet dédié)
- Affichage des logs en temps réel (niveau configurable)
- Copie du contenu possible

### 5.4 Widgets communs

Dans `ui/widgets/` :

- `FilterableTable` : Treeview + champ de filtre + tri par colonne
- `SecretField` : Entry masqué + bouton révéler
- `StatusBadge` : label coloré selon état
- `ProgressDialog` : fenêtre modale avec barre de progression + bouton annuler
- `ConfirmDialog` : confirmation avant action destructive

---

## Phase 6 — GUI sections CRUD

**Objectif :** gestion complète de providers, credentials, modèles depuis l'interface.

### 6.1 Vue Providers

- Liste filtrée avec colonnes : nom, URL, auth, statut, santé
- Actions : ajouter, modifier, supprimer, activer/désactiver, tester la connexion
- Formulaire d'édition complet (modale)

### 6.2 Vue Credentials

- Liste filtrée par provider avec colonnes : nom, provider, validité, statut
- Formulaire complet avec onglets : Basic (api_key/bearer) + OAuth2
- Champs secrets via `SecretField`
- Bouton "Tester la connexion"

### 6.3 Vue Models

- Liste filtrée (provider, type, favori, tag)
- Colonnes : nom, provider, type, capacités (icônes), coût, note, favori
- Formulaire d'édition + gestion des capacités (checkboxes)
- Bouton "Synchroniser depuis l'API"

### 6.4 Vue Settings

- Formulaire des paramètres `config.ini`
- Gestion de la passphrase de chiffrement
- Thème, langue, timeout global

### 6.5 Vue Dashboard

- Widgets de comptage (providers, profils, modèles)
- Tableau des derniers tests
- Tableau des derniers échecs
- Indicateurs de santé par provider

---

## Phase 7 — Test Lab

**Objectif :** exécution de tests depuis GUI et CLI, résultats affichés et sauvegardés.

### 7.1 Interface Test Lab (GUI)

Flux de sélection : provider → credential → modèle → modalité → preset

Panneau paramètres : champs adaptés à la modalité sélectionnée, chargement/sauvegarde preset

Panneau résultat :
- Onglet "Requête" : URL, méthode, payload, headers masqués
- Onglet "Réponse" : réponse brute + formatée (texte/image/audio)
- Métriques : latence, coût estimé, statut
- Boutons : Lancer, Annuler, Sauvegarder, Relancer

Tâches asynchrones : barre de polling avec statut temps réel, bouton "Récupérer plus tard".

### 7.2 Presets (GUI)

- Liste des presets dans une sidebar du Test Lab
- Sauvegarde du preset courant avec nom
- Chargement rapide par clic

### 7.3 CLI run

- Déjà couvert en Phase 4
- Vérifier la cohérence des sorties JSON avec le format interne

---

## Phase 8 — Historique et notation

**Objectif :** historique complet, filtrable, exportable.

### 8.1 Vue History (GUI)

- Tableau filtrable : provider, modèle, modalité, date, statut
- Colonnes : date, provider, modèle, modalité, latence, coût, statut, note
- Détail d'un test (panneau latéral ou modale)
- Actions : relancer, dupliquer, noter, supprimer, exporter

### 8.2 Vue Compare (GUI)

- Sélection de 2 à N entrées d'historique
- Affichage côte à côte : paramètres + réponse + métriques
- Mode multi-run : lancer le même prompt sur N modèles, attente parallèle, affichage comparatif

### 8.3 Notation

- Étoiles 1–5 sur les tests et les modèles
- Champ commentaire libre
- Mise à jour possible depuis History et depuis Test Lab

---

## Phase 9 — Providers supplémentaires

**Objectif :** intégrer les providers restants avec au minimum `run_text`.

Ordre recommandé (du plus standard au plus spécifique) :

| Provider | Priorité | Notes |
|---|---|---|
| OpenRouter | haute | compatible openai_compat |
| Anthropic | haute | déjà en Phase 2 |
| Alibaba (DashScope) | moyenne | API propre, doc disponible |
| MiniMax | moyenne | tâches async pour vidéo |
| Z.ai | basse | vérifier doc disponible |

Pour chaque provider :

1. `test_connection` + `list_models`
2. `run_text`
3. `run_image` si supporté
4. `run_audio` si supporté
5. `run_video` si supporté (avec `poll_task`)

Provider marqué `[PARTIEL]` si implémentation incomplète.

---

## Phase 10 — Tests, QA et documentation

**Objectif :** projet stable, documenté, livrable.

### 10.1 Tests unitaires

- `tests/test_storage.py` : repositories (SQLite en mémoire)
- `tests/test_services.py` : services avec providers mockés
- `tests/test_providers.py` : adaptateurs avec responses HTTP mockées (`responses` ou `unittest.mock`)
- `tests/test_cli.py` : commandes CLI avec assertions sur stdout et exit code

### 10.2 Documentation

**README.md**
- Prérequis
- Installation
- Lancement GUI : `python main.py`
- Lancement CLI : `python main.py --cli <commandes>`
- Lancement mode sandbox : `python main.py --sandbox`

**doc/CLI_GUIDE.md**
- Toutes les commandes avec exemples
- Exemples de sorties JSON
- Exit codes

**doc/ARCHITECTURE.md**
- Diagramme de l'arborescence
- Rôle de chaque couche
- Comment ajouter un provider
- Comment ajouter une modalité

**doc/SKILL.md**
- Description du CLI orientée agent IA
- Commandes déterministes recommandées
- Format des entrées/sorties
- Exemples de workflows automatisés

### 10.3 Provider mock — données d'exemple

Fournir en base initiale :
- 1 provider Mock configuré
- 2 credentials d'exemple (mock + sandbox OpenAI)
- 5 modèles fictifs avec capacités variées
- 10 tests d'historique d'exemple
- 6 prompts templates

---

## Dépendances entre phases

```
0 → 1 → 2 → 3 → 4 (CLI)
                ↓
                5 → 6 → 7 (Test Lab GUI)
                         ↓
                         8 (History GUI)
         9 (providers) → 3 (services, parallélisable après Phase 3)
                         10 (QA, en dernier)
```

---

## Estimation de charge (indicative)

| Phase | Complexité | 
|---|---|
| 0 — Setup | faible |
| 1 — Modèles + Storage | moyenne |
| 2 — Provider base + OpenAI | moyenne |
| 3 — Services | moyenne-haute |
| 4 — CLI | moyenne |
| 5 — GUI squelette | moyenne |
| 6 — GUI CRUD | haute |
| 7 — Test Lab | haute |
| 8 — History + Compare | moyenne |
| 9 — Providers supplémentaires | moyenne par provider |
| 10 — Tests + Docs | moyenne |

---

## Règles de développement

* Une fonctionnalité = un service + un repo + des tests avant l'interface
* Chaque provider concret : toujours hériter de `BaseProvider`, jamais de logique HTTP directe hors du provider
* Aucune logique dans les vues Tkinter : les vues appellent les services uniquement
* Aucun appel réseau dans le thread principal
* Chaque `run_*` crée systématiquement un `TestRun` en base, même en cas d'échec
* Les erreurs réseau ne font jamais crasher l'application
