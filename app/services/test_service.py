import threading
import time
from datetime import datetime
from typing import Callable, Optional

from app.models.test_run import TestRun
from app.models.async_task import AsyncTask
from app.models.results import AsyncTaskRef, TaskStatus
from app.storage.db import get_conn
from app.storage.repositories.test_run_repo import TestRunRepository
from app.storage.repositories.async_task_repo import AsyncTaskRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.model_repo import ModelRepository
from app.storage.repositories.provider_repo import ProviderRepository
from app.providers import get_provider_class
from app.utils.logger import get_logger

logger = get_logger("service.test")


class TestService:
    def __init__(self):
        conn = get_conn()
        self._run_repo = TestRunRepository(conn)
        self._task_repo = AsyncTaskRepository(conn)
        self._cred_repo = CredentialRepository(conn)
        self._model_repo = ModelRepository(conn)
        self._prov_repo = ProviderRepository(conn)

    def _resolve(self, credential_id: int, model_id: int):
        cred = self._cred_repo.get_by_id(credential_id)
        model = self._model_repo.get_by_id(model_id)
        if not cred or not model:
            raise ValueError("Credential or model not found")
        provider = self._prov_repo.get_by_id(model.provider_id)
        if not provider:
            raise ValueError("Provider not found for model")
        cls = get_provider_class(provider.slug)
        if not cls:
            raise ValueError(f"No adapter registered for '{provider.slug}'")
        adapter = cls(timeout=provider.timeout_global, proxy=provider.proxy or None)
        return cred, model, provider, adapter

    def _create_run(self, credential_id, model_id, provider_id, modality, params) -> TestRun:
        run = TestRun(
            credential_id=credential_id, model_id=model_id,
            provider_id=provider_id, modality=modality,
            params=params, status="pending",
        )
        return self._run_repo.create(run)

    def _finalise_run(self, run: TestRun, result, start: float) -> TestRun:
        import json as _json
        run.latency_ms = int((time.monotonic() - start) * 1000)
        run.status = "success" if result.success else "error"
        run.error_message = getattr(result, "error", "")
        if hasattr(result, "content") and result.content:
            run.response_raw = result.content
        elif hasattr(result, "raw_response") and result.raw_response:
            run.response_raw = _json.dumps(result.raw_response, default=str)
        if hasattr(result, "cost_estimated"):
            run.cost_estimated = result.cost_estimated
        return self._run_repo.update(run)

    def run_text(self, credential_id: int, model_id: int, params: dict,
                 on_chunk: Optional[Callable] = None, callback: Optional[Callable] = None) -> TestRun:
        cred, model, provider, adapter = self._resolve(credential_id, model_id)
        run = self._create_run(credential_id, model_id, provider.id, "text", params)
        start = time.monotonic()

        def _execute():
            try:
                result = adapter.run_text(cred, model.technical_name, params, on_chunk=on_chunk)
                self._finalise_run(run, result, start)
                if callback:
                    callback(run, result)
            except Exception as e:
                run.status = "error"
                run.error_message = str(e)
                run.latency_ms = int((time.monotonic() - start) * 1000)
                self._run_repo.update(run)
                if callback:
                    callback(run, None)

        if callback:
            threading.Thread(target=_execute, daemon=True).start()
            return run
        _execute()
        return run

    def run_image(self, credential_id: int, model_id: int, params: dict,
                  callback: Optional[Callable] = None) -> TestRun:
        cred, model, provider, adapter = self._resolve(credential_id, model_id)
        run = self._create_run(credential_id, model_id, provider.id, "image", params)
        start = time.monotonic()

        def _execute():
            try:
                result = adapter.run_image(cred, model.technical_name, params)
                self._finalise_run(run, result, start)
                if callback:
                    callback(run, result)
            except Exception as e:
                run.status = "error"; run.error_message = str(e)
                run.latency_ms = int((time.monotonic() - start) * 1000)
                self._run_repo.update(run)
                if callback:
                    callback(run, None)

        if callback:
            threading.Thread(target=_execute, daemon=True).start()
            return run
        _execute()
        return run

    def run_audio(self, credential_id: int, model_id: int, params: dict,
                  file_path: Optional[str] = None, callback: Optional[Callable] = None) -> TestRun:
        cred, model, provider, adapter = self._resolve(credential_id, model_id)
        run = self._create_run(credential_id, model_id, provider.id, "audio", params)
        start = time.monotonic()

        def _execute():
            try:
                result = adapter.run_audio(cred, model.technical_name, params, file_path=file_path)
                self._finalise_run(run, result, start)
                if callback:
                    callback(run, result)
            except Exception as e:
                run.status = "error"; run.error_message = str(e)
                run.latency_ms = int((time.monotonic() - start) * 1000)
                self._run_repo.update(run)
                if callback:
                    callback(run, None)

        if callback:
            threading.Thread(target=_execute, daemon=True).start()
            return run
        _execute()
        return run

    def run_video(self, credential_id: int, model_id: int, params: dict,
                  callback: Optional[Callable] = None) -> "TestRun | AsyncTaskRef":
        cred, model, provider, adapter = self._resolve(credential_id, model_id)
        run = self._create_run(credential_id, model_id, provider.id, "video", params)
        start = time.monotonic()

        def _execute():
            try:
                result = adapter.run_video(cred, model.technical_name, params)
                if isinstance(result, AsyncTaskRef):
                    task = AsyncTask(
                        test_run_id=run.id,
                        provider_task_id=result.provider_task_id,
                        poll_interval_s=result.poll_interval_s,
                        timeout_s=result.timeout_s,
                        status="pending",
                    )
                    self._task_repo.create(task)
                    run.status = "pending"; self._run_repo.update(run)
                    if callback:
                        callback(run, result)
                else:
                    self._finalise_run(run, result, start)
                    if callback:
                        callback(run, result)
            except Exception as e:
                run.status = "error"; run.error_message = str(e)
                run.latency_ms = int((time.monotonic() - start) * 1000)
                self._run_repo.update(run)
                if callback:
                    callback(run, None)

        if callback:
            threading.Thread(target=_execute, daemon=True).start()
            return run
        _execute()
        return run

    def poll_async_task(self, task_id: int) -> TaskStatus:
        task = self._task_repo.get_by_id(task_id)
        if not task:
            return TaskStatus(status="failed", error="Task not found")
        run = self._run_repo.get_by_id(task.test_run_id)
        if not run:
            return TaskStatus(status="failed", error="TestRun not found")
        cred = self._cred_repo.get_by_id(run.credential_id)
        model = self._model_repo.get_by_id(run.model_id)
        provider = self._prov_repo.get_by_id(run.provider_id)
        cls = get_provider_class(provider.slug)
        adapter = cls(timeout=provider.timeout_global, proxy=provider.proxy or None)
        task_ref = AsyncTaskRef(provider_task_id=task.provider_task_id,
                                poll_interval_s=task.poll_interval_s)
        status = adapter.poll_task(cred, task_ref)
        task.status = status.status
        task.last_polled_at = datetime.now()
        if status.result:
            import json
            task.result = {"video_file": status.result.video_file}
            run.status = "success"
            run.response_raw = json.dumps(task.result)
            self._run_repo.update(run)
        self._task_repo.update(task)
        return status

    def cancel_async_task(self, task_id: int) -> bool:
        task = self._task_repo.get_by_id(task_id)
        if not task:
            return False
        task.status = "failed"; task.error = "Cancelled by user"
        self._task_repo.update(task)
        run = self._run_repo.get_by_id(task.test_run_id)
        if run:
            run.status = "cancelled"; self._run_repo.update(run)
        return True

    def run_multi(self, credential_model_pairs: list[tuple], modality: str,
                  params: dict, callback: Optional[Callable] = None) -> list[TestRun]:
        runs = []
        for cred_id, model_id in credential_model_pairs:
            if modality == "text":
                run = self.run_text(cred_id, model_id, params, callback=callback)
            elif modality == "image":
                run = self.run_image(cred_id, model_id, params, callback=callback)
            elif modality == "audio":
                run = self.run_audio(cred_id, model_id, params, callback=callback)
            else:
                run = self.run_video(cred_id, model_id, params, callback=callback)
            runs.append(run)
        return runs
