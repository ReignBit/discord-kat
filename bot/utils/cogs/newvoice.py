import asyncio
from dis import disco
import functools
import json
from locale import currency
from re import T
from typing import Optional, Tuple

from subprocess import STDOUT

import discord
from enum import Enum

import youtube_dl
import random

#########################################################

#TODO:                STILL TO DO
# 1. Seeking is broken completely ✔                                 white noise weirdness if you seek too much?
# 2. Playing single song (no playlist) is broken ✔
# 3. Need to test if other providers still work (newsground, other) 
# 4. Replace all ctx.send() with appropriate get_embed and get_response
# 5. Go through and test all combinations of commands and states
# 6. Save song lists/queues to play later
# 7. Move command
# 8. Skip to song in queue (number)
#########################################################





ytdl = youtube_dl.YoutubeDL(
    {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'extract_flat': True,       # Speeds up extract_info by a fuck ton. (eg: 70 song playlist used to take ~30 seconds, now takes 0.4 seconds)
    'skip_download': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
)

# Used for when no url is supplied, only a search term. If extract_flat is set then we only get ytsearch:<term> and nothing of use.
ytdl_deep = youtube_dl.YoutubeDL(
    {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'extract_flat': False,       # Disabled for searches.
    'skip_download': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
)


def set_logger(logger):
    Track.logger = logger
    TrackPlaylist.logger = logger

class TrackSource(discord.PCMVolumeTransformer):
    def __init__(self, url, original, volume=0.5):
        super().__init__(original, volume)
        self.ms = 0
        self.source = url
        
    
    def read(self):
        try:
            data = super().read()
            self.ms += 20
        except Exception as e:
            Track.logger.warn(e)
        else:
            return data
        return None

    def __repr__(self):
        return str({
            'url': self.source,
            'ms': self.ms,
        })
    
    @classmethod
    def from_url(cls, url, ffmpeg_options):
        return cls(url, discord.FFmpegPCMAudio(url, **ffmpeg_options, stderr=STDOUT), volume=0.5)


class Track:
    logger = None
    def __init__(self, url, requested_by: discord.Member, data: dict, loop=None):
        """Information about a song/video in a playlist.

        source: TrackSource - Contains information about audio stream and duration
        url: str - web-front url for the video (not the actual stream url)
        requested_by: discord.Member - Member who queued the track
        duration: int - Total duration of the video
        title: str - Title of the video
        _data: JSON data retrieved via ytdl.extract_info(url) 

        Args:
            url (str): URL of the video
            requested_by (discord.Member): Member who requested/queued the track
        """
        self.loop = loop or asyncio.get_event_loop()

        self.url            = url           # A normal url (eg: https://www.youtube.com/watch?v=dQw4w9WgXcQ)
        self.requested_by   = requested_by  # discord.Member who requested the song

        self._data          = data
        self.title          = self._data['title']
        self.duration       = self._data['duration']

        self.readable       = f"{self.title} [{self.duration}] {self.requested_by.mention}"
        self._source        = None


    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, val):
        self._source = val
    

    @classmethod
    async def from_url(cls, url, requester, loop) -> list:
        """Create Track from a source url. If url is a playlist then the list of all videos is returned.

        Args:
            url (str): URL of the video(s)
            requester (discord.Member): Member who requested the video(s)
            loop (asyncio.Loop): Event loop to run on.

        Returns:
            list: List of Track
        """
        loop = loop
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))


        # Proper Youtube Playlist link (https://youtube.com/playlist?....)
        if data.get('_type', "") == "playlist":
            tracks = []
            for track in data['entries']:
                tracks.append(cls("https://youtube.com/watch?v=" + track['url'], requester, track, loop=loop))
            return tracks

        # Indirect Youtube Playlist link (https://youtube.com/watch?v=....&list=....)
        if data.get('_type', "") == "url" and data['url'].startswith("https://www.youtube.com/playlist?list="):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(data['url'], download=False))
            tracks = []
            for track in data['entries']:
                tracks.append(cls("https://youtube.com/watch?v=" + track['url'], requester, track, loop=loop))
            return tracks

        # Search Query (ytsearch:rickroll)
        if data['url'].startswith("ytsearch:"):
            data = await loop.run_in_executor(None, lambda: ytdl_deep.extract_info(url, download=False))
            data = data['entries'][0]

        return [cls(data['webpage_url'], requester, data, loop=loop)]


    def _extract_info(self):
        return self.loop.run_in_executor(None, lambda: ytdl.extract_info(self.url, download=False))


    def generate_source(self, timestamp=0) -> TrackSource:
        """Build an FFmpeg Stream from a url"""

        ffmpeg_options = {
            'options': f'-vn -ss {timestamp / 1000} -to {self.duration} -b:a 126K',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
        # We have to extract_info here again to get the latest stream URL.
        # Since youtube has expiration dates on them.
        # If we use an old url we recieve a 403 Forbidden error.

        # TODO: See about implementing some kind of caching of extract_info() based on expiretime on the source url.
        #       This would stop us requiring to extract info everytime we seek in a short period, possibly reducing time to seek.
        info = ytdl.extract_info(self.url, download=False)
        self.source = TrackSource.from_url(info['url'], ffmpeg_options)
        return self.source


    def seek(self, position: int) -> TrackSource:
        """Seek to a position in the Track (ms)"""
        Track.logger.debug(f"Seeking to position: {position}")
        self.generate_source(position)
        self.ms = position
        return self.source
        

    def reset(self):
        """Seek stream to 0."""
        self.seek(0)

    def __repr__(self):
        return str(
            {
            'title': self.title,
            'requested_by': self.requested_by.display_name,
            'duration': self.duration,
            'url': self.url,
            'source': self.source
        }
        )


class PlayerStatus(Enum):
    NOT_PLAYING = 0
    PLAYING = 1
    PAUSED = 2
    PLAYLIST_EMPTY = 3
    ERRORED = 4
    NOT_IN_CHANNEL = 5

class TrackPlaylist:
    """Per guild queue of Tracks"""

    logger = None

    def __init__(self, loop, guild: discord.Guild, ctx):
        self.queue          = []
        self.played_queue   = []
        self.now_playing    = None
        self.is_stopped     = False
        self.ctx            = ctx
        self.guild          = guild
        self.loop           = loop
        self.voice_channel  = ctx.author.voice.channel
        self.current_track  = None
        self.old_channel    = None
        
        self.status         = PlayerStatus.PLAYLIST_EMPTY

    @property
    def length(self):
        return len(self.queue)


    async def insert(self, url: str, requester: discord.Member) -> list[Track]:
        """Enqueue a new Track instance with url.

        Args:
            url (str): URL of the video to insert to queue.

        Returns:
            list[Track]: Tracks extracted from the url.
        """
        tracks = await Track.from_url(url, requester, loop=self.loop) # from_url returns list(Track)
        [self.queue.append(track) for track in tracks]
        return tracks

    async def validate_voice_status(self):
        
        #Check if kat  has a voice channel/voice client
        if self.guild.voice_client:#if kat is already connected to a voice
            return True
        elif self.voice_channel:#if kat is not connected but has voice_channel
            await self.voice_channel.connect()
            return True
        else:
            if(self.voice_channel != None):
                await self.ctx.send("You must be connected to a voice channel to use this command!")
            return False
        
    def pop(self, index=0) -> Track:
        """Remove and return a Track from the queue.

        Args:
            index (int, optional): Index to pop at. Defaults to 0.

        Returns:
            Track: Track instance that was removed from the queue.
        """
        if len(self.queue) > 0:
            return self.queue.pop(index)
        return None


    def seek_current_track(self, position: int):
        """Seek around the current playing Track

        Args:
            position (int): Position in the Track to seek to.
        """
        if self.current_track:
            self.guild.voice_client.pause()
            self.is_stopped = True
            source = self.current_track.seek(position)
            self.guild.voice_client.source = source
            self.guild.voice_client.resume()
            self.is_stopped = False
   
    async def now_playing(self):
        if self.current_track:
            return f"Now playing: {self.current_track.url}\nRequested by: {self.current_track.requested_by.display_name}"

    async def shuffle(self):
        """Shuffles playlist"""
        random.shuffle(self.queue)

    async def disconnect(self):
        """On disconnect command reset bot"""
        self.voice_channel = None
        self.status = PlayerStatus.NOT_PLAYING
        self.queue = []
        self.played_queue   = []
        self.is_stopped = True
        self.current_track = None

    async def play(self) -> None:
        """Plays the next available track. Used to start the playlist."""
        await self._after_playback(None)
        
    async def get_queue(self):
        """Get queue object"""
        return self.queue    

    async def get_now_playing(self):
        """Get current track title"""
        return str(self.current_track.title)

    def stop(self):
        """Stop the player and clear the playlist."""
        self.current_track = None
        self.queue = []
        self.played_queue   = []
        self.status = PlayerStatus.NOT_PLAYING
        self.is_stopped = True
        self.guild.voice_client.stop()

    async def skip(self) -> Track:
        """Skips the current song, if one is playing, returns the next Track"""
        self.guild.voice_client.stop()
    
    def pause_play(self, resume=False) -> None:
        """Pause/Resume the current playing Track

        Args:
            resume (bool, optional): should we resume or stop current playback? Defaults to False.
        """

        if not resume:
            self.is_stopped = True
            self.guild.voice_client.pause()
        else:
            self.is_stopped = False
            self.guild.voice_client.resume()

     

    async def _after_playback(self, error=None):
        # pre
        await self._pre_after_playback(error)

    async def _pre_after_playback(self, error):
        """Called when a Track has finished playing.

        Args:
            error (Exception): Exception that has occured during playback. None if no error.
            ctx (discord.Context): Original Context object of the message that caused playback ($play).
        """
        ctx = self.ctx

        if error:
            TrackPlaylist.logger.warn(error)
            self.status = PlayerStatus.ERRORED
            raise error

        if not await self.validate_voice_status():
            return

        if self.length == 0:
            TrackPlaylist.logger.debug(f"{self.guild.id} no longer has Tracks in the queue.")
            self.current_track = None
            self.status = PlayerStatus.PLAYLIST_EMPTY
            return

        if self.is_stopped:
            TrackPlaylist.logger.debug(f"{self.guild.id} is_stopped=True")
            self.status = PlayerStatus.PAUSED
            return

        # Has playlist, with tracks, not stopped, in voice
        track = self.pop()            
        self.current_track = track
        self.played_queue.append(self.current_track)
        self.guild.voice_client.play(track.generate_source(), after=lambda e: self.loop.create_task(self._after_playback(e)))
        embed = discord.Embed(title=f"Now playing: {track.title}",url = f"{track.url}", description=f"Requested by: {track.requested_by.display_name}", color=16777215)
        await ctx.send(embed = embed)
                
        self.status = PlayerStatus.PLAYING
        return self.current_track

    async def voice_state_update(self, before, after):
        """Event for when bot gets disconnected/moved by force"""
        self.voice_channel = after.channel  
        if self.voice_channel == None:#If bot get's disconnected by user
            TrackPlaylist.logger.info(f"[{self.guild.id} | {self.guild.name}] Bot Disconnected from voice by force")
            self.voice_channel = None
            self.old_channel = before
            self.status = PlayerStatus.NOT_PLAYING
            self.queue = []
            self.played_queue   = []
            self.is_stopped = True
            self.current_track = None
            if self.guild.voice_client != None:
                await self.guild.voice_client.disconnect()
                            
        elif before.channel != None:#If bot moved
            TrackPlaylist.logger.info(f"[{self.guild.id} | {self.guild.name}] Bot moved")
            if(self.guild.voice_client == None):
                await self.voice_channel.connect() 
            self.status = PlayerStatus.PLAYING
            self.is_stopped = False                
            self.guild.voice_client.resume()  
            
        else:#initial join
            if(self.guild.voice_client == None):
                await self.voice_channel.connect() 
            self.status = PlayerStatus.PLAYING
            self.is_stopped = False                
            self.guild.voice_client.resume()
     
    async def insert_next(self, url: str, requester: discord.Member):
        tracks = await Track.from_url(url, requester, loop=self.loop) # from_url returns list(Track)
        i = 0
        for track in tracks:
            self.queue.insert(i,track)
            i += 1
    
    async def update_channel(self,channel):
        self.voice_channel = channel
    
    async def play_link(self,link,author):
        track = Track(link, author, data={"title":"simulator radio","duration":60000000})
        if self.queue == []:
            self.guild.voice_client.play(link)
        else:
            self.queue.append(track)
            if self.guild.voice_client == None:
                self.voice_channel.connect()
    
    async def skip_queue(self, count):
        if len(self.queue) < count:
              return
        count = int(count)
        TrackPlaylist.logger.debug(count)
        track = self.queue.pop(count-1)
        return track.title
        
    def __repr__(self):
        return str({
            'status': self.status.name,
            'now_playing': self.current_track,
            'length': self.length,
            'queue': [track for track in self.queue]
        })