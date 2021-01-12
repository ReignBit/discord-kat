import json
import os

import pytest

from bot.utils.setting_loader import Settings

config = {'test_key': 1, 'embedded_dict': {'test': 1}}

fallback = {'test_key': 1, 'embedded_dict': {'test': 1, 'not_in': True}}



@pytest.fixture(scope="session")
def setup():
    settings = Settings(config, fallback)
    return settings
