import asyncio
from types import SimpleNamespace

from clim4cast_imagegen import cli


def test_main_skips_when_already_processed(monkeypatch):
    called = []
    monkeypatch.setattr(cli, "load_app_config", lambda: SimpleNamespace(dry_run=True))
    monkeypatch.setattr(cli, "is_already_processed", lambda today: True)
    monkeypatch.setattr(cli, "find_input_data", lambda *a, **k: called.append("find_data"))
    monkeypatch.setattr(cli, "prepare_environment", lambda *a, **k: called.append("prepare"))

    asyncio.run(cli.main())

    assert called == []


def test_main_exits_when_data_not_ready(monkeypatch):
    called = []
    monkeypatch.setattr(cli, "load_app_config", lambda: SimpleNamespace(dry_run=True))
    monkeypatch.setattr(cli, "is_already_processed", lambda today: False)
    monkeypatch.setattr(cli, "find_input_data", lambda *a, **k: None)
    monkeypatch.setattr(cli, "prepare_environment", lambda *a, **k: called.append("prepare"))

    asyncio.run(cli.main())

    assert called == []


def test_marker_not_written_in_dry_run(monkeypatch):
    called = []
    monkeypatch.setattr(cli, "load_app_config", lambda: SimpleNamespace(dry_run=True))
    monkeypatch.setattr(cli, "is_already_processed", lambda today: False)
    monkeypatch.setattr(cli, "find_input_data", lambda *a, **k: "fake/path")
    monkeypatch.setattr(cli, "prepare_environment", lambda *a, **k: None)
    monkeypatch.setattr(cli, "generate_base_raster", lambda *a, **k: [])
    monkeypatch.setattr(cli, "generate_visualizations", lambda *a, **k: {})
    monkeypatch.setattr(cli, "generate_templates",
                        lambda *a, **k: called.append("templates"))   # ← якір
    monkeypatch.setattr(cli, "cleanup", lambda *a, **k: None)
    monkeypatch.setattr(cli, "mark_processed", lambda *a, **k: called.append("marked"))

    asyncio.run(cli.main())

    assert "templates" in called
    assert "marked" not in called


def test_marker_written_when_not_dry_run(monkeypatch):
    called = []
    monkeypatch.setattr(cli, "load_app_config", lambda: SimpleNamespace(dry_run=False))
    monkeypatch.setattr(cli, "is_already_processed", lambda today: False)
    monkeypatch.setattr(cli, "find_input_data", lambda *a, **k: "fake/path")
    monkeypatch.setattr(cli, "prepare_environment", lambda *a, **k: None)
    monkeypatch.setattr(cli, "generate_base_raster", lambda *a, **k: [])
    monkeypatch.setattr(cli, "generate_visualizations", lambda *a, **k: {})
    monkeypatch.setattr(cli, "generate_templates", lambda *a, **k: None)
    monkeypatch.setattr(cli, "cleanup", lambda *a, **k: None)
    monkeypatch.setattr(cli, "mark_processed", lambda *a, **k: called.append("marked"))

    async def fake_upload(*a, **k):
        called.append("uploaded")
    monkeypatch.setattr(cli, "upload_results_async", fake_upload)

    asyncio.run(cli.main())

    assert called == ["uploaded", "marked"]
