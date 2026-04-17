# Cahier des charges — Application Python Tkinter de test de providers IA
# Version 1.0

---

## 1. Objet

Développer une application desktop en **Python** avec interface graphique **Tkinter** permettant de **configurer, tester, comparer et historiser** plusieurs providers d'IA ainsi que les modèles qu'ils proposent, sur les modalités suivantes :

* **Texte**
* **Image**
* **Audio**
* **Vidéo**
* **Autres modalités si supportées par le provider**

L'application sert d'outil local de travail pour évaluer différents fournisseurs, leurs modèles, leurs paramètres, leurs performances, leur coût et leur stabilité.

---

## 2. Providers à supporter

L'application devra prendre en charge au minimum :

* **MiniMax**
* **Z.ai**
* **OpenAI**
* **Alibaba (Qwen / DashScope)**
* **Anthropic**
* **OpenRouter**

L'architecture devra être **extensible** : ajout d'un nouveau provider sans modifier le cœur applicatif.

Un **adaptateur générique OpenAI-compatible** devra être prévu pour couvrir les APIs tierces suivant ce standard.

---

## 3. Contraintes techniques

| Contrainte | Valeur |
|---|---|
| Langage | Python 3.11+ |
| Interface graphique | Tkinter + ttk |
| Persistance | SQLite (données métier) + JSON (préférences, exports) |
| Async | `threading.Thread` + queue de callbacks Tkinter |
| Dépendances | limitées au strict nécessaire |
| Portabilité | Linux, macOS, Windows |
| Mode d'exécution | GUI desktop + CLI scriptable |

### Stratégie async

Les appels réseau ne doivent jamais bloquer l'interface. Stratégie retenue :

* exécution dans un `threading.Thread` dédié
* résultats remontés via `root.after()` ou une queue `queue.Queue`
* barre de progression et bouton d'annulation sur toutes les opérations longues

### Tâches longues (vidéo, batch)

Certains providers (MiniMax, Kling, etc.) ont des APIs asynchrones avec polling de statut. L'application devra prévoir :

* un mécanisme de suivi de tâche : état `pending / running / done / failed`
* un polling configurable (intervalle, timeout max)
* affichage du statut en temps réel dans l'interface
* possibilité de récupérer le résultat ultérieurement si l'app est relancée

---

## 4. Configuration de l'application

Un fichier `config.ini` (ou `.env`) devra permettre de configurer :

* répertoire de données (base SQLite, fichiers médias)
* niveau de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
* thème visuel par défaut
* langue (fr/en, extensible)
* timeout réseau global par défaut
* activation du mode sandbox/mock

Ce fichier devra être chargé au démarrage et surchargeable par variables d'environnement.

---

## 5. Architecture logicielle

```
app/
  main.py              # point d'entrée (GUI ou CLI selon args)
  cli.py               # point d'entrée CLI
  ui/                  # vues Tkinter, formulaires, dialogues, tableaux
  models/              # entités métier (dataclasses ou Pydantic)
  services/            # logique applicative (provider_service, model_service, test_service…)
  providers/           # adaptateurs par provider
    base.py            # classe abstraite BaseProvider
    openai_compat.py   # adaptateur générique OpenAI-compatible
    minimax.py
    anthropic.py
    openrouter.py
    ...
  storage/             # couche persistance SQLite/JSON
    db.py              # connexion, migrations
    repositories/      # un repo par entité
  utils/               # helpers techniques
  config/              # constantes, chargement config
  tests/               # tests unitaires (services + providers mockés)
```

### Abstraction provider

```python
class BaseProvider(ABC):
    def test_connection(self, credentials) -> ConnectionResult
    def list_models(self, credentials) -> list[ModelInfo]
    def run_text(self, credentials, model, params) -> TextResult
    def run_image(self, credentials, model, params) -> ImageResult
    def run_audio(self, credentials, model, params) -> AudioResult
    def run_video(self, credentials, model, params) -> VideoResult | AsyncTaskRef
    def poll_task(self, credentials, task_ref) -> TaskStatus  # pour les providers async
    def normalize_capabilities(self, raw_model) -> ModelCapabilities
```

Chaque provider concret implémente l'interface et lève `NotImplementedError` pour les capacités non supportées — jamais de silence silencieux.

---

## 6. Gestion des providers

Pour chaque provider :

* nom et identifiant technique
* statut actif / inactif
* URL de base
* endpoint(s) par modalité
* version d'API
* type d'authentification (`api_key`, `bearer`, `oauth2`, `custom`)
* en-têtes personnalisés (paires clé/valeur)
* timeout (global + par modalité)
* stratégie de retry (nombre, délai, backoff)
* proxy (optionnel)
* notes internes
* champs spécifiques provider (JSON libre)

---

## 7. Gestion des credentials

L'application gère **plusieurs profils d'accès par provider**.

Exemples : `OpenAI perso`, `OpenAI pro`, `OpenRouter compte A`.

### Données par profil

* nom du profil
* provider associé
* api_key
* bearer token
* oauth2 : access_token, refresh_token, client_id, client_secret, scopes, authorization_url, token_endpoint, expiration
* organisation / project_id
* statut actif / inactif
* validité (ok / invalide / non testé)
* date création / modification
* notes

### Opérations

* créer, modifier, supprimer, dupliquer, activer/désactiver
* tester la connexion
* rafraîchir un token OAuth2

### Sécurité

* secrets masqués par défaut dans l'interface, révélation sur action explicite
* secrets jamais affichés dans les logs (remplacés par `***`)
* stockage : champs sensibles chiffrés en base (AES-256, clé dérivée d'une passphrase locale ou keyring OS)
* aucune transmission de secrets vers un service externe autre que le provider cible

---

## 8. Gestion OAuth2

L'application doit supporter OAuth2 proprement :

* saisie et stockage de tous les champs (§7)
* test d'authentification
* rafraîchissement de token automatique si expiré avant un appel
* détection d'expiration et alerte utilisateur
* structure extensible par provider

Si un flux OAuth2 complet n'est pas implémentable immédiatement (documentation manquante, redirect URI complexe), l'application devra fournir :

* architecture et modèle de données complets
* formulaire GUI complet
* connecteur marqué `[PARTIEL]` avec message explicite

---

## 9. Gestion des modèles

Pour chaque provider :

* synchroniser la liste via API si disponible
* ajouter / modifier / supprimer / désactiver manuellement

### Métadonnées par modèle

* nom technique + nom affiché
* provider
* type principal : `text`, `image`, `audio`, `video`, `multimodal`, `embedding`, `other`
* capacités : `chat`, `reasoning`, `vision`, `image_gen`, `video_gen`, `video_understanding`, `transcription`, `speech`, `embeddings`, `tool_calling`, `json_output`, `streaming`
* contexte max (tokens)
* coût input/output (par 1K tokens ou par image/seconde)
* devise
* limites RPM / TPM si connues
* statut actif / inactif / favori
* note (1–5)
* tags libres
* commentaires

---

## 10. Presets de test

Presets enregistrables par modèle ou par type de tâche.

Opérations : créer, modifier, dupliquer, renommer, supprimer, appliquer.

### Texte

`system_prompt`, `user_prompt`, `temperature`, `top_p`, `max_tokens`, `frequency_penalty`, `presence_penalty`, `stop_sequences`, `seed`, `json_mode`, `streaming`

### Image

`prompt`, `negative_prompt`, `size`, `ratio`, `quality`, `steps`, `seed`, `output_format`, `n`

### Audio

`file_input`, `operation` (`transcription`/`speech`/`translation`), `voice`, `format`, `sample_rate`, `language`, `temperature`, `diarization`, `timestamps`

### Vidéo

`prompt`, `negative_prompt`, `source_image`, `source_video`, `duration`, `resolution`, `ratio`, `fps`, `seed`, `output_format`, `n_variants`, `mode` (`generate`/`edit`/`transform`/`upscale`), `audio_track`, `provider_params` (JSON libre)

### Autres modalités

Architecture extensible pour : `embeddings`, `vision_analysis`, `reranking`, `moderation`, `tool_calling`, `document_understanding`.

---

## 11. Test Lab (interface de test)

Sélection : provider → profil → modèle → modalité → preset (optionnel)

Depuis l'interface :

* saisir / modifier les paramètres
* lancer le test
* voir la requête envoyée (URL, méthode, payload, headers masqués)
* voir la réponse brute et formatée
* mesurer la latence
* voir le statut (succès / échec / en cours)
* voir le coût estimé si disponible
* sauvegarder dans l'historique

Pour les tâches asynchrones (vidéo) : affichage du statut de polling, résultat récupérable après fermeture.

---

## 12. Historique des tests

Toutes les exécutions sont historisées en SQLite.

### Données conservées

* date/heure
* provider, profil, modèle
* modalité et paramètres
* requête (payload)
* réponse (texte ou référence fichier media)
* latence (ms)
* coût estimé
* statut + message d'erreur
* note utilisateur (1–5) + commentaire
* référence aux fichiers d'entrée/sortie

### Opérations

* filtrer (provider, modèle, modalité, date, statut)
* rechercher dans les réponses
* relancer un test depuis l'historique
* dupliquer en modifiant les paramètres
* comparer plusieurs entrées côte à côte
* exporter en JSON ou CSV

---

## 13. Comparaison et multi-run

Mode **multi-run** : exécuter le même prompt/paramètres sur plusieurs modèles simultanément.

Comparaison sur :

* temps de réponse
* coût estimé
* résultat brut
* note utilisateur

Disponible pour texte, image, audio. Vidéo si les tâches sont asynchrones et que l'attente est gérée.

---

## 14. Notation

### Par modèle

Note globale (1–5), coût, vitesse, qualité, stabilité, commentaire libre.

### Par test

Note du résultat, qualité du rendu, conformité, commentaires.

### Par provider

Stabilité générale, qualité globale, qualité d'intégration, commentaires.

---

## 15. Tableau de bord

* nombre de providers configurés / actifs
* nombre de profils actifs
* nombre de modèles disponibles
* derniers tests exécutés
* derniers échecs
* latence moyenne par provider
* coût total estimé (session / global)
* modèles favoris

### Indicateur de santé par provider/profil

`OK` · `auth_invalide` · `endpoint_ko` · `timeout` · `non_testé`

Health check automatique au démarrage sur les providers actifs (ping léger, non bloquant).

---

## 16. Interface graphique (Tkinter)

Organisation :

* panneau latéral de navigation
* barre de statut (état courant, dernière opération)
* zone de logs techniques (filtrables, niveau configurable)
* formulaires clairs avec validation inline
* tableaux filtrables et triables
* dialogues modaux pour édition

Sections :

* **Dashboard**
* **Providers**
* **Credentials**
* **Models**
* **Test Lab**
* **History**
* **Compare**
* **Settings**

---

## 17. Interface CLI

Le mode CLI est conçu dès la conception, pas en ajout secondaire. Il partage la même couche métier que la GUI.

### Usages cibles

* humain en terminal
* scripts automatisés
* agent IA pilotant l'application par CLI

### Règles

* commandes stables, explicites, documentées
* `--help` sur toutes les commandes et sous-commandes
* `--output json|table|plain` sur toutes les commandes retournant des données (défaut : `table`)
* entrée/sortie non interactive possible (pas de prompt interactif obligatoire)
* exit codes cohérents :
  * `0` : succès
  * `1` : erreur métier (credential invalide, modèle introuvable…)
  * `2` : erreur réseau / timeout
  * `3` : erreur de configuration
  * `4` : entrée invalide

### Commandes

```
app providers list [--output json|table]
app providers add --name <n> --url <url> [--auth api_key]
app providers show <id>
app providers delete <id>

app credentials list [--provider <id>]
app credentials add --provider <id> --name <n> --api-key <key>
app credentials test <id>

app models list [--provider <id>] [--type text|image|audio|video]
app models sync --provider <id>
app models show <id>

app run text --model <id> --prompt <text> [--system <text>] [--temperature 0.7] [--output json]
app run image --model <id> --prompt <text> [--size 1024x1024]
app run audio --model <id> --file <path> --op transcription
app run video --model <id> --prompt <text> [--duration 5]

app history list [--provider <id>] [--model <id>] [--limit 20]
app history show <id>
app history export --format json|csv [--output <file>]

app config export [--output <file>]
app config import --file <path>

app health [--provider <id>]
```

---

## 18. Journal technique et debug

Panneau dédié (GUI) et flag `--debug` (CLI) affichant pour chaque appel :

* URL appelée
* méthode HTTP
* payload envoyé
* headers (secrets remplacés par `***`)
* code HTTP de réponse
* réponse brute
* durée d'exécution (ms)
* message d'erreur détaillé

---

## 19. Persistance

### SQLite

Tables principales :

* `providers`
* `credentials` (champs sensibles chiffrés)
* `models`
* `model_capabilities`
* `presets`
* `test_runs`
* `ratings`
* `prompt_templates`
* `async_tasks`

Migrations versionnées dès le départ (table `schema_version`).

### JSON

* préférences UI (`settings.json`)
* exports historique / configuration

---

## 20. Sécurité

* secrets chiffrés en base (AES-256 ou keyring OS)
* secrets jamais loggués (remplacés par `***`)
* secrets masqués par défaut dans l'interface
* aucune transmission involontaire de données
* aucune télémétrie

---

## 21. Fonctions complémentaires

### Bibliothèque de prompts

Table `prompt_templates` : titre, contenu, type (texte/image/audio), tags, catégorie. Prompts standards fournis par défaut (résumé, extraction JSON, traduction, classification, génération image, transcription).

### Mode sandbox / mock

Provider fictif inclus avec modèles simulés et réponses prédéfinies. Permet de tester l'interface sans clé API.

### Import / export de configuration

Export complet (providers + modèles, sans secrets) en JSON. Import avec résolution de conflits.

### Queue de tests

Préparation de plusieurs tests à lancer en séquence. Résultats collectés à la fin.

---

## 22. Tests et qualité

* tests unitaires sur les services et les adaptateurs providers (mockés)
* tests d'intégration sur la couche storage
* couverture minimale des cas d'erreur réseau et d'authentification
* CI-friendly : `python -m pytest` sans dépendance externe

---

## 23. Roadmap

### MVP

* gestion providers + credentials + modèles
* test texte fonctionnel (2+ providers)
* historique SQLite
* notation simple
* interface Tkinter de base
* CLI avec commandes core
* mode sandbox

### V2

* image et audio complets (tous providers supportés)
* OAuth2 enrichi avec refresh automatique
* multi-run et comparaison
* import/export config
* coûts estimés et suivi quota
* logs avancés

### V3

* gestion tâches asynchrones vidéo complète
* chiffrement local des secrets (si non fait en MVP)
* benchmark automatisé
* statistiques et dashboard enrichi
* système de plugins providers
* queue de tests avec scheduling

---

## 24. Livrables

1. arborescence du projet
2. code source complet
3. `requirements.txt`
4. `README.md` (installation, lancement GUI, lancement CLI)
5. documentation CLI avec exemples et sorties JSON attendues
6. documentation technique architecture
7. données d'exemple et provider mock
8. base de documentation pour intégration en Skill agent

---

## 25. Critères de réussite

* l'application se lance en GUI et en CLI
* plusieurs providers configurables
* plusieurs credentials par provider
* OAuth2 prévu proprement dans l'architecture
* tests texte lancables depuis GUI et CLI
* historique et notes sauvegardés
* CLI avec `--output json` fonctionnel sur les commandes principales
* architecture propre, extensible, testable
* limitations clairement documentées
