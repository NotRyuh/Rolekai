import pytest
from pydantic import ValidationError


def test_malformed_port_is_rejected_without_leaking_password():
    from rolekai.settings import Settings

    value = "postgresql://user:private-password@localhost:not-a-port/rolekai"
    with pytest.raises(ValidationError) as error:
        Settings(database_url=value, _env_file=None)
    assert "private-password" not in str(error.value)


def test_database_url_is_required_and_secret_safe(monkeypatch):
    from rolekai.settings import Settings

    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    value = "postgresql://candidate:private-password@localhost:15432/rolekai"
    settings = Settings(database_url=value, _env_file=None)
    assert settings.database_url.get_secret_value() == value
    assert "private-password" not in str(settings)
    assert "private-password" not in repr(settings)


@pytest.mark.parametrize("value", ["https://u:private-password@host/db", "not-a-dsn"])
def test_invalid_database_url_does_not_leak_input(value):
    from rolekai.settings import Settings

    with pytest.raises(ValidationError) as error:
        Settings(database_url=value, _env_file=None)
    assert value not in str(error.value)
    assert "private-password" not in str(error.value)


def test_readiness_timeout_has_a_bounded_range():
    from rolekai.settings import Settings

    for value in (0, 11):
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql://localhost/rolekai",
                database_connect_timeout_seconds=value,
                _env_file=None,
            )
