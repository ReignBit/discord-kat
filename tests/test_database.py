import json

import pytest

from bot.utilities.KatClasses import KatUser, KatGuild, KatMember


def test_sql_ensure_exists(setup):
    user = setup.ensure_exists("KatUser", user_id=172408031060033537)
    assert isinstance(user, KatUser)

    guild = setup.ensure_exists("KatGuild", guild_id=438542169855361025)
    print(guild)
    assert isinstance(guild, KatGuild)

    member = setup.ensure_exists(
        "KatMember", guild_id=438542169855361025, user_id=172408031060033537)
    assert isinstance(member, KatMember)

