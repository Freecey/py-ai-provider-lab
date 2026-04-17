# AUDIT_R6 — Audit Round 6 (2026-04-17)

## Résumé exécutif

Audit de suivi post-R5. Revue des providers secondaires, CLI restant, UI views non couvertes, tests et seed.  
**Résultat : 3 bugs corrigés, 0 bloquant résiduel.**

---

## Fichiers audités

| Fichier | Statut | Notes |
|---------|--------|-------|
| `app/providers/openrouter.py` | ✅ | Hérite openai_compat, headers custom OK, normalize_capabilities correct |
| `app/providers/alibaba.py` | ✅ | Hérite openai_compat, DashScope base_url correct |
| `app/providers/zai.py` | ✅ | Stub OpenAI-compat, test_connection délègue correctement |
| `app/cli/models.py` | ✅ | print_error → sys.exit() donc print_output(None) jamais atteint |
| `app/cli/history.py` | ✅ | Même conclusion — print_error exit avant print_output |
| `app/cli/health.py` | ✅ | health_check_all résultats correctement itérés |
| `app/cli/config_cmd.py` | ✅ | import_config après print_error — sys.exit() protège contre data undefined |
| `app/cli/output.py` | ⚠️ → ✅ | `list \| None` annotation Python 3.10+ corrigée |
| `app/ui/views/credentials.py` | ⚠️ → ✅ | `int \| None` annotation dans `_on_save` corrigée |
| `app/ui/views/models.py` | ⚠️ → ✅ | `int \| None` annotation dans `_on_save` corrigée |
| `app/ui/views/compare.py` | ✅ | Stub correct, pas de logique |
| `app/ui/views/settings.py` | ✅ | `_save()` in-memory correct, `_apply_passphrase()` délègue correctement |
| `app/ui/views/dashboard.py` | ✅ | Exception silencieuse dans refresh() acceptable pour UI — inchangé depuis R4 |
| `app/ui/app_window.py` | ✅ | Queue + after(50) pattern correct, lazy view loading OK |
| `app/storage/seed.py` | ✅ | Guard `if existing and not force: return` OK, get_by_slug avant create évite doublons |
| `app/services/export_service.py` | ✅ | export_config sans secrets, import_config robuste avec try/except par item |
| `app/tests/test_storage.py` | ✅ | Fixtures in-memory correctes, couverture repos OK |
| `app/tests/test_providers.py` | ✅ | Mock HTTP via patch.object — robuste |
| `app/tests/test_cli.py` | ✅ | monkeypatch `_db` correct, seed neutralisé, coverage CLI OK |

---

## Bugs corrigés

### BUG #1 — app/ui/views/credentials.py:94 — `int | None` dans signature de méthode
**Severity:** Haute — TypeError à l'import du module en Python 3.9 → vue Credentials non chargeable

```python
# AVANT
def _on_save(self, data: dict, cred_id: int | None) -> None:

# APRÈS
def _on_save(self, data: dict, cred_id: "int | None") -> None:
```

**Cause:** L'opérateur `|` pour les unions de types (PEP 604) est Python 3.10+ uniquement. En Python 3.9, les annotations de paramètres de fonctions sont évaluées à la définition du `def` (au chargement de la classe). Sans `from __future__ import annotations`, `int | None` lève `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`.

Les annotations locales dans les corps de fonctions (`self._selected_id: int | None = None` dans `__init__`) ne sont **pas** évaluées et restent sûres — le bug ne concerne que les signatures de méthodes.

---

### BUG #2 — app/ui/views/models.py:109 — Même bug
**Severity:** Haute — TypeError à l'import → vue Models non chargeable

```python
# AVANT
def _on_save(self, data: dict, model_id: int | None) -> None:

# APRÈS
def _on_save(self, data: dict, model_id: "int | None") -> None:
```

---

### BUG #3 — app/cli/output.py:9 — `list | None` dans signature de fonction
**Severity:** Critique — `output.py` est importé par TOUS les modules CLI. TypeError à l'import → toutes les commandes CLI crashent au démarrage en Python 3.9

```python
# AVANT
def print_output(data: Any, output_format: str = "table",
                 columns: list | None = None, key: str = "id") -> None:

# APRÈS
def print_output(data: Any, output_format: str = "table",
                 columns: "list | None" = None, key: str = "id") -> None:
```

**Cause:** Même root cause que BUG #1/#2. Puisque `output.py` est importé par `providers.py`, `credentials.py`, `models.py`, `history.py`, `run.py` (tous les modules CLI), ce bug rendait l'intégralité du CLI non fonctionnel en Python 3.9.

---

## Analyse : annotations Python 3.9 — récapitulatif complet

| Syntaxe | Python 3.9 OK | Contexte |
|---------|--------------|---------|
| `list[str]` (PEP 585) | ✅ | Paramètre, retour, variable locale |
| `dict[str, int]` (PEP 585) | ✅ | Idem |
| `int \| None` (PEP 604) | ❌ runtime | Paramètre ou retour de fonction |
| `int \| None` (PEP 604) | ✅ si string `"int \| None"` | Toujours |
| `int \| None` dans corps `__init__` | ✅ | Variable locale — non évaluée |
| `Optional[int]` (typing) | ✅ | Tous contextes |

**Corrections appliquées (cumulatif R4–R6) :**
- R4 : `app/providers/base.py` — `VideoResult | AsyncTaskRef` dans retour
- R6 : `app/ui/views/credentials.py`, `app/ui/views/models.py` — `int | None` dans paramètre
- R6 : `app/cli/output.py` — `list | None` dans paramètre

---

## Vérifications non-bugs

### `app/cli/models.py` et `app/cli/history.py` — pattern `print_error` sans `return`
```python
if not m:
    print_error(f"Modèle {args.id} introuvable", 1)
print_output(m, fmt)  # Jamais atteint si m is None
```
**Statut :** ✅ Non-bug. `print_error` appelle `sys.exit()` qui lève `SystemExit(BaseException)` — non capturé par `except Exception`. `print_output(None, ...)` n'est jamais exécuté.

### `app/cli/config_cmd.py` — `import_config` après `print_error` dans except
```python
except Exception as e:
    print_error(f"...", 3)  # sys.exit(3) — data jamais utilisé si undefined
result = svc.import_config(data)
```
**Statut :** ✅ Non-bug. `sys.exit(3)` empêche l'accès à `data` non défini.

### `app/storage/seed.py` — mock models sans guard de déduplication
**Statut :** ✅ Acceptable. La garde `if existing and not force: return` évite la réexécution normale. `force=True` est une opération explicite de réinitialisation.

---

## Audit sécurité (inchangé depuis R4)

| Aspect | Statut |
|--------|--------|
| Masquage secrets (logs) | ✅ |
| Encryption credentials | ✅ AES-256-GCM |
| SQL injection | ✅ Parameterized queries |
| Streaming — secret exposure | ✅ Headers masqués même en stream=True |

---

## Checklist post-R6

| Composant | Statut |
|-----------|--------|
| Providers base/mock/openai/anthropic/openai_compat | ✅ |
| Providers minimax/openrouter/alibaba/zai | ✅ |
| Services test/model/credential/provider/history/export | ✅ |
| CLI run/models/history/health/config (streaming + non-streaming) | ✅ |
| UI app_window/dashboard/testlab/history/providers | ✅ |
| UI credentials/models/settings/compare | ✅ |
| Storage repos/db/crypto/seed | ✅ |
| Tests storage/providers/services/cli | ✅ |
| Models/dataclasses | ✅ |

---

## Résumé des bugs R1–R6

| Round | Bugs | Severity max | Statut |
|-------|------|-------------|--------|
| R1 | 10 | Haute (cli init) | ✅ Tous corrigés |
| R2 | 5 | Critique (package shadowing) | ✅ Tous corrigés |
| R3 | 2 | Moyenne (None-safety) | ✅ Tous corrigés |
| R4 | 4 | Haute UI (simpledialog + streaming flag) | ✅ Tous corrigés |
| R5 | 2 | Haute (CLI streaming thread + KeyError) | ✅ Tous corrigés |
| R6 | 3 | Critique (Python 3.9 annotations CLI + UI) | ✅ Tous corrigés |

**Total cumulé : 26 bugs détectés et corrigés sur 6 rounds d'audit.**

---

**Audit effectué :** 2026-04-17  
**Fichiers vérifiés :** 19  
**Bugs trouvés :** 3 (tous corrigés)  
**Inconsistances :** 0
