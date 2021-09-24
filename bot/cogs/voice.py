import asyncio
import json
import os

from discord import player
from discord.ext import commands
import discord
from discord.guild import Guild
import youtube_dl

from bot.utils.extensions import KatCog

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

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

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
        return cls(data.get('url'), requester, data.get('title'), data)

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
    def __init__(self, source, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, loop=None, stream=False, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, volume=volume)

class Voice(KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.queues = {}


    # @commands.command()
    # async def join(self, ctx):
    #     if ctx.author.voice:
    #         self.players[ctx.guild.id] = await ctx.author.voice.channel.connect()
    #         await ctx.send("Connected!")

    async def check_voice_status(self, ctx):
        # If author no voice
        # If have voice and author have diff voice channel
        
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
        

    async def _after_play(self, error, ctx):
        if error:
            self.log.warn(error)

        if self.queues.get(ctx.guild.id):
            # The guild has a queue
            if len(self.queues[ctx.guild.id].queue) > 0:
                if not self.queues[ctx.guild.id].is_stopped:
                    guild_queue_item = self.queues[ctx.guild.id].pop()
                    source = await StreamSource.from_url(guild_queue_item.url, loop=self.bot.loop, stream=True)
                    ctx.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self._after_play(e, ctx)))
                
                    now_playing = self.queues[ctx.guild.id].now_playing
                    await ctx.send(f'Now playing: {now_playing.title} - {now_playing.webpage_url} - {now_playing.requester}')

            else:
                # Queue is now empty
                del self.queues[ctx.guild.id]

    @commands.command()
    async def play(self, ctx, *, url=None):
        if await self.check_voice_status(ctx) == False:
            return


        if url is None and ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            await ctx.send(":arrow_forward: Resuming music!")
            return

        if url is None and self.queues.get(ctx.guild.id):
            if self.queues[ctx.guild.id].is_stopped:
                self.queues[ctx.guild.id].is_stopped = False
                await self._after_play(None, ctx)
            return

        if url is None:
            await ctx.send("Missing argument! `url / search`: Video to play.")

        async with ctx.typing():
            item = await GuildQueueItem.from_url(url, ctx.author)

            if not self.queues.get(ctx.guild.id):
                # We are not playing any songs, create a queue and start music
                if not ctx.guild.voice_client:
                    await ctx.author.voice.channel.connect()
                self.queues[ctx.guild.id] = GuildQueue(ctx.guild)
                
                self.queues[ctx.guild.id].add(item)
                await self._after_play(None, ctx)
            else:
                if self.queues[ctx.guild.id].is_stopped:
                    self.queues[ctx.guild.id].is_stopped = False
                    await self._after_play(None, ctx)
                # Already have a queue, just add url to queue
                self.queues[ctx.guild.id].add(item)
                await ctx.send("Added " + item.title + " to the queue!")
    
    @commands.command()
    async def stop(self, ctx):
        "Stops the current song."
        if not await self.check_voice_status(ctx):
            return

        if self.queues.get(ctx.guild.id):
            self.queues[ctx.guild.id].is_stopped = True
            ctx.guild.voice_client.stop()
            await ctx.send(":stop_button: Stopped the music!")

    @commands.command()
    async def pause(self, ctx):
        if not await self.check_voice_status(ctx):
            return
        await ctx.send(":pause_button: Paused music!")
        ctx.guild.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        if not await self.check_voice_status(ctx):
            return
        ctx.guild.voice_client.resume()
        await ctx.send(":arrow_forward: Resuming music!")

    @commands.command()
    async def leave(self, ctx):
        if not await self.check_voice_status(ctx):
            return
        await ctx.guild.voice_client.disconnect()

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if self.queues.get(ctx.guild.id):
            queue = []
            for i, item in enumerate(self.queues[ctx.guild.id].queue):
                queue.append(f"{i+1}. - [{item.title}]({item.webpage_url}) [{item.duration}] {item.requester.mention}")

            if len(queue) > 0:
                embed = discord.Embed.from_dict(self.get_embed("voice.embeds.queue"))
                embed.description = "\n".join(queue)
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed.from_dict(self.get_embed("voice.embeds.no_queue", prefix=ctx.prefix)))
        else:
            await ctx.send(embed=discord.Embed.from_dict(self.get_embed("voice.embeds.no_queue", prefix=ctx.prefix)))
    
    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        if self.queues.get(ctx.guild.id):
            if self.queues.get(ctx.guild.id).now_playing:
                item = self.queues.get(ctx.guild.id).now_playing
                await ctx.send(f"**{item.title}**\n{item.webpage_url}\n*Requested By: {item.requester}*")

    @commands.command()
    async def remove(self, ctx, index: int):
        if not await self.check_voice_status(ctx):
            return
        if self.queues.get(ctx.guild.id):
            try:
                item = self.queues[ctx.guild.id].queue.pop(index-1)
                await ctx.send(f"Removed `{item.title}` from the queue")
            except:
                pass

    @commands.command()
    async def move(self, ctx, src: int, dest: int):
        if not await self.check_voice_status(ctx):
            return
        if self.queues.get(ctx.guild.id):
            if len(self.queues.get(ctx.guild.id).queue) >= src and len(self.queues.get(ctx.guild.id).queue) >= dest:
                queue = self.queues.get(ctx.guild.id).queue
                a = queue.pop(src-1)
                queue.insert(dest-1, a)
                self.queues.get(ctx.guild.id).queue = queue

                await ctx.send(f"Moved {src} to {dest}")

    @commands.command()
    async def purge(self, ctx):
        if not await self.check_voice_status(ctx):
            return
        if self.queues.get(ctx.guild.id):
            self.queues[ctx.guild.id].queue = []
            await ctx.send("Cleared the queue!")

    @commands.command()
    async def skip(self, ctx):
        if not await self.check_voice_status(ctx):
            return
        if ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
            await ctx.send(":track_next: Skipping current song!")

    @commands.command()
    async def exportqueue(self, ctx):
        async with ctx.typing():
            with open(str(ctx.guild.id) + ".katq", "wb") as f:
                f.write(json.dumps(self.queues[ctx.guild.id].to_json(), indent=4).encode("utf-8"))
                pass
            
            with open(str(ctx.guild.id) + ".katq", "rb") as f:
                await ctx.send(f"Current queue has been exported! Use `{ctx.prefix}load` with this file to load the queue.", file=discord.File(f))
            
            os.remove(str(ctx.guild.id) + ".katq")


    #TODO: Load queues


    def cog_unload(self):
        for q in self.bot.guilds:
            self.bot.loop.create_task(q.voice_client.disconnect())
        
        super().__init__(self.bot)

def setup(bot):
    bot.add_cog(Voice(bot))
