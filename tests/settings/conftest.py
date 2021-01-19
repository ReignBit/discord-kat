import pytest

from bot.utils.setting_loader import Settings

config = {'test_key': 1, 'embedded_dict': {'test': 1}, 'bool_test': 1}
fallback = {'test_key': 1, 'embedded_dict': {'test': 1, 'not_in': 1}}


@pytest.fixture(scope="session")
def setup():
    settings = Settings(config, fallback)
    return settings
