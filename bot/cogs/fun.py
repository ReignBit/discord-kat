import json
import random
import time
import datetime
import asyncio
import re
import os

import discord
import requests
from discord.ext import commands

from bot.utils.extensions import KatCog, read_resource, write_resource

class Fun(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.megumin_gif_cache = self.get_cached_gifs()
        self.pat_gif_cache = {}
        self.megu_cache_time = 3600     # 1 hour until it re-gets gifs

        # day of the week reponse flags
        self.dayresponse = [
            "***:boom: It's Megumonday! :boom:***\n今日、メグー月曜日だよ！",
        ]

        self.bot.run_day_check = True


    def get_cached_gifs(self):
        self.log.info("Refreshing gif cache for 1 hour...")

        r = requests.get(
            "https://api.tenor.com/v1/search?q=megumin&key={}&limit=8&anon_id=312ced313baf42079d1588df7e032c69".format(self.settings.get('gify_api_key')))
        if r.status_code == 200:
            # load the GIFs using the urls for the smaller GIF sizes
            return json.loads(r.content)
        return []

    async def _get_gif(self, search_query):
        """ Sends API call to tenor, for search_query. Returns a random gif from result."""
        r = requests.get(
        "https://api.tenor.com/v1/search?q={}&key={}&limit=20&anon_id=312ced313baf42079d1588df7e032c69".format(search_query,self.settings.get('gify_api_key')))
        if r.status_code == 200:
            # load the GIFs using the urls for the smaller GIF sizes
            raw = json.loads(r.content)['results']
            _ = raw[random.randrange(0, len(raw))]['media'][0]['gif']['url']

            while _ == "https://media.tenor.com/images/4bdc2faacb4abfc4fc6f9c8b759cd583/tenor.gif":
                _ = raw[random.randrange(0, len(raw))]['media'][0]['gif']['url']
            return _


    def _generate_generic_embed(self, ctx, gif, action, user: discord.User=None):
        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} performs {action} to everyone!")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} performs {action} to {user.display_name} O.o")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"{ctx.author.display_name} performs {action} to K- wait a minute! :flushed:")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        return embed

    def _generate_specific_embed(self, ctx, gif, responses, user: discord.User=None, color=discord.Color.red()):
        """
        Generates a embed for emotes.
            responses should look like:
                {
                    "everyone" : "kisses everyone! <3",
                    "user" : "kisses {user.display_name} Aww!",
                    "kat" : "kisses Ka- Wait a minute! O.o"
                }
        """
        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} " + responses['everyone'])
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} " + responses['user'].format(user))
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=responses['kat'])

        embed.set_image(url=gif)
        embed.colour = color
        return embed



    @commands.Cog.listener()
    async def on_kat_hour_event(self):
        if not self.bot.run_day_check:
            return

        try:
            guild = discord.utils.get(self.bot.guilds, id=311612862554439692)
            channel = discord.utils.get(guild.channels, id=432214639305162752)
        except AttributeError:
            # we mustn't be able to see Reign guild
            self.bot.run_day_check = False
            return

        self.log.info("Daily check started.")
        date = datetime.datetime.today()

        if date.weekday() is 0: #is monday
            if "megu_done" not in os.listdir("bot/resources/days/"):
                await channel.send(self.dayresponse[0], file = discord.File('bot/resources/days/0.png'))

                write_resource('days/megu_done', 1)
                self.log.info("It's megumonday!")
        else:
            try:
                os.remove('resources/days/megu_done')
            except FileNotFoundError:
                pass

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if "gorl" in ctx.content.lower() and ctx.guild.id == 311612862554439692:
            emoji = discord.utils.get(self.bot.get_guild(311612862554439692).emojis, name='gorl')
            await ctx.add_reaction(emoji)

    @commands.command()
    async def time(self, ctx):
        embed = discord.Embed(title="The time is (GMT)")
        embed.description = str(datetime.datetime.now())
        embed.set_footer(text="WIP. Timezones coming soon.")
        await ctx.send(embed=embed)

    @commands.command()
    async def stuff(self, ctx):
        f = discord.File("bot/resources/stuff.png", filename="stuff.png")
        embed = discord.Embed()
        embed.set_author(name="I'll stuff you all in the crust!")
        embed.set_image(url="attachment://stuff.png")
        await ctx.send(file=f, embed=embed)


    @commands.command()
    async def emote(self, ctx, action: str, user: discord.User=None):
        """Do a custom emote ($emote <action> <mention>)"""
        gif = await self._get_gif("anime%20{}".format(action))
        await ctx.channel.send(embed=self._generate_generic_embed(ctx, gif, action, user))


    @commands.command()
    async def spank(self, ctx, user: discord.User=None):
        """Spank ($spank <mention>)"""
        gif = await self._get_gif("anime%20spank")

        responses = {
            'everyone': "spanks everyone!",
            'user': "spanks {user.display_name} kinky!",
            'kat': "I-I'm sorry! ;-;"
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)



    @commands.command()
    async def nom(self, ctx, user: discord.User=None):
        """Nom ($nom <mention>)"""
        gif = await self._get_gif("anime%20nom")

        responses = {
            'everyone': "noms everyone!",
            'user': "takes a nibble of {user.display_name} tasty!",
            'kat': "D-do I taste good?"
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)


    @commands.command(aliases=['cum'])
    async def lewd(self, ctx, user: discord.User=None):
        """Lewd someone ($lewd <mention>)"""
        gif = await self._get_gif("anime%20lewd")

        responses = {
            'everyone': "does lewd things to everyone!",
            'user': "lewdifies {user.display_name} How lewd!",
            'kat': "Hentai!"
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)


    @commands.command(aliases=['giveflower'])
    async def flower(self, ctx, user: discord.User=None):
        """Give someone a flower ($flower <mention>)"""
        gif = await self._get_gif("anime%20flower")

        responses = {
            'everyone': "gives everyone a flower!",
            'user': "hands {user.display_name} a flower!",
            'kat': "A flower for me? O.O"
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)


    @commands.command(aliases=['murder'])
    async def kill(self, ctx, user: discord.User=None):
        """Kill someone ($kill <mention>)"""
        gif = await self._get_gif("anime%20kill")

        responses = {
            'everyone': "kills everyone!",
            'user': "kills {user.display_name}! F",
            'kat': "[insert death noises here]"
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)


    @commands.command(aliases=['snuggle'])
    async def cuddle(self, ctx, user: discord.User=None):
        """Snuggle ($snuggle <mention>)"""
        gif = await self._get_gif("anime%20snuggle")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} cuddles everyone!")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} cuddles {user.display_name}:3")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"Nya~ (*´ω｀)")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)


    @commands.command()
    async def pat(self, ctx, user: discord.User=None):
        """Pat a user's head ($pat <mention>)"""
        gif = await self._get_gif("anime%20pat")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} pats everyone")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} pats {user.display_name}'s head :3")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"Nya~ (*´ω｀)")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)


    @commands.command()
    async def lick(self, ctx, user: discord.User=None):
        """Lick a user ($lick <mention>)"""
        gif = await self._get_gif("anime%20lick")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} licks everyone")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} licks {user.display_name} O.o")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"B-Baka!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)


    @commands.command()
    async def hug(self, ctx, user: discord.User=None):
        """Hug a user ($hug <mention>)"""
        gif = await self._get_gif("anime%20hug")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} hugs everyone")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} hugs {user.display_name} :3")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"W-What are you doing! :flushed:")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def slap(self, ctx, user: discord.User = None):
        """Slap a user ($slap <mention>)"""
        gif = await self._get_gif("anime%20slap")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} slaps everyone!")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} slaps {user.display_name}!")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"いたい! That hurt!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def kiss(self, ctx, user: discord.User=None):
        """Kiss a user ($kiss <mention>)"""
        gif = await self._get_gif("anime%20kiss")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} kisses everyone")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} kisses {user.display_name} <3")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"I-It's not like I like you or anything!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=['handhold'])
    async def holdhand(self, ctx, user: discord.User=None):
        """Hold a users hand ($holdhand/$handhold <mention>)"""
        gif = await self._get_gif("hold%20hand")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} holds everyones hand")
        else:
            if user is not None and user.id != 379153719180394498:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(title=f"{ctx.author.display_name} holds hands with {user.display_name}")
            elif user.id == 379153719180394498:
                embed = discord.Embed(title=f"I-It's not like I like you or anything!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)



    @commands.command()
    async def random(self, ctx, *args):
        """Let Kat choose from a list of inputs ($random 1 2 3 4 ...)"""
        if args is None:

            raise IndexError("Missing list of items to choose from.")
        await ctx.send("**Hmm... I pick `{}`!**".format(random.choice(args)))

    @random.error
    async def random_error(self, ctx, error):
        if isinstance(error, IndexError):
            await ctx.send(self.get_response("common.error.missing_args", args="list"))


    #### Hit or miss
    @commands.command(aliases=['huh'])
    async def hitormiss(self, ctx):
        """I guess they never miss, huh?"""
        await ctx.send(
            "**I guess they never miss, huh?**\nhttps://cdn.discordapp.com/attachments/569186352583933953/570671772320661544/nico1.mp4")

    @commands.command(aliases=['owo'])
    async def owoifier(self, ctx):
        """Turn any message into cancer"""
        last_message = await ctx.channel.history(limit=2).flatten()
        last_message = last_message[1].content.lower()
        last_message = re.sub(r'[RrIl]', "w", last_message)
        last_message = last_message.replace("ove", "uv")
        last_message = last_message.replace("thi", "wi")

        await ctx.send(last_message)



def setup(bot):
    bot.add_cog(Fun(bot))
