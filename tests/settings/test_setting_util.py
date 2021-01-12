import pytest

from bot.utils.setting_loader import Settings

def test_get_item_from_settings(setup: Settings):
    assert setup['test_key'] is not None

def test_get_nested_item_from_settings(setup: Settings):
    assert setup['embedded_dict']['test'] is not None

def test_set_item_to_settings(setup: Settings):
    setup['example'] = 10
    assert setup['example'] == 10

def test_set_item_to_nested_settings(setup: Settings):
    setup['embedded_dict']['example'] = 11
    assert setup['embedded_dict']['example'] == 11

def test_get_item_not_in_settings_but_in_fallback(setup: Settings):
    assert setup['embedded_dict']['not_in'] is not None

def test_get_item_not_exist(setup: Settings):
    assert setup['not_exist'] is None

