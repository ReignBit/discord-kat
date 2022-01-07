import asyncio
import functools
import json
from typing import Optional, Tuple

import discord

import youtube_dl


#########################################################

#TODO:                STILL TO DO
# 1. Seeking is broken completely
# 2. Playing single song (no playlist) is broken
# 3. Need to test if other providers still work (newsground, other)
# 4. Replace all ctx.send() with appropriate get_embed and get_response
# 5. Go through and test all combinations of commands and states

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
    'default_search': 'youtube',
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
        self.ms += 20
        return super().read()


    def __repr__(self):
        return {
            'url': self.source,
            'ms': self.ms,
        }

    def __str__(self):
        return str({
            'url': self.source,
            'ms': self.ms,
        })
    
    @classmethod
    def from_url(cls, url, ffmpeg_options):
        return cls(url, discord.FFmpegPCMAudio(url, **ffmpeg_options), volume=0.5)


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
        if self._source is None:
            Track.logger.warn("Tried to access source before it was generated!")
        return self._source
    
    @source.setter
    def source(self, val):
        self._source = val
    

    @classmethod
    async def from_url(cls, url, requester, loop=None) -> list:
        """Create Track from a source url. If url is a playlist then the list of all videos is returned.

        Args:
            url (str): URL of the video(s)
            requester (discord.Member): Member who requested the video(s)
            loop (asyncio.Loop, optional): Event loop to run on. If left blank, asyncio.get_event_loop() is called.

        Returns:
            list: List of Track
        """
        loop = loop

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if data.get('_type', "") == "playlist":
            tracks = []
            for track in data['entries']:
                tracks.append(cls("https://youtube.com/watch?v=" + track['url'], requester, track, loop=loop))
            return tracks

        return [cls(url, requester, data, loop=loop)]


    def _extract_info(self):
        return self.loop.run_in_executor(None, lambda: ytdl.extract_info(self.url, download=False))


    def generate_source(self, timestamp=0) -> TrackSource:
        """Build an FFmpeg Stream from a url"""

        ffmpeg_options = {
            'options': f'-vn -ss {timestamp}',
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
        self.generate_source(position)
        return self.source
        

    def reset(self):
        """Seek stream to 0."""
        self.seek(0)

    def __str__(self):
        return json.dumps(
            {
            'title': self.title,
            'requested_by': self.requested_by.display_name,
            'duration': self.duration,
            'url': self.url,
            'source': self.source.__repr__()
        }
        ,indent=4
        )


class TrackPlaylist:
    """Per guild queue of Tracks"""

    logger = None

    def __init__(self, loop, guild: discord.Guild, ctx):
        self.queue          = []
        self.now_playing    = None
        self.is_stopped     = False
        self.ctx            = ctx
        self.guild          = guild
        self.loop           = loop

    @property
    def length(self):
        return len(self.queue)


    async def insert(self, url: str, requester: discord.Member) -> Track:
        """Enqueue a new Track instance with url.

        Args:
            url (str): URL of the video to insert to queue.

        Returns:
            list(Track): Tracks extracted from the url.
        """
        tracks = await Track.from_url(url, requester, loop=self.loop) # from_url returns list(GuildQueueItem)
        [self.queue.append(track) for track in tracks]


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
        if self.now_playing:
            source = self.now_playing.seek(position)
            self.ctx.guild.voice_client.source = source

    
    async def play(self) -> None:
        """Plays the next available track. Used to start the playlist."""
        await self._after_playback(None)
    
    def stop(self):
        """Stop the player and clear the playlist."""
        self.now_playing = None
        self.queue = []
        self.ctx.guild.voice_client.stop()

    async def skip(self) -> Track:
        """Skips the current song, if one is playing, returns the next Track"""
        self.ctx.guild.voice_client.stop()
    
    def pause_play(self, resume=False) -> None:
        """Pause/Resume the current playing Track

        Args:
            resume (bool, optional): should we resume or stop current playback? Defaults to False.
        """

        if not resume:
            self.is_stopped = True
            self.ctx.guild.voice_client.pause()
        else:
            self.is_stopped = False
            self.ctx.guild.voice_client.resume()

    async def check_voice_status(self):
        # If author no voice
        # If have voice and author have diff voice channel
        ctx = self.ctx
        if not ctx.author.voice:
            await ctx.send("You must be connected to a voice channel to use this command!")
            return False
        
        if not ctx.guild.voice_client:
            await ctx.author.voice.channel.connect()
            return True

        if ctx.guild.voice_client.channel != ctx.author.voice.channel:
            await ctx.send("You must be in the same room as Kat to use this command!")
            return False
        return True            


    async def _after_playback(self, error):
        """Called when a Track has finished playing.

        Args:
            error (Exception): Exception that has occured during playback. None if no error.
            ctx (discord.Context): Original Context object of the message that caused playback ($play).
        """
        ctx = self.ctx

        TrackPlaylist.logger.debug(error)
        if error:
            TrackPlaylist.logger.warn(error)
            await ctx.send(error)

        if await self.check_voice_status() == False:
            TrackPlaylist.logger.debug(f"{ctx.guild.id} failed to join voice due to user error.")
            return

        if self.length == 0:
            TrackPlaylist.logger.debug(f"{ctx.guild.id} no longer has Tracks in the queue.")
            return

        if self.is_stopped:
            TrackPlaylist.logger.debug(f"{ctx.guild.id} is_stopped=True")
            return

        # Has playlist, with tracks, not stopped, in voice
        track = self.pop()
        self.now_playing = track
        TrackPlaylist.logger.debug(str(track.generate_source()))
        ctx.guild.voice_client.play(track.source, after=lambda e: self.loop.create_task(self._after_playback(e)))
        await ctx.send(f"Now playing: {track.url}\nRequested by: {track.requested_by.display_name}")
        return self.now_playing


    def json(self):
        return {
            'now_playing': self.now_playing,
            'length': self.length,
            'queue': [track.__str__ for track in self.queue]
        }
