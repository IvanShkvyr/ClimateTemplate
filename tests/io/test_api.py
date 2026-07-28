import asyncio
import logging

import aiohttp
import pytest

from clim4cast_imagegen.io import api
from clim4cast_imagegen.io.api import (
    upload_single_file,
    upload_files_to_api_async,
    upload_results_async,
    UploadReport
    )
from clim4cast_imagegen.core.exceptions import UploadIncompleteError

class FakeResp:
    def __init__(self, outcome):
        self.outcome = outcome

    async def __aenter__(self):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        self.status = self.outcome
        return self

    async def __aexit__(self, *args):
        return False

    async def text(self):
        return "error body"


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def post(self, url, data=None):
        outcomes = self.outcomes[self.calls]
        self.calls += 1
        return FakeResp(outcomes)


async def _run(session, file_path, root_path, max_attempts=3, base_delay=0.0):
    return await upload_single_file(
        session=session,
        file_path=file_path,
        root_path=root_path,
        base_url="http://x",
        logger=logging.getLogger("test"),
        semaphore=asyncio.Semaphore(1),
        max_attempts=max_attempts,
        base_delay=base_delay,
    )


def test_upload_success_first_try(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    session = FakeSession([200])
    assert asyncio.run(_run(session, f, tmp_path)) is True
    assert session.calls == 1


def test_upload_retries_transient_then_succeeds(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    session = FakeSession([aiohttp.ClientError(), 500, 200])
    assert asyncio.run(_run(session, f, tmp_path)) is True
    assert session.calls == 3


def test_upload_paermanent_4xx_no_retry(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    session = FakeSession([404])
    assert asyncio.run(_run(session, f, tmp_path)) is False
    assert session.calls == 1


def test_upload_exhausts_attempts(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    session = FakeSession([500, 500, 500])
    assert asyncio.run(_run(session, f, tmp_path)) is False
    assert session.calls == 3


def test_upload_unexpected_error_no_retry(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    session = FakeSession([ValueError("boom")])
    assert asyncio.run(_run(session, f, tmp_path)) is False
    assert session.calls == 1    


def test_missing_root_folder_returns_empty_report(tmp_path):
    missing = tmp_path / "no_such_dir"
    report = asyncio.run(upload_files_to_api_async(
        base_url="http://x", username="u", password="p",
        root_folder=str(missing), logger=logging.getLogger("test"),
    ))
    assert report.uploaded == []
    assert report.failed == []
    assert report.total == 0


def test_report_counts_uploaded_and_failed(tmp_path, monkeypatch):
    for name in ("ok1.png", "ok2.png", "bad.png"):
        (tmp_path / name).write_bytes(b"x")

    async def fake_upload(*, file_path, **kwargs):
        return file_path.name != "bad.png"

    monkeypatch.setattr(api, "upload_single_file", fake_upload)

    report = asyncio.run(upload_files_to_api_async(
        base_url="http://x", username="u", password="p",
        root_folder=str(tmp_path), logger=logging.getLogger("test"),
    ))
    assert report.total == 3
    assert len(report.uploaded) == 2
    assert [p.name for p in report.failed] == ["bad.png"]


def _fake_config():
    from types import SimpleNamespace
    return SimpleNamespace(
        api=SimpleNamespace(base_url="http://x", username="u", password="p"),
        folders=SimpleNamespace(to_send="ignored"),
    )


def test_results_async_raises_when_some_failed(monkeypatch):
    async def fake_files(**kwargs):
        return UploadReport(uploaded=["a"], failed=["b"])
    monkeypatch.setattr(api, "upload_files_to_api_async", fake_files)

    with pytest.raises(UploadIncompleteError):
        asyncio.run(upload_results_async(_fake_config(), logging.getLogger("test")))


def test_results_async_silent_when_all_uploaded(monkeypatch):
    async def fake_files(**kwargs):
        return UploadReport(uploaded=["a", "b"], failed=[])
    monkeypatch.setattr(api, "upload_files_to_api_async", fake_files)

    asyncio.run(upload_results_async(_fake_config(), logging.getLogger("test")))
