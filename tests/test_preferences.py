"""User preferences tests."""

from app.schemas.preferences import DEFAULT_PREFERENCES, UserPreferences


def test_default_preferences() -> None:
    prefs = UserPreferences()
    assert prefs.notifications_enabled is True
    assert prefs.hide_adult is True
    assert prefs.alert_on_release is True


def test_preferences_serialization() -> None:
    data = DEFAULT_PREFERENCES.model_dump()
    restored = UserPreferences.model_validate(data)
    assert restored.notifications_enabled == DEFAULT_PREFERENCES.notifications_enabled