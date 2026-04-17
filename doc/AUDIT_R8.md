# AUDIT_R8 — Audit Round 8 (2026-04-17)

## Résumé exécutif

Audit de clôture — derniers fichiers non couverts par R1–R7 : widgets UI, modèles de données
complets (async_task, results), constants, et schéma SQL.  
**Résultat : 0 bug. Codebase entièrement audité.**

---

## Fichiers audités

| Fichier | Statut | Notes |
|---------|--------|-------|
| `app/ui/widgets/__init__.py` | ✅ | Re-exports simples — OK |
| `app/ui/widgets/filterable_table.py` | ✅ | `Optional[Callable]` via typing, `list[str]` PEP 585 seul (sans `\|`) — OK |
| `app/ui/widgets/secret_field.py` | ✅ | Aucune annotation `\|` — OK |
| `app/ui/widgets/status_badge.py` | ✅ | Aucune annotation — OK |
| `app/ui/widgets/progress_dialog.py` | ✅ | `Optional[Callable]` via typing — OK |
| `app/ui/widgets/confirm_dialog.py` | ✅ | Aucune annotation `\|` — OK |
| `app/models/credential.py` | ✅ | `Optional[...]` via typing — OK |
| `app/models/model.py` | ✅ | `Optional[...]` via typing, `list`/`dict` non subscriptés — OK |
| `app/models/preset.py` | ✅ | `Optional[...]` via typing — OK |
| `app/models/test_run.py` | ✅ | `Optional[...]` via typing — OK |
| `app/models/async_task.py` | ✅ | `Optional[...]` via typing — OK |
| `app/models/prompt_template.py` | ✅ | `Optional[...]` via typing — OK |
| `app/models/results.py` | ✅ | `Optional[...]` via typing pour tous les résultats — OK |
| `app/config/constants.py` | ✅ | Constantes pures, aucune annotation — OK |
| `app/storage/migrations/001_initial.sql` | ✅ | Toutes les tables correspondent exactement aux dataclasses |

---

## Bugs corrigés

Aucun.

---

## Vérifications non-bugs

### `app/ui/widgets/filterable_table.py` — `list[str]` dans paramètre
```python
def __init__(self, parent, columns: list[str], ...):
```
**Statut :** ✅ Correct. `list[str]` seul (PEP 585) est valide en Python 3.9. Seule la combinaison
`list[str] | None` (PEP 585 + PEP 604) échoue. Pas de `|` ici — sûr.

### `app/ui/widgets/filterable_table.py` — `iid` basé sur `id(row)` pour les lignes sans clé `id`
```python
self._tree.insert("", "end", iid=str(row.get("id", id(row))), values=values)
```
**Statut :** ✅ Correct. Fallback sur l'adresse mémoire de l'objet si pas de clé `id`. Acceptable
pour des tables sans identifiant explicite — les sélections fonctionnent car `_handle_select`
retrouve la ligne par `iid`.

### `app/models/results.py` — `SyncResult` et `HealthStatus` absents du PLAN_V1
**Statut :** ✅ Ajouts légitimes apparus pendant le développement (résultat de sync_models,
statut de health_check_all). Pas d'incohérence avec le schéma SQL (ces types ne sont pas persistés
directement).

### `app/storage/migrations/001_initial.sql` — cohérence schéma/dataclasses
Vérification champ par champ :

| Table SQL | Dataclass | Champs manquants | Champs supplémentaires |
|-----------|-----------|-----------------|----------------------|
| `providers` | `Provider` | — | — |
| `credentials` | `Credential` | — | — |
| `models` | `Model` | `capabilities` (chargé via jointure) | — |
| `model_capabilities` | `ModelCapability` | — | — |
| `presets` | `Preset` | — | — |
| `test_runs` | `TestRun` | — | — |
| `async_tasks` | `AsyncTask` | — | — |
| `prompt_templates` | `PromptTemplate` | — | — |

**Statut :** ✅ Cohérence totale. Le champ `capabilities` de `Model` est intentionnellement absent
de la table `models` — il est peuplé par jointure avec `model_capabilities`.

---

## Audit sécurité (inchangé depuis R4)

| Aspect | Statut |
|--------|--------|
| Masquage secrets (logs) | ✅ |
| Encryption credentials | ✅ AES-256-GCM |
| SQL injection | ✅ Parameterized queries |
| Streaming — secret exposure | ✅ Headers masqués même en stream=True |

---

## Checklist finale — codebase 100% audité

| Composant | Rounds | Statut |
|-----------|--------|--------|
| Providers (9 adapters) | R2, R7 | ✅ |
| Services (6 services) | R3, R5, R7 | ✅ |
| CLI (entry + 7 sous-commandes + output) | R1, R2, R5, R6, R7 | ✅ |
| UI — app_window + 8 vues | R1, R4, R6, R7 | ✅ |
| UI — widgets (5 widgets) | **R8** | ✅ |
| Storage — db + seed + 8 repos | R1, R6, R7 | ✅ |
| Storage — migrations SQL | **R8** | ✅ |
| Models — 7 dataclasses + results | R7, **R8** | ✅ |
| Config (settings + constants) | R7, **R8** | ✅ |
| Utils (logger + crypto + http_client + formatters) | R2, R3, R7 | ✅ |
| Tests (4 suites) | R6 | ✅ |

---

## Résumé des bugs R1–R8

| Round | Bugs | Severity max | Statut |
|-------|------|-------------|--------|
| R1 | 10 | Haute (CLI init) | ✅ Tous corrigés |
| R2 | 5 | Critique (package shadowing) | ✅ Tous corrigés |
| R3 | 2 | Moyenne (None-safety) | ✅ Tous corrigés |
| R4 | 4 | Haute UI (simpledialog + streaming) | ✅ Tous corrigés |
| R5 | 2 | Haute (CLI streaming thread + KeyError) | ✅ Tous corrigés |
| R6 | 3 | Critique (Python 3.9 annotations — UI + CLI output) | ✅ Tous corrigés |
| R7 | 3 | Critique (Python 3.9 annotations — formatters + cli + settings) | ✅ Tous corrigés |
| R8 | 0 | — | ✅ Aucun bug |

**Total cumulé : 29 bugs détectés et corrigés sur 8 rounds d'audit.**  
**Audit complet — 0 fichier restant.**

---

**Audit effectué :** 2026-04-17  
**Fichiers vérifiés :** 15  
**Bugs trouvés :** 0  
**Inconsistances :** 0
