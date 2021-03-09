"""
Test unit for bot/utils/configurator.py

Tests the following scenarios:
    - Create Config
    - Create config category with name
    - Destroy config category by id
    - Create a config element with parent category
    - Destroy a config element that exists
    - Destroy a config element that does not exist
    - Attempt to retrieve information from a config element in a category
"""
import bot.utils.configurator as c

def test_create_config():
    test = c.Config()
    assert test
    test = None

def test_create_config_category():
    test_cat = c.Config()
    cat_id = test_cat.add_category("Example category", "example", desc="Example desc")

    assert cat_id == 0
    assert test_cat._categories[0].name = "Example category"

def test_destroy_category():
    test = c.Config()
    test.add_category("AAA", "BBB")
    test.remove_category(0)

    assert len(test._categories) == 0

def test_add_command_to_root():
    test = c.Config()
    test.add_configurable()
