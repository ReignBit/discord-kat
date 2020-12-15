import json

import pytest

from bot.utils.database import SqlEngine
from bot.utils.models import KatUser, KatGuild, KatMember
from bot.cogs.moderation.warnsys import Warn



def test_data_fetch(setup: SqlEngine):
    member = setup.ensure_exists(
        "KatMember", guild_id=438542169855361025, user_id=172408031060033537)

    print(member.settings)
    assert type(member.settings) == dict

    # Make sure that we have a warnsys.warns key available.
    warn_list = member.ensure_setting("warnsys.warns", [])

    #Create a new warn
    warn = Warn("This is a reason", 1234567890, 172408031060033537, 0)
    warn_list.append(warn.to_dict())

    with setup.get_sql_session() as session:
        member.set_setting("warnsys.warns", warn_list)
        session.commit()

    assert member.get_setting("warnsys.warns") == warn_list
