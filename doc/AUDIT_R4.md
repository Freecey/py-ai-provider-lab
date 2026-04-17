# AUDIT_R4 — Audit Round 4 (2026-04-17)

## Résumé exécutif

Audit de suivi post-R3. Vérification approfondie des providers, services, tests et UI.  
**Résultat : 4 bugs corrigés, 2 inconsistances documentées, aucun bloquant.**

---

## Fichiers audités

| Fichier | Statut | Notes |
|---------|--------|-------|
| `app/providers/base.py` | ⚠️ → ✅ | Type hint Python 3.10+ corrigé |
| `app/providers/openai_compat.py` | ⚠️ → ✅ | Streaming flag incohérent corrigé |
| `app/providers/anthropic.py` | ⚠️ → ✅ | Même fix streaming |
| `app/providers/openai.py` | ✅ | Capabilities dupliquées nettoyées par `set()` — OK |
| `app/providers/minimax.py` | ✅ | Exception chaining correct (R2), list_models fallback OK |
| `app/providers/zai.py` | ✅ | Stub OpenAI-compat correct |
| `app/providers/__init__.py` | ✅ | Auto-register avec logger.warning sur ImportError |
| `app/services/test_service.py` | ⚠️ → ✅ | Proxy manquant dans poll_async_task corrigé |
| `app/ui/views/testlab.py` | ⚠️ → ✅ | `tk.simpledialog.askstring` → `simpledialog.askstring` |
| `app/ui/views/dashboard.py` | ✅ | Exception silencieuse dans refresh() acceptable pour UI |
| `app/ui/app_window.py` | ✅ | Queue + after(50) pattern correct |
| `app/storage/seed.py` | ℹ️ | Anthropic base_url a suffix /v1 (inconsistant avec adapter) |
| `app/tests/test_storage.py` | ✅ | Fixtures correctes, double connect() sans effet |
| `app/tests/test_providers.py` | ✅ | Mock HTTP via patch.object — robuste |

---

## Bugs corrigés

### BUG #1 — app/services/test_service.py:190 — Proxy absent dans poll_async_task
**Severity:** Basse — même pattern que model_service.py (corrigé R3)

```python
# AVANT
adapter = cls(timeout=provider.timeout_global)

# APRÈS
adapter = cls(timeout=provider.timeout_global, proxy=provider.proxy or None)
```

**Cause:** `poll_async_task()` avait la même omission que `sync_models()`. Cohérence avec tous les autres points d'instanciation d'adapter.

---

### BUG #2 — app/providers/openai_compat.py:65 — stream=True envoyé sans handler
**Severity:** Moyenne — provoque un crash `resp.json()` sur une réponse streaming

```python
# AVANT
stream = bool(on_chunk) or params.get("streaming", False)
payload["stream"] = stream
# Problème : si streaming=True en params mais on_chunk=None →
#   payload["stream"] = True mais code path non-streaming → resp.json() échoue

# APRÈS
stream = bool(on_chunk)
payload["stream"] = stream
# Streaming activé uniquement si callback fourni
```

**Cause:** Confusion entre le flag UI "l'utilisateur veut du streaming" et la présence réelle d'un handler. Sans `on_chunk`, envoyer `"stream": true` à l'API retourne un flux SSE que `resp.json()` ne peut pas parser.

---

### BUG #3 — app/providers/anthropic.py:83 — Même bug streaming
**Severity:** Moyenne — même cause, même fix

```python
# AVANT
stream = bool(on_chunk) or params.get("streaming", False)

# APRÈS
stream = bool(on_chunk)
```

---

### BUG #4 — app/ui/views/testlab.py:216 — Mauvais accès à simpledialog
**Severity:** Haute UI — crash silencieux, nom preset jamais demandé

```python
# AVANT
name = tk.simpledialog.askstring(...) if hasattr(tk, "simpledialog") else "Preset"
# Problème : tk = import tkinter, simpledialog est déjà importé séparément ligne 3
# hasattr(tk, "simpledialog") peut retourner False → fallback "Preset" utilisé toujours

# APRÈS
name = simpledialog.askstring("Preset", "Nom du preset :", parent=self)
# simpledialog est importé en ligne 3 : from tkinter import ..., simpledialog
```

**Cause:** La correction R1 a ajouté `simpledialog` aux imports mais l'appel utilisait encore `tk.simpledialog` avec un guard `hasattr` qui court-circuitait silencieusement.

---

## Inconsistances documentées (non bloquants)

### Inconsistance #1 — app/providers/base.py:37 — Type hint Python 3.10+
**Status:** Corrigé en R4

```python
# AVANT (Python 3.10+ uniquement)
def run_video(...) -> VideoResult | AsyncTaskRef:

# APRÈS (Python 3.9+ compatible)
def run_video(...) -> "VideoResult | AsyncTaskRef":
```

### Inconsistance #2 — app/storage/seed.py:21 — base_url Anthropic
**Status:** Documenté, non bloquant

```python
# Seed data
Provider(name="Anthropic", base_url="https://api.anthropic.com/v1", ...)

# Adapter anthropic.py
_ANTHROPIC_BASE = "https://api.anthropic.com"  # Pas de /v1 (ajouté par l'adapter)
```

**Impact:** Le champ `base_url` dans la table providers est purement informatif — l'adapter hardcode sa propre base URL. Pas d'impact fonctionnel.

---

## Analyse du pattern streaming (R4)

Le bug #2/#3 révèle un design issue dans la gestion du streaming :

| Cas | on_chunk | params["streaming"] | payload["stream"] R3 | payload["stream"] R4 |
|-----|----------|---------------------|----------------------|----------------------|
| CLI sans stream | None | False | False ✅ | False ✅ |
| CLI sans stream mais flag set | None | True | **True ❌** | False ✅ |
| GUI stream | Callable | True | True ✅ | True ✅ |
| GUI stream sans flag | Callable | False | False ❌ | True ✅ |

**Résultat R4 :** Le seul signal fiable pour activer le streaming est la présence du callback `on_chunk`. Le flag `params["streaming"]` était ambigu et pouvait envoyer des réponses SSE non parsables.

---

## Audit sécurité (inchangé depuis R3)

| Aspect | Statut |
|--------|--------|
| Masquage secrets (logs) | ✅ |
| Encryption credentials | ✅ AES-256-GCM |
| SQL injection | ✅ Parameterized queries |
| Streaming — secret exposure | ✅ Headers masqués même en stream=True |

---

## Checklist post-R4

| Phase | Statut |
|-------|--------|
| Providers base/mock/openai/anthropic | ✅ |
| Providers minimax/openrouter/alibaba/zai | ✅ |
| Services test/model/credential/provider/history | ✅ |
| CLI providers/credentials/models/run/history | ✅ |
| UI app_window/dashboard/testlab/history | ✅ |
| Tests storage/providers/services/cli | ✅ |

---

## Résumé des bugs R1–R4

| Round | Bugs | Severity max | Statut |
|-------|------|-------------|--------|
| R1 | 10 | Haute (cli init) | ✅ Tous corrigés |
| R2 | 5 | Critique (package shadowing) | ✅ Tous corrigés |
| R3 | 2 | Moyenne (None-safety) | ✅ Tous corrigés |
| R4 | 4 | Haute UI (simpledialog + streaming) | ✅ Tous corrigés |

**Total : 21 bugs détectés et corrigés sur 4 rounds d'audit.**

---

## Recommandations finales

### Avant merge/release
Aucune action bloquante. Tous les bugs identifiés sont corrigés.

### Phase 11+ (future)
1. Ajouter `params.get("streaming", False)` comme hint UI uniquement (ne pas l'envoyer à l'API)
2. Exposer `streaming` comme paramètre optionnel dans `run_text()` signature plutôt que dans `params` dict
3. CompareView implémentation complète
4. OAuth2 refresh token par provider

---

**Audit effectué :** 2026-04-17  
**Fichiers vérifiés :** 14  
**Bugs trouvés :** 4 (tous corrigés)  
**Inconsistances :** 2 (documentées)
