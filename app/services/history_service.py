from typing import Optional

from app.models.test_run import TestRun
from app.storage.db import get_conn
from app.storage.repositories.test_run_repo import TestRunRepository
from app.utils.logger import get_logger

logger = get_logger("service.history")


class HistoryService:
    def __init__(self):
        self._repo = TestRunRepository(get_conn())

    def list_runs(self, provider_id: Optional[int] = None, model_id: Optional[int] = None,
                  status: Optional[str] = None, modality: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> list[TestRun]:
        return self._repo.list(provider_id=provider_id, model_id=model_id,
                               status=status, modality=modality, limit=limit, offset=offset)

    def get_run(self, id: int) -> Optional[TestRun]:
        return self._repo.get_by_id(id)

    def rate_run(self, id: int, rating: int, notes: str = "") -> Optional[TestRun]:
        run = self._repo.get_by_id(id)
        if not run:
            return None
        run.rating = max(1, min(5, rating))
        run.rating_notes = notes
        return self._repo.update(run)

    def delete_run(self, id: int) -> bool:
        return self._repo.delete(id)

    def replay_run(self, id: int) -> Optional[TestRun]:
        original = self._repo.get_by_id(id)
        if not original:
            return None
        from app.services.test_service import TestService
        svc = TestService()
        if original.modality == "text":
            return svc.run_text(original.credential_id, original.model_id, original.params)
        elif original.modality == "image":
            return svc.run_image(original.credential_id, original.model_id, original.params)
        elif original.modality == "audio":
            return svc.run_audio(original.credential_id, original.model_id, original.params)
        elif original.modality == "video":
            return svc.run_video(original.credential_id, original.model_id, original.params)
        return None

    def export_runs(self, filters: dict, format: str = "json") -> str:
        from app.services.export_service import ExportService
        runs = self.list_runs(**{k: v for k, v in filters.items()
                                 if k in ("provider_id", "model_id", "status", "modality", "limit")})
        return ExportService().export_history(runs, format)
