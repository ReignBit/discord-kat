from typing import Union

from contextlib import contextmanager
import sqlalchemy

from bot.utils.models import sessionmaker, KatGuild, KatUser, KatMember
from bot.utils import logger as KatLogger


# TODO: This needs a rewrite. It is too dependant on external code.
class SqlEngine:
    MASTER_SQL = None
    COUNT = -1

    def __init__(self, bot=None, local=True, use_kat_logger=True, standalone=False, options=None):
        SqlEngine.COUNT += 1
        if use_kat_logger:
            self.log = KatLogger.get_logger("SQL")
            self.log.info(
                "SQLEngine Instance {} Created".format(SqlEngine.COUNT))

        if standalone:
            self._sql_engine = sqlalchemy.create_engine(
                f"mysql+mysqldb://{options['user']}:{options['password']}@{options['hostname']}/{options['db']}")

        if bot is not None:
            self.bot = bot
            _sql_settings = self.bot.settings['sql']
            SqlEngine.MASTER_SQL = self
            self._sql_engine = sqlalchemy.create_engine("mysql+mysqldb://{}:{}@{}/{}".format(_sql_settings['user'],
                                                                                             _sql_settings['password'],
                                                                                             _sql_settings['hostname'],
                                                                                             _sql_settings['db']))
            if use_kat_logger:
                self.log.debug("Created BOT SQL Engine")
        elif not standalone:
            self._sql_engine = SqlEngine.MASTER_SQL.get_engine()

    def create_sql_session(self):
        Session = sessionmaker(bind=self._sql_engine)
        self._sql_session = Session()

    def destroy(self):
        self._sql_session.close()
        SqlEngine.COUNT -= 1
        self.log.destroy()
        del self

    @contextmanager
    def get_sql_session(self):
        if not self._sql_session:
            self.create_sql_session()
        session = self._sql_session
        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            session.commit()

    def get_engine(self):
        """Returns 'master' engine. Will only return if we have the Bot object."""
        if self.bot is not None:
            return self._sql_engine
        else:
            return False

    def sql_test(self):
        """Output length of `guild_data` table."""
        with self.get_sql_session() as session:
            return len(session.query(KatGuild).all())

    def query(self, kat_class: str):
        """Returns a filterable list (SQLAlchemy.orm.query.Query Object)"""
        with self.get_sql_session() as session:
            if kat_class is "KatGuild":
                return session.query(KatGuild)
            if kat_class is "KatMember":
                return session.query(KatMember)
            if kat_class is "KatUser":
                return session.query(KatUser)

    def purge_unguilded_users(self):
        """Deletes unguilded users from the database."""
        with self.get_sql_session() as session:
            user_ids = session.query(KatUser.user_id).all()
            members = session.query(KatMember.user_id).all()
            for user in user_ids:
                if user not in members:
                    self.log.debug(
                        "Found unguilded user `%s`, deleting..." % user)
                    session.query(KatUser).filter_by(user_id=user).delete()

    def edit_prefix(self, guild_id, new_prefix):
        """Updates a guild's prefix in the database."""
        with self.get_sql_session():
            guild = self.ensure_exists("KatGuild", guild_id=guild_id)
            guild.prefix = new_prefix
            return guild.prefix

    def ensure_exists(self, kat_class, guild_id=None, user_id=None) -> Union[KatGuild, KatUser, KatMember]:
        """Ensures that the Object relation exists in the DB and returns the result. 
           If one is not found an entry is generated and returned.
        """

        if kat_class is "KatGuild":
            if guild_id is not None:
                with self.get_sql_session() as session:
                    result = session.query(KatGuild).filter_by(
                        guild_id=guild_id).first()
                    if result == None:
                        new = KatGuild(guild_id=guild_id)
                        session.add(new)
                        result = new
                    return result
            else:
                return - 1

        elif kat_class is "KatMember":
            if guild_id is not None and user_id is not None:
                with self.get_sql_session() as session:
                    result = session.query(KatMember).filter_by(
                        guild_id=guild_id, user_id=user_id).first()
                    if result == None:
                        self.ensure_exists("KatUser", user_id=user_id)
                        new = KatMember(guild_id=guild_id, user_id=user_id)
                        session.add(new)
                        result = new
                    return result
            else:
                return - 1

        elif kat_class is "KatUser":
            if user_id is not None:
                with self.get_sql_session() as session:
                    result = session.query(KatUser).filter_by(
                        user_id=user_id).first()
                    if result == None:
                        new = KatUser(user_id=user_id)
                        session.add(new)
                        result = new
                    return result
            else:
                return - 1


if __name__ == "__main__":
    sql = SqlEngine(bot=None, local=False,
                    use_kat_logger=False, standalone=True)
    guilds = sql.query("KatGuild").all()
