import asyncio
import json
import os
import datetime
from random import shuffle
import time
from inspect import trace
from typing import Optional, Tuple, Union
import math

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

def convert_sec_to_str(seconds):
    """Convert milliseconds to a timestamp."""
    line = str(datetime.timedelta(seconds=seconds))
    if int(line[0:line.find(':')]) == 0:
        line = line[line.find(':')+1:]
    return line


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
                embed = discord.Embed(title=f"That link doesn't seem to work:(", color=16777215)
                await ctx.send(embed = embed)
                return
                           
            await self.playlists[ctx.guild.id].update_channel(ctx.author.voice.channel)
            
            if not await playlist.validate_voice_status():
                TrackPlaylist.logger.debug("Validating voice status error")
                return
            
            if len(tracks) == 1:
                song = tracks[0]
                await ctx.send(
                    embed = discord.Embed.from_dict(
                        self.get_embed(
                            "newvoice.embeds.play",
                            track = url,
                            youtube_url = song.url,
                            added_title = song.title,
                            youtube_link = song.url,
                            duration = f"{convert_sec_to_str(song.duration)}",
                            author = song.requested_by
                        )
                    )
                ) 
            elif len(tracks) > 1:
                duration = 0
                for track in tracks:
                    duration += track.duration
                await ctx.send(
                    embed = discord.Embed.from_dict(
                        self.get_embed(
                            "newvoice.embeds.play",
                            track = f"{len(tracks)} tracks",
                            youtube_url = str(url),
                            added_title = "",
                            youtube_link = str(url),
                            duration = f"Total duration: {convert_sec_to_str(duration)}",
                            author = ctx.author.display_name
                        )
                    )
                ) 
            self.playlists[ctx.guild.id].is_stopped = False     
            if not ctx.guild.voice_client.is_playing():                
                await self.playlists[ctx.guild.id].play()
                return
            
    
    @commands.command(aliases=['cl','purge','clearplaylist','clear'])
    async def clearqueue(self, ctx):
        """Clears the current queue."""
        if self.playlists.get(ctx.guild.id):
            self.playlists[ctx.guild.id].queue = []
            embed = discord.Embed(title=f"Cleared the playlist!", color=16777215)
            await ctx.send(embed = embed)
    
    @commands.command()
    async def stop(self, ctx):
        """Stop the current song."""
        if self.playlists.get(ctx.guild.id):
            self.playlists[ctx.guild.id].stop()        
            embed = discord.Embed(title=f"Stopped the music", color=16777215)
            await ctx.send(embed = embed)
    
    @commands.command()
    async def skip(self, ctx, count:str=None):
        """Skip the current song."""
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].current_track:
                if(count == None):
                    await self.playlists[id].skip()
                    embed = discord.Embed(title=f"Skipped current song", color=16777215)
                    await ctx.send(embed = embed)
                    return
                # ctx.send(count)
                # title = await self.playlists[id].skip_queue()
                
                    
    
    @commands.command()
    async def seek(self, ctx, pos="0"):
        """Seek into the current playing song."""
        if self.playlists.get(ctx.guild.id):
            if self.playlists[ctx.guild.id].current_track:                
                try:
                    self.playlists[ctx.guild.id].seek_current_track(convert_str_to_milli(pos))
                    embed = discord.Embed(title=f"Seeked to {pos}", color=16777215)
                    await ctx.send(embed = embed)
                except MilliConvertException:
                    embed = discord.Embed(title=f"Incorrect time format. Must be in the format of either `12:34:56`, `34:56`, or `56`.", color=16777215)
                    await ctx.send(embed = embed)

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles current queue"""
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped:
                embed = discord.Embed(title=f"Nothing in the queue", color=16777215)
                await ctx.send(embed = embed)
                return
            await self.playlists[id].shuffle()
            embed = discord.Embed(title=f"Playlist shuffled", color=16777215)
            await ctx.send(embed = embed)
            line = ""
            counter = 1
            #
            for track in await self.playlists[id].get_queue():
                title = str(track.title).replace('"',"").replace("'","").replace("$","")
                line += f"{counter}. {title} | duration: [{convert_sec_to_str(track.duration)}]"                
                if counter == 10:
                    break 
                else:
                    counter += 1
                    line += "\n"
            if await self.playlists[id].get_queue() == []:
                line += "Nothing in queue"
            await ctx.send(
                embed = discord.Embed.from_dict(
                    self.get_embed(
                        "newvoice.embeds.queue",
                        currently_playing_title = self.playlists[id].current_track.title,
                        youtube_url = self.playlists[id].current_track.url,
                        timestamp = convert_sec_to_str(self.playlists[id].current_track.duration),
                        author = ctx.author.display_name,
                        song_list = str(line)
                    )
            ))    
        else:
            embed = discord.Embed(title=f"Nothing to shuffle. Try adding some songs using the play command", color=16777215)
            await ctx.send(embed = embed)

    @commands.command(aliases=['np','nowplaying'])
    async def now_playing(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped:
                embed = discord.Embed(title=f"Bot is currently stopped", color=16777215)
                await ctx.send(embed = embed)
                return  
            if self.playlists[id].current_track == None:
                embed = discord.Embed(title=f"Nothing is currently playing", color=16777215)
                await ctx.send(embed = embed)
                return   
            timestamp = math.ceil((self.playlists[id].current_track._source.ms)/1000)          
            duration = math.ceil(self.playlists[id].current_track.duration)
            
            comp_line   = ""
            to_line     = ""
            for x in range(math.floor(timestamp/duration*20)):
                comp_line += "═"
            for x in range(math.ceil(((duration-timestamp)/duration)*20)):
                to_line += "═"
                
                       
            await ctx.send(
                embed = discord.Embed.from_dict(
                    self.get_embed(
                        "newvoice.embeds.now_playing",
                        current_now = "Currently",
                        title_of_song = self.playlists[id].current_track.title,
                        youtube_url = self.playlists[id].current_track.url,
                        youtube_link = self.playlists[id].current_track.url,
                        completed_line = comp_line,
                        to_play_line = to_line,
                        timestamp = f"{convert_sec_to_str(timestamp)}/{convert_sec_to_str(duration)}",
                        author = self.playlists[id].current_track.requested_by.display_name
                    )
            ))
            
    @commands.command()
    async def pause(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].current_track:
                self.playlists[id].pause_play(False)
            else:
                self.playlists[id].pause_play(True)

    @commands.command(aliases=['qeueu','q'])
    async def queue(self, ctx):
        id = ctx.guild.id
        if self.playlists.get(id):
            if self.playlists[id].is_stopped or self.queue == []:
                embed = discord.Embed(title=f"Queue", description=f"Nothing in queue", color=16777215)
                await ctx.send(embed=embed)
                return
            
            line = ""
            counter = 1
            #
            for track in await self.playlists[id].get_queue():
                title = str(track.title).replace('"',"").replace("'","").replace("$","")
                line += f"{counter}. {title} | duration: [{convert_sec_to_str(track.duration)}]"                
                if counter == 10:
                    break 
                else:
                    counter += 1
                    line += "\n"
            if await self.playlists[id].get_queue() == []:
                line += "Nothing in queue"
            await ctx.send(
                embed = discord.Embed.from_dict(
                    self.get_embed(
                        "newvoice.embeds.queue",
                        currently_playing_title = self.playlists[id].current_track.title,
                        youtube_url = self.playlists[id].current_track.url,
                        timestamp = convert_sec_to_str(self.playlists[id].current_track.duration),
                        author = ctx.author.nick,
                        song_list = str(line)
                    )
            ))

    @commands.command()
    async def debug(self, ctx):
        await ctx.send("```py\n%s\n```" % self.get_playlist(ctx))

    @commands.command(aliases=['leave','dc','kys'])
    async def disconnect(self, ctx):
        id = ctx.guild.id
        if(self.playlists.get(id)):
            await self.playlists[id].disconnect()
            await ctx.guild.voice_client.disconnect()
            embed = discord.Embed(title=f"Bye Bye :)", color=16777215)
            await ctx.send(embed = embed)

    # @commands.command(aliases=['playnext'])
    # async def play_next(self, ctx, *, url=""):
    #     """Plays a song or playlist."""
    #     async with ctx.typing():
    #         playlist = self.get_playlist(ctx)
    #         tracks = await playlist.insert_next(url, ctx.author)

    #         if len(tracks) > 1:
    #             msg = "Added {} to the queue!".format(len(tracks))
    #         else:
    #             msg = "Added {} to the queue!".format(str(url))

    #         if not await playlist.validate_voice_status():
    #             TrackPlaylist.logger.debug("Validating voice status error")
    #             return

    #         if not ctx.guild.voice_client.is_playing():
    #             await self.playlists[ctx.guild.id].play()
    #             return
            
    #         await ctx.send(msg)
        
        
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
