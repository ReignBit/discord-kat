# discord specific imports
from discord.ext import commands
import discord

# python imports
import json
import html
import re

# third party imports
from translate import Translator
import requests

# kat specific imports
import utilities.KatCog as KatCog

class Translate(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        # make sure we only have one translator. Only really using this for Reign for now, in the future
        # we may want to have this be a dict and have some sort of TranslatorManager or smth.
        self.tranlator = None

        # list of all languages that have an ISO code (2-char)
        self.lang_list = {}

        # retrieve said list and turn it into a dict using json.load()
        with open('resources/languages.json', 'r', encoding='utf-8') as f:
            self.lang_list = json.load(f, encoding='utf-8')
    
    

    async def _translate(self, from_lang, to_lang, msg):
        self.tranlator = Translator(to_lang=to_lang, from_lang=from_lang, provider="mymemory")
        translation = self.tranlator.translate(msg)
        # self.log.debug(type(translation))
        return html.unescape(translation)


    @commands.Cog.listener()
    async def on_message(self, message):
        """If Hiragana or Katakana detected, attempt to translate"""
        if message.author.bot:
            return

        if re.search("[\u3040-\u30ff]", message.content) is not None:
            result = await self._translate("ja", "en", message.content)
            embed = discord.Embed(colour=discord.Colour(0x2b2b2b), description=result)
            embed.set_author(name="{} Auto Translate".format(message.author.display_name), icon_url=message.author.avatar_url)
            embed.set_footer(text="⚠️| Powered by opensource translations. May not be accurate.")
            #embed.set_footer(text="Options to disable auto translation are WIP.")
            await message.channel.send(embed=embed)

    @commands.command(aliases=['tlast', 'translateuser', 'tuser'])
    async def translatelast(self, ctx, user: discord.User, lang='en'):
        """Translates a user's last message in the current channel"""
        # from_lang : to_lang
        if ":" in lang:
            from_lang = lang.split(':')[0]
            to_lang = lang.split(':')[1]
            if len(to_lang) is not 2:
                to_lang = 'en'
        else:
            from_lang = "ja"
            to_lang = lang

        msgs = await ctx.channel.history(limit=100).flatten()
        for message in msgs:
            if message.author == user:
                result = await self._translate(from_lang, to_lang, message.clean_content)
                embed = discord.Embed(colour=discord.Colour(0x2b2b2b), description=result)
                embed.set_author(name="{}".format(message.author.display_name), icon_url=message.author.avatar_url)
                await ctx.send(embed=embed)
                return

        embed = discord.Embed(colour=discord.Colour(0x2b2b2b), description="Could not find {}'s last message. Could be older than 100 messages!".format(user.display_name))
        await ctx.send(embed=embed)

    @commands.command(aliases=['tmsg'])
    async def translatemsg(self, ctx, message_id: int, lang='en'):
        """Translates a message by message id"""
        # from_lang : to_lang
        if ":" in lang:
            from_lang = lang.split(':')[0]
            to_lang = lang.split(':')[1]
            if len(to_lang) is not 2:
                to_lang = 'en'
        else:
            from_lang = "ja"
            to_lang = lang

        try:
            msgs = await ctx.channel.fetch_message(message_id)
            #self.log.debug(msgs)
            result = await self._translate(from_lang, to_lang, msgs.clean_content)
        except Exception as e:
            self.log.debug(e)
            await ctx.send("Unable to find message. Could be deleted.")
            return

        embed = discord.Embed(colour=discord.Colour(0x2b2b2b), description=result)
        embed.set_author(name="{}".format(msgs.author.name), icon_url=msgs.author.avatar_url)
        await ctx.send(embed=embed)


    @commands.command()
    async def translate(self, ctx, lang='en'):
        """Attempts to translate the last sent message. If no language code is given then defaults to English."""

        # $translate list
        if lang == "list":
            _ = "Language Codes for Translation (Some listed languages may not be supported)"
            # return a fancy string with nice formatted list of languages.
            for k, v in self.lang_list.items():
                _ += "`{}` : {}\n".format(k,v)
            # send the list to authors pm box
            await ctx.author.send("```apache\n{}```".format(_))
            return
    
        # from_lang : to_lang
        if ":" in lang:
            from_lang = lang.split(':')[0]
            to_lang = lang.split(':')[1]
            if len(to_lang) is not 2:
                to_lang = 'en'
        else:
            from_lang = "ja"
            to_lang = lang

        self.log.debug(to_lang + ':' + from_lang)
        msgs = await ctx.channel.history(limit=2).flatten()

        # if the message includes an embed then cancel the translation.
        if len(msgs[1].embeds) == 0:

            # Show to the user that the command is being processed.
            async with ctx.channel.typing():
                # Attempt to translate. Unsure what errors, if any, are thrown by Translator

                result = await self._translate(from_lang, to_lang, msgs[1].clean_content)
                # trying to translate from the same language (en-en)
                if result == b"PLEASE SELECT TWO DISTINCT LANGUAGES":
                    await ctx.send("Already in English!")
                    return
                # was given an invalid language to translate into to / from
                if b"INVALID TARGET LANGUAGE" in result:
                    await ctx.send("Invalid language! For a full list of available languages, do `$translate list`")
                    return

                # create the embed to show fancy results to user.
                embed = discord.Embed(colour=discord.Colour(0x2b2b2b), description="{}".format(result))
                embed.set_author(name="{}".format(msgs[1].author.display_name), icon_url=msgs[1].author.avatar_url)

            # delete the command message
            await msgs[0].delete()
            # send our message
            await ctx.send(embed=embed)

        else:
            # message had an embed. aborted.
            await ctx.send("Unable to translate that message :(")



    @commands.command(aliases=['ttext'])
    async def translatetext(self, ctx, lang='en'):     
        """Translate text in the message that was sent by the author"""

        # Get rid of extra text from msg
        msg = ctx.message.clean_content
        if "$ttext" in msg:
            msg = msg.replace("$ttext","")
        else:
            msg = msg.replace("$translatetext","")  
        await ctx.send(msg)


        # from_lang : to_lang
        if ":" in lang:
            from_lang = lang.split(':')[0]
            to_lang = lang.split(':')[1]
            if len(to_lang) is not 2:
                to_lang = 'en'
        else:
            from_lang = "ja"
            to_lang = lang

        try:
            #self.log.debug(msgs)
            result = await self._translate(from_lang, to_lang, msg.clean_content)
        except Exception as e:
            self.log.debug(e)
            await ctx.send("Unable to find message. Could be deleted.")



        

def setup(bot):
    bot.add_cog(Translate(bot))