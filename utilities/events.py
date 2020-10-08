import asyncio
import utilities.KatLogger as KatLogger

    # PLANNING
    # When we unload a cog that created the event we should also remove the event. Since its highly unlikely that
    # an event that was created in a cog will be used in another cog if that cog is unloaded.
    # This means we need to keep a reference to which cog creates the event.

    # To do this we could just change the data in the EVENTS dict to a tuple (event_obj, cog_name)
    # but im not sure if this is the best way to do it?
    # We could have one EventManager per cog?
    # Then when we unload the cog we could simply call a method that cleans up that EventManager instance
    # this sounds like the simpler and cleaner idea. I think i will stick with this.
    # Buutttt this also runs the issue of having conflicting event names in seperate cogs,
    # since we are using DAPI's event dispatch method.

    # One solution to this would be to just change the event names to: kat_<cog_name>_<event_name>
    # Actually, if we have two events with the same name, it's highly likely that they will be used for the same thing.
    # So we could just return a warning to console that the event name already exists and just let the Listener listen for that event instead.
    # But... how do we know that event exists? We need a global list of event names. I wonder if DAPI already has this...
    
    # DAPI already has a global event list. bot.extra_events
    # bot.extra_events = {'on_event_name': <methods that listen for this event>}


class EventManager:
    def __init__(self, bot, cog=None):
        if cog is not None:
            self.log = KatLogger.get_logger("{}.EventManager".format(cog.qualified_name))
            
        else:
            self.log = KatLogger.get_logger("EventManager")
        #self.log.debug("EventManager Instance created.")
        self.bot = bot
        self._events = {}
        # _events = {
        #   "event_name" : (<asyncio>, callable1, callable2)
        # }

        try:
            self.settings = self.bot.settings['EventManager']
        except KeyError:
            self.settings = {}
    

    #TODO: Add args passthrough for events that require custom arguments.
    def create_event(self, name, seconds):
        if not name.startswith('kat'):
            name = "kat_" + name

        # TODO: Revise this. Need some global list to avoid duplicate dispatches of same events.
        if "on_" + name in self.bot.extra_events:
            self.log.warning("Tried to create event `{}` that already exists!".format(name))
        elif seconds > self.settings['MAX_EVENT_TIMER']:
            self.log.warning("Tried to create event `{}` with a wait period longer than {} seconds.".format(name, self.settings['MAX_EVENT_TIMER']))
        else:

            event = self.bot.loop.create_task(self._event(name, seconds))
            self._events[name] = event
            self.log.info("Registered new event `{}` executing every `{}` seconds".format(name, seconds))

    def create_events(self, event_map: dict):
        """ Create multiple events through a dictionary in the form {'event_name': seconds}"""
        for k, v in event_map.items():
            self.create_event(k, v)
        

    def remove_event(self, name):
        if name in self._events:
            try:
                self._events[name].cancel()
                del self._events[name]
                self.log.info("Deleted event `{}`".format(name))

            except Exception as e:
                self.log.exception("Exception caught whilst trying to delete event `{}` ".format(name), exc_info=e)
                return -1
        else:
            self.log.warning("Tried to delete event that doesn't exist in this EventManager instance.")
            return -2


    def destroy(self):
        """Should be called whenever a Cog is unloaded."""
        for name in self._events:
            try:
                self.log.debug("Attempting to delete event `{}`".format(name))
                self._events[name].cancel()
            except Exception as e:
                self.log.exception("Exception caught whilst trying to delete event `{}` ".format(name), exc_info=e)
        #self.log.info("Cancelled all events. Destroying self.")
        del self


    # TODO: Time verification. Throw warning when fired before firetime.
    async def _event(self, name, seconds):
        while name in self._events:
            self.bot.dispatch(name)
            #self.log.debug("Dispatched event `{}`".format(name))
            await asyncio.sleep(seconds)