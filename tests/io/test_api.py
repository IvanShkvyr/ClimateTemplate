import asyncio
import logging

import aiohttp

from clim4cast_imagegen.io.api import upload_single_file


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
