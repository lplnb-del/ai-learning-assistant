from ai_study_agent.core.config import AppConfig


def test_config_uses_safe_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

    config = AppConfig.from_env()

    assert config.deepseek_api_key is None
    assert not config.has_llm_key
    assert config.deepseek_base_url == "https://api.deepseek.com"
    assert config.deepseek_model == "deepseek-v4-flash"


def test_config_reads_llm_key_without_echoing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    config = AppConfig.from_env()

    assert config.has_llm_key
    assert config.deepseek_api_key == "test-key"


def test_config_reads_local_dotenv_without_printing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    tmp_path.joinpath(".env").write_text(
        'DEEPSEEK_API_KEY="dotenv-key"\nDEEPSEEK_MODEL=deepseek-v4-flash\n',
        encoding="utf-8",
    )

    config = AppConfig.from_env()

    assert config.has_llm_key
    assert config.deepseek_api_key == "dotenv-key"
    assert config.deepseek_model == "deepseek-v4-flash"
