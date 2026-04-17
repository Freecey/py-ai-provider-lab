import csv
import io
import json
from typing import Any

from app.models.test_run import TestRun
from app.utils.logger import get_logger

logger = get_logger("service.export")


class ExportService:
    def export_history(self, runs: list[TestRun], format: str = "json") -> str:
        if format == "json":
            return json.dumps([self._run_to_dict(r) for r in runs], ensure_ascii=False, indent=2, default=str)
        elif format == "csv":
            return self._runs_to_csv(runs)
        raise ValueError(f"Unsupported format: {format}")

    def export_config(self, include_providers: bool = True,
                      include_models: bool = True) -> dict:
        from app.storage.repositories.provider_repo import ProviderRepository
        from app.storage.repositories.model_repo import ModelRepository
        from app.storage.db import get_conn
        conn = get_conn()
        result: dict[str, Any] = {}
        if include_providers:
            repo = ProviderRepository(conn)
            result["providers"] = [
                {k: v for k, v in p.__dict__.items() if k != "id"}
                for p in repo.list()
            ]
        if include_models:
            repo = ModelRepository(conn)
            result["models"] = [
                {k: v for k, v in m.__dict__.items() if k not in ("id", "capabilities")}
                for m in repo.list(active_only=False)
            ]
        return result

    def import_config(self, data: dict) -> dict:
        from app.storage.repositories.provider_repo import ProviderRepository
        from app.storage.repositories.model_repo import ModelRepository
        from app.storage.db import get_conn
        from app.models.provider import Provider
        from app.models.model import Model
        conn = get_conn()
        result = {"providers_added": 0, "models_added": 0, "errors": []}
        p_repo = ProviderRepository(conn)
        m_repo = ModelRepository(conn)
        for p_data in data.get("providers", []):
            try:
                p = Provider(**{k: v for k, v in p_data.items() if hasattr(Provider, k)})
                p_repo.create(p)
                result["providers_added"] += 1
            except Exception as e:
                result["errors"].append(str(e))
        for m_data in data.get("models", []):
            try:
                m = Model(**{k: v for k, v in m_data.items() if hasattr(Model, k)})
                m_repo.create(m)
                result["models_added"] += 1
            except Exception as e:
                result["errors"].append(str(e))
        return result

    def _run_to_dict(self, run: TestRun) -> dict:
        return {
            "id": run.id, "provider_id": run.provider_id,
            "credential_id": run.credential_id, "model_id": run.model_id,
            "modality": run.modality, "params": run.params,
            "response_raw": run.response_raw, "latency_ms": run.latency_ms,
            "cost_estimated": run.cost_estimated, "status": run.status,
            "error_message": run.error_message, "rating": run.rating,
            "rating_notes": run.rating_notes,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }

    def _runs_to_csv(self, runs: list[TestRun]) -> str:
        output = io.StringIO()
        if not runs:
            return ""
        fieldnames = list(self._run_to_dict(runs[0]).keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in runs:
            row = self._run_to_dict(r)
            row["params"] = json.dumps(row["params"])
            writer.writerow(row)
        return output.getvalue()
