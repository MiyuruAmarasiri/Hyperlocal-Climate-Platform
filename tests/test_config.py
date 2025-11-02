from shared.config import get_settings


def test_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv('DATA_ROOT', str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.data_root.exists()
