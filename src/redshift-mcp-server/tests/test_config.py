import pytest

from redshift_mcp_server.config import ConfigurationError, Settings


def test_missing_settings_are_actionable() -> None:
    with pytest.raises(
        ConfigurationError, match="Missing environment settings: REDSHIFT_HOST"
    ) as err:
        Settings.from_env({})
    assert ".env and restart" in str(err.value)


def test_defaults_and_password_repr(configured: None) -> None:
    settings = Settings.from_env()
    assert settings.port == 5439
    assert settings.timeout == 10
    assert settings.auth_mode == "password"
    assert settings.password not in repr(settings)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("REDSHIFT_PORT", "no"),
        ("REDSHIFT_PORT", "0"),
        ("REDSHIFT_PORT", "65536"),
        ("REDSHIFT_CONNECT_TIMEOUT", "61"),
        ("REDSHIFT_CONNECT_TIMEOUT", "-1"),
        ("REDSHIFT_AUTH_MODE", "unknown"),
        ("REDSHIFT_HOST", "https://example.invalid"),
        ("REDSHIFT_HOST", "bad host"),
    ],
)
def test_bad_config_never_echoes_values(
    configured: None, monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as error:
        Settings.from_env()
    assert name in str(error.value)
    assert "synthetic-test-only" not in str(error.value)


def test_iam_does_not_require_password(configured: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDSHIFT_AUTH_MODE", "iam")
    monkeypatch.delenv("REDSHIFT_PASSWORD")
    with pytest.raises(ConfigurationError, match="AWS_REGION, REDSHIFT_CLUSTER_IDENTIFIER"):
        Settings.from_env()
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("REDSHIFT_CLUSTER_IDENTIFIER", "synthetic-cluster")
    assert Settings.from_env().password == ""
