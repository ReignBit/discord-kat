import asyncio
import json
import os
import datetime
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
            tracks = await playlist.insert(url, ctx.author)

            if len(tracks) > 1:
                msg = "Added {} to the queue!"
            else:
                msg = "Added tracks to the queue!"

            if not await playlist.check_voice_status():
                return

            if not ctx.guild.voice_client.is_playing():
                await self.playlists[ctx.guild.id].play()
                return
            
            await ctx.send(msg)
    
    @commands.command(aliases=['cl','purge','clearplaylist'])
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
        if self.playlists.get(ctx.guild.id):
            await self.playlists[ctx.guild.id].shuffle()
            await ctx.send("Playlist shuffled!")
        else:
            await ctx.send("Nothing shuffled!")

    @commands.command()
    async def pause(self, ctx):
        if self.playlists.get(ctx.guild.id):
            if self.playlists[ctx.guild.id].now_playing:
                self.playlists[ctx.guild.id].pause_play(False)
            else:
                self.playlists[ctx.guild.id].pause_play(True)

    @commands.command()
    async def queue(self, ctx):
        if self.playlists.get(ctx.guild.id):
            string = "```\n" + "".join([f"{i}. {track.readable}\n" for i, track in enumerate(self.playlists[ctx.guild.id].queue)]) + "```"
            await ctx.send(string)

    @commands.command()
    async def debug(self, ctx):
        await ctx.send("```py\n%s\n```" % self.get_playlist(ctx))

def setup(bot):
    bot.add_cog(Newvoice(bot))
