import discord
import asyncio

import youtube_dl

MAX_TRIES_GET_STREAM = 5

ytdl = youtube_dl.YoutubeDL(
    {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
)

class GuildQueueItem:
    __slots__ = "url", "requester", "title", "webpage_url", "duration", "data"
    def __init__(self, url, requester, title, data=None):
        
        if data.get("entries"):
            self.url = data['entries'][0]['webpage_url']
            self.title = data['entries'][0]['title']
        else:
            self.url = url
            self.title = title

        self.data = data['entries'][0] if data.get("entries") else data
        self.requester = requester
        

        self.webpage_url = self.data['webpage_url']
        self.duration = self.data.get('duration', '???')
    
    def to_json(self):
        return {'url':self.url, 'requester':self.requester.id, 'title': self.title, 'webpage_url': self.webpage_url, 'duration': self.duration}

    @classmethod
    async def from_url(cls, url, requester=None):
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))     
        return cls(data.get('webpage_url'), requester, data.get('title'), data)

    @classmethod
    async def from_url_playlist(cls, url, requester=None):
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        playlist = []
        if data['_type'] == "playlist":
            for item in data['entries']:
                playlist.append(cls(item.get('webpage_url'), requester, item.get("title"), item))
            return playlist

class GuildQueue:
    def __init__(self, guild):
        self.guild = guild
        self.now_playing = None
        self.is_stopped = False
        self.queue = []
    
    def add(self, item):
        self.queue.append(item)
    
    def pop(self):
        self.now_playing = self.queue[0]
        return self.queue.pop(0)
    
    def to_json(self):
        o = []
        for track in self.queue:
            o.append(track.to_json())
        return {'guild': self.guild.id, 'now_playing': self.now_playing.to_json(), 'is_stopped': self.is_stopped, 'tracks': o}


class StreamSource(discord.PCMVolumeTransformer):
    def __init__(self, source, data, volume=0.5, ms=0):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.ms = ms

    def read(self):
        """Reads 20ms of audio"""
        self.ms += 20
        return super().read()


    @classmethod
    async def from_url(cls, url, loop=None, stream=False, volume=0.5, timestamp=0):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        ffmpeg_options = {
            'options': f'-vn -ss {timestamp}',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, volume=volume, ms=timestamp)


def get_player_bar(item: GuildQueueItem, source: StreamSource) -> str:
    BAR_LENGTH = 20
    
    now = source.ms / 1000
    percent = (now / item.duration)

    bar = b'\xe2\x96\xac'.decode("utf-8") * BAR_LENGTH
    l = bar[:int(len(bar) * percent)]
    r = bar[int(len(bar) * percent):]

    return "[{}](https://kat.reign-network.co.uk):radio_button:{}".format(l,r)