import asyncio

from bot.utils import logger as KatLogger


MAX_EVENT_TIMER = 86400


class EventManager:
    """Managed event caller for Kat.

    Events are registered with `create_event` and are called every `seconds`.

    event information is stored in `self._events`:

    ```
        self._events = {
            "event-name": ()
        }

    """

    def __init__(self, bot, cog=None):
        """Creates new instance of EventManager

        arguments:
            bot: Kat - Bot that the event manager should run on.
            cog: extension.KatCog - KatCog instance which owns the event manager.
        """

        if cog is not None:
            # If we are not owned by a cog, then create a new logger.
            self.log = KatLogger.get_logger(
                "{}.EventManager".format(cog.qualified_name)
            )

        else:
            self.log = KatLogger.get_logger("EventManager")

        self.bot = bot
        self._events = {}

        try:
            self.settings = self.bot.settings.from_key("EventManager")
        except KeyError:
            self.settings = {}

    def create_event(self, name, seconds):
        """Register an event `name` to loop every `seconds`."""

        if not name.startswith("kat"):
            # ensure our events start with a prefix as to not interfer with internal ones.
            name = "kat_" + name

        if "on_" + name in self.bot.extra_events:
            # If we have already registered this event.
            self.log.warning(
                "Tried to create event `{}` that already exists!".format(name)
            )
        elif seconds > MAX_EVENT_TIMER:
            self.log.warning(
                "Tried to create event `{}` with a wait period longer than {} seconds.".format(
                    name, MAX_EVENT_TIMER
                )
            )
        else:

            event = self.bot.loop.create_task(self._event(name, seconds))
            self._events[name] = event
            self.log.info(
                f"Registered new event `{name}` for every `{seconds}` seconds"
            )

    def create_events(self, event_map: dict):
        """Create multiple events.

        `event_map`: Dict - {'event_name': int}
        """

        for k, v in event_map.items():
            self.create_event(k, v)

    def remove_event(self, name):
        """Unregister an event.

        `name`: str - Event name to unregister.
        """

        if name in self._events:
            try:
                self._events[name].cancel()
                del self._events[name]
                self.log.info("Deleted event `{}`".format(name))

            except Exception as e:
                self.log.exception(
                    "Exception caught whilst trying to delete event `{}` ".format(name),
                    exc_info=e,
                )
                return -1
        else:
            self.log.warning(
                "Tried to delete event that doesn't exist in this EventManager instance."
            )
            return -2

    def destroy(self):
        """Safely stops all running events and ends the instance.

        Should be called whenever a KatCog unloads.
        """

        for name in self._events:
            try:
                self.log.debug("Attempting to delete event `{}`".format(name))
                self._events[name].cancel()
            except Exception as e:
                self.log.exception(
                    "Exception caught whilst trying to delete event `{}` ".format(name),
                    exc_info=e,
                )
        del self

    async def _event(self, name, seconds):
        """Calls event and waits."""
        while name in self._events:
            self.bot.dispatch(name)
            await asyncio.sleep(seconds)
