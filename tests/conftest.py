import json

import pytest

from bot.utils.database import SqlEngine
from bot.utils.models import KatGuild, KatMember, KatUser


@pytest.fixture(scope="session")
def setup():
    options = ""
    with open('config/config.json', 'r') as f:
        options = f.read()

    options = json.loads(options)['sql']

    sql = SqlEngine(local=False, standalone=True, options={
                        'hostname': "reign-network.co.uk", "user": "kat_user", "password": options['password'], "db": "yumi_database"})
    sql.create_sql_session()

    return sql
