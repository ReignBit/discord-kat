import asyncio
import json
import os
import datetime
from random import shuffle
import time
from inspect import trace
from typing import Optional, Tuple, Union


import discord
import youtube_dl
from discord import player
from discord.ext import commands
from discord.guild import Guild
from bot.utils import constants
from bot.utils.cogs.newvoice import TrackPlaylist, set_logger

from bot.utils.extensions import KatCog
from bot.utils import logger, events

class MilliConvertException(Exception):
    def __init__(self):
        return Exception("Failed to convert timestamp to milliseconds")

def convert_str_to_milli(str_time):
    """Convert timestamp to a milliseconds."""
    if ":" in str_time:
        try:
            date_time = datetime.datetime.strptime(str_time, "%H:%M:%S")
        except:
            date_time = datetime.datetime.strptime(str_time, "%M:%S")

        a_timedelta = date_time - datetime.datetime(1900, 1, 1)
        return a_timedelta.total_seconds() * 1000
    
    else:
        try:
            return int(str_time) * 1000
        except:
            raise MilliConvertException

class Newvoice(KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.playlists = {}
        
        set_logger(self.log)

    def get_playlist(self, ctx) -> TrackPlaylist:
        """Attempt to retrieve a guild's TrackPlaylist or create one if does'nt exist."""
        try:
            return self.playlists[ctx.guild.id]
        except KeyError:
            player = TrackPlaylist(self.bot.loop, ctx.guild, ctx)
            self.playlists[ctx.guild.id] = player
            return player

    @commands.command()
    async def play(self, ctx, *, url=""):
        """Plays a song or playlist."""
        async with ctx.typing():
            playlist = self.get_playlist(ctx)
            tracks = []
            try:
                tracks = await playlist.insert(url, ctx.author)
            except:
                await ctx.send("That link doesn't seem to work :(")
                return
           
            if len(tracks) > 1:
                msg = "Added {} to the queue!".format(len(tracks))
            else:
                msg = "Added {} to the queue!".format(str(url))
                
            await self.playlists[ctx.guild.id].update_channel(ctx.author.voice.channel)
            
            if not await playlist.validate_voice_status():
                TrackPlaylist.logger.debug("Validating voice status error")
                return

            if not ctx.guild.voice_client.is_playing():                
                await self.playlists[ctx.guild.id].play()
                return
            
            await ctx.send(msg)
    
<<<<<<< Updated upstream
    @commands.command(aliases=['cl','purge','clearplaylist','clear'])
=======
    @commands.command(aliases=['simulatorradio'])
    async def simulator_radio(self, ctx):
        """Plays simulator radio"""        
        if(self.playlists.get(ctx.guild.id)):            
            await self.playlists[ctx.guild.id].update_channel(ctx.author.voice.channel)
            await self.playlists[ctx.guild.id].play_link("https://simulatorradio.stream/stream?1643236017005",ctx.author)
            await ctx.send("Playing simulator radio")
    
    @commands.command(aliases=['cl','purge','clearplaylist'])
>>>>>>> Stashed changes
    async def clearqueue(self, ctx):
        """Clears the current queue."""
        if self.playlists.get(ctx.guild.id):
            self.playlists[ctx.guild.id].queue = []

            await ctx.send("Cleared playlist!")
    
    @commands.command()
    async def stop(self, ctx):
        """Stop the current song."""
        if self.playlists.get(ctx.guild.id):
            self.playlists[ctx.guild.id].stop()
        
            await ctx.send("Stopped the player!")
    
    @commands.command()
    async def skip(self, ctx, url=""):
        """Skip the current song."""
        if self.playlists.get(ctx.guild.id):
            if self.playlists[ctx.guild.id].now_playing:
                await self.playlists[ctx.guild.id].skip()
                await ctx.send("Skipped the song!")
    
    @commands.command()
    async def seek(self, ctx, pos="0"):
        """Seek into the current playing song."""
        if self.playlists.get(ctx.guild.id):
            if self.playlists[ctx.guild.id].now_playing:
                
                try:
                    self.playlists[ctx.guild.id].seek_current_track(convert_str_to_milli(pos))
                    await ctx.send(f"Seeked to {pos}")
                except MilliConvertException:
                    await ctx.send("Incorrect time format. Must be in the format of either `12:34:56`, `34:56`, or `56`.")

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles current queue"""
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped:
                await ctx.send("Nothing in queue!")
                return
            await self.playlists[ctx.guild.id].shuffle()
            await ctx.send("Playlist shuffled!\n")
            line = f"Currently playing: {self.playlists[id].current_track.title}\n"
            counter = 1
            for track in await self.playlists[id].get_queue():
                line += f"{counter}. {track.title}"                
                if counter == 10:
                    break 
                counter += 1
                line += "\n"
            if await self.playlists[id].get_queue() == []:
                line += "Nothing in queue"
            await ctx.send(line)        
        else:
            await ctx.send("Nothing shuffled!")

    @commands.command(aliases=['np','nowplaying'])
    async def now_playing(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped:
                await ctx.send("Nothing in queue!")
                return  
            if self.playlists[id].current_track == None:
                await ctx.send("Nothing in queue!")
                return   
            line = f"Now playing: {self.playlists[id].current_track.title}\n"
            # timestamp = (self.playlists[id].current_track._source.ms)/1000            
            # timestamp = f"{'0' if int(round((timestamp//1))/60)<10 else ''}{int(round((timestamp//1))/60)}:{'0' if int(round((timestamp%1))*60)<10 else ''}{int(round((timestamp%1))*60)}"
            # duration = self.playlists[id].current_track.duration
            # duration = f"{'0' if int(round((duration//1))/60)<10 else ''}{int(round((duration//1))/60)}:{'0' if int(round((duration%1))*60)<10 else ''}{int(round((duration%1))*60)}"       
            # line += f"Current timestamp: {timestamp}/{duration}\n"
            line += f"Requested by: {self.playlists[id].current_track.requested_by.display_name}\n"
            line += f"{self.playlists[id].current_track.url}"
            await ctx.send(line)
            
    @commands.command()
    async def pause(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].now_playing:
                self.playlists[id].pause_play(False)
            else:
                self.playlists[id].pause_play(True)

    @commands.command(aliases=['qeueu','q'])
    async def queue(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped:
                await ctx.send("Nothing in queue!")
                return
            line = f"Currently playing: {self.playlists[id].current_track.title}\n"
            counter = 1
            for track in await self.playlists[id].get_queue():
                line += f"{counter}. {track.title}"                
                if counter == 10:
                    break 
                counter += 1
                line += "\n"
            if await self.playlists[id].get_queue() == []:
                line += "Nothing in queue"
            await ctx.send(line)

    @commands.command()
    async def debug(self, ctx):
        await ctx.send("```py\n%s\n```" % self.get_playlist(ctx))

    @commands.command(aliases=['leave','dc'])
    async def disconnect(self, ctx):
        id = ctx.guild.id
        if(self.playlists.get(id)):
            await self.playlists[id].disconnect()
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Bye bye!")

    @commands.command(aliases=['playnext'])
    async def play_next(self, ctx, *, url=""):
        """Plays a song or playlist."""
        async with ctx.typing():
            playlist = self.get_playlist(ctx)
            tracks = await playlist.insert_next(url, ctx.author)

            if len(tracks) > 1:
                msg = "Added {} to the queue!".format(len(tracks))
            else:
                msg = "Added {} to the queue!".format(str(url))

            if not await playlist.validate_voice_status():
                TrackPlaylist.logger.debug("Validating voice status error")
                return

            if not ctx.guild.voice_client.is_playing():
                await self.playlists[ctx.guild.id].play()
                return
            
            await ctx.send(msg)
        
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if(member.id != self.bot.id):
            return
        if(before.channel == after.channel):
            return
        id = member.guild.id
        if(self.playlists.get(id)):
            await self.playlists[id].voice_state_update(before, after)
        
        
            
        
    
def setup(bot):
    bot.add_cog(Newvoice(bot))
