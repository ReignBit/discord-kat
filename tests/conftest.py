import json
import os

import pytest

from bot.utils.database import SqlEngine
from bot.utils.models import KatGuild, KatMember, KatUser


@pytest.fixture(scope="session")
def setup():
    options = ""

    sql_pass = os.environ.get("sql-pass")
    sql_user = os.environ.get("sql-user")
    sql_db = os.environ.get("sql-db")

    options = json.loads(options)['sql']

    sql = SqlEngine(local=False, standalone=True, options={
                        'hostname': "reign-network.co.uk", "user": sql_user, "password": sql_pass, "db": sql_db})
    sql.create_sql_session()

    return sql
