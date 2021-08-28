import random
import datetime
import re
import os
import time

import discord
import requests
from discord.ext import commands

from bot.utils.extensions import KatCog, write_resource
from bot.utils import constants


class Fun(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.cocks = 0
        self.gif_cache = {}
        # TODO: Not sure if this is still used.
        self.megu_cache_time = 3600

        # day of the week reponse flags
        self.dayresponse = [
            "***:boom: It's Megumonday! :boom:***\n今日、メグー月曜日だよ！",
        ]

        self.bot.run_day_check = True

    def _get_and_cache_gifs(self, search_query):
        """Download gif cache and store results for 1 hour."""
        self.log.info(f"Caching gifs for {search_query} for 1 hour...")
        r = requests.get(
            "https://api.tenor.com/v1/search?q={}&key={}&limit=20&anon_id={}".format(
                search_query,
                constants.Fun.api_key,
                constants.Fun.anon_key,
            )
        )
        if r.status_code == 200:
            gif_links = []
            for gif in r.json()["results"]:
                # All of the gif links.
                gif_links.append(gif["media"][0]["gif"]["url"])

            self.gif_cache[search_query] = (time.time(), gif_links)

    async def _get_gif(self, search_query):
        """Returns a random gif from the gif cache.
        If query is not already in the cache, we download gif collection and then cache it.
        """
        if (
            search_query not in self.gif_cache
            or self.gif_cache[search_query][0] + 3600 < time.time()
        ):
            self.log.debug(f"Cache expired for {search_query}.")
            self._get_and_cache_gifs(search_query)

        # return a random gif from cached gif links.
        raw = self.gif_cache[search_query][1]
        return raw[random.randrange(0, len(raw))]

    def _generate_generic_embed(self, ctx, gif, action, user: discord.User = None):
        responses = {
            "everyone": f"performs {action} to everyone!",
            "user": "performs " + action + " to {user.display_name} O.o",
            "self": f"performs {action} to me!? :flushed:",
        }
        return self._generate_specific_embed(ctx, gif, responses, user, constants.Color.soft_red)

    def _generate_specific_embed(
        self, ctx, gif, responses, user: discord.User = None, color=discord.Color.red()
    ):
        """
        Generates an embed for emotes.
            responses should look like:
                {
                    "everyone" : "kisses everyone! <3",
                    "user" : "kisses {user.display_name} Aww!",
                    "self" : "kisses Ka- Wait a minute! O.o"
                }
        """
        if user is None:
            embed = discord.Embed(
                title=f"{ctx.author.display_name} " + responses["everyone"]
            )
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} " + responses['user'].format(user=user)
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title=responses["self"])

        embed.set_image(url=gif)
        embed.colour = color
        return embed

    @commands.Cog.listener()
    async def on_kat_hour_event(self):
        if not self.bot.run_day_check:
            return

        try:
            guild = discord.utils.get(self.bot.guilds, id=constants.HomeGuild.ids[0])
            channel = discord.utils.get(guild.channels, id=constants.HomeGuild.channels[0])
        except AttributeError:
            # we mustn't be able to see Reign guild
            self.bot.run_day_check = False
            return

        self.log.info("Daily check started.")
        date = datetime.datetime.today()

        if date.weekday():  # is monday
            if "megu_done" not in os.listdir("bot/resources/days/"):
                await channel.send(
                    self.dayresponse[0], file=discord.File("bot/resources/days/0.png")
                )

                write_resource("days/megu_done", "1")
                self.log.info("It's megumonday!")
        else:
            try:
                os.remove("bot/resources/days/megu_done")
            except FileNotFoundError:
                pass

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if "gorl" in ctx.content.lower() and ctx.guild.id in constants.HomeGuild.ids:
            emoji = discord.utils.get(
                self.bot.get_guild(311612862554439692).emojis, name="gorl"
            )
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
    async def emote(self, ctx, action: str, user: discord.User = None):
        """Do a custom emote ($emote <action> <mention>)"""
        gif = await self._get_gif("anime%20{}".format(action))
        await ctx.channel.send(
            embed=self._generate_generic_embed(ctx, gif, action, user)
        )

    @commands.command()
    async def spank(self, ctx, user: discord.User = None):
        """Spank ($spank <mention>)"""
        gif = await self._get_gif("anime%20spank")

        responses = {
            "everyone": "spanks everyone!",
            "user": "spanks {user.display_name} kinky!",
            "self": "I-I'm sorry! ;-;",
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def nom(self, ctx, user: discord.User = None):
        """Nom ($nom <mention>)"""
        gif = await self._get_gif("anime%20nom")

        responses = {
            "everyone": "noms everyone!",
            "user": "takes a nibble of {user.display_name}, tasty!",
            "self": "D-do I taste good?",
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["cum"])
    async def lewd(self, ctx, user: discord.User = None):
        """Lewd someone ($lewd <mention>)"""
        gif = await self._get_gif("anime%20lewd")

        responses = {
            "everyone": "does lewd things to everyone!",
            "user": "lewdifies {user.display_name} How lewd!",
            "self": "Hentai!",
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["giveflower"])
    async def flower(self, ctx, user: discord.User = None):
        """Give someone a flower ($flower <mention>)"""
        gif = await self._get_gif("anime%20flower")

        responses = {
            "everyone": "gives everyone a flower!",
            "user": "hands {user.display_name} a flower!",
            "self": "A flower for me? O.O",
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["murder"])
    async def kill(self, ctx, user: discord.User = None):
        """Kill someone ($kill <mention>)"""
        gif = await self._get_gif("anime%20kill")

        responses = {
            "everyone": "kills everyone!",
            "user": "kills {user.display_name}! F",
            "self": "[insert death noises here]",
        }

        embed = self._generate_specific_embed(ctx, gif, responses, user=user)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["snuggle"])
    async def cuddle(self, ctx, user: discord.User = None):
        """Snuggle ($snuggle <mention>)"""
        gif = await self._get_gif("anime%20snuggle")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} cuddles everyone!")
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} cuddles {user.display_name}:3"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="Nya~ (*´ω｀)")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def pat(self, ctx, user: discord.User = None):
        """Pat a user's head ($pat <mention>)"""
        gif = await self._get_gif("anime%20pat")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} pats everyone")
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} pats {user.display_name}'s head :3"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="Nya~ (*´ω｀)")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def lick(self, ctx, user: discord.User = None):
        """Lick a user ($lick <mention>)"""
        gif = await self._get_gif("anime%20lick")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} licks everyone")
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} licks {user.display_name} O.o"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="B-Baka!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def hug(self, ctx, user: discord.User = None):
        """Hug a user ($hug <mention>)"""
        gif = await self._get_gif("anime%20hug")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} hugs everyone")
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} hugs {user.display_name} :3"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="W-What are you doing! :flushed:")
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
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} slaps {user.display_name}!"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="いたい! That hurt!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def kiss(self, ctx, user: discord.User = None):
        """Kiss a user ($kiss <mention>)"""
        gif = await self._get_gif("anime%20kiss")

        if user is None:
            embed = discord.Embed(title=f"{ctx.author.display_name} kisses everyone")
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} kisses {user.display_name} <3"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="I-It's not like I like you or anything!")
        embed.set_image(url=gif)
        embed.colour = discord.Color.red()
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["handhold"])
    async def holdhand(self, ctx, user: discord.User = None):
        """Hold a users hand ($holdhand/$handhold <mention>)"""
        gif = await self._get_gif("hold%20hand")

        if user is None:
            embed = discord.Embed(
                title=f"{ctx.author.display_name} holds everyones hand"
            )
        else:
            if user is not None and user.id != self.bot.id:
                user = ctx.guild.get_member(user.id)
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} holds hands with {user.display_name}"
                )
            elif user.id == self.bot.id:
                embed = discord.Embed(title="I-It's not like I like you or anything!")
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

    # Hit or miss
    @commands.command(aliases=["huh"])
    async def hitormiss(self, ctx):
        """I guess they never miss, huh?"""
        await ctx.send(
            "**I guess they never miss, huh?**"
            "\nhttps://cdn.discordapp.com/attachments/569186352583933953/570671772320661544/nico1.mp4"
        )

    @commands.command(aliases=["owo"])
    async def owoifier(self, ctx):
        """Turn any message into cancer"""
        last_message = await ctx.channel.history(limit=2).flatten()
        last_message = last_message[1].content.lower()
        last_message = re.sub(r"[RrIl]", "w", last_message)
        last_message = last_message.replace("ove", "uv")
        last_message = last_message.replace("thi", "wi")

        await ctx.send(last_message)

        # Cock counter for omegle

    @commands.command(aliases=["cc"])
    async def cockcounter(self, ctx, arg=None):
        """Keep track of cocks seen during omegle ($cockcounter)"""
        guild = self.sql.ensure_exists("KatGuild", guild_id=ctx.guild.id)
        cock_highscore = guild.ensure_setting(constants.GuildSettings.fun_counter, 0)

        if arg is None:
            self.cocks += 1
            if self.cocks > cock_highscore:
                guild.set_setting(constants.GuildSettings.fun_counter, cock_highscore + 1)
                cock_highscore += 1
                gif = await self._get_gif("celebrate")

                # If new highscore achived, send embed.
                embedHighscore = discord.Embed
                embedHighscore = discord.Embed()
                embedHighscore.title = "NEW COCK HIGHSCORE"
                embedHighscore.description = " "
                embedHighscore.color = constants.Color.invisible
                embedHighscore.set_image(url=gif)
                await ctx.send(embed=embedHighscore)

        elif arg == "start":
            self.cocks = 0
        elif arg == "reset":
            self.cocks = 0
            guild.set_setting(constants.GuildSettings.fun_counter, 0)
            cock_highscore = 0

        embed = discord.Embed()
        embed.title = "Official Cock Counter"
        embed.description = (
            "Current Amount of cocks: {}\n"
            "Current Highscore: {}".format(self.cocks, cock_highscore)
        )
        embed.color = 15843965
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
