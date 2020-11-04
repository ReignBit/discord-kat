import json

import pytest

from bot.utilities.orm_utilities import SqlEngine
from bot.utilities.KatClasses import KatGuild, KatMember, KatUser


@pytest.fixture(scope="session")
def setup():
    options = ""
    with open('bot/config/config.json', 'r') as f:
        options = f.read()

    options = json.loads(options)['sql']

    sql = SqlEngine(local=False, standalone=True, options={
                        'hostname': "reign-network.co.uk", "user": "kat_user", "password": options['password'], "db": "yumi_database"})
    sql.create_sql_session()

    return sql
