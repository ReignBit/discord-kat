"""
Test unit for setting_loader.py

Tests the following scenarios:
    - Get item
    - Set item
    - Get nested item
    - Get nested item
    - Get invalid item
    - Get item from fallback
"""
import os


from bot.utils.setting_loader import Settings


def test_get_item_from_settings(setup: Settings):
    assert setup.get("test_key") is not None


def test_get_nested_item_from_settings(setup: Settings):
    assert setup.get("embedded_dict.test") is not None


def test_set_item_to_settings(setup: Settings):
    print(setup)
    setup.set("example", 10)
    print(setup)
    assert setup.get("example") == 10


def test_set_item_to_nested_settings(setup: Settings):
    setup.set("embedded_dict.example", 11)
    assert setup.get("embedded_dict.example") == 11


def test_get_item_not_in_settings_but_in_fallback(setup: Settings):
    assert setup.get("embedded_dict.not_in") is not None


def test_get_item_not_exist(setup: Settings):
    assert setup.get("not_exist") is None


def test_bool_cast_from_item(setup: Settings):
    assert type(bool(setup.get("bool_test"))) is bool


def test_create_from_file(setup):
    print(os.getcwd())
    test = Settings.from_file("tests/settings/test.json", "tests/settings/test_fallback.json")
    print(test._settings_dict)
    assert test.get("test_key") == "test_value"
