# discord specific imports
from discord.ext import commands
import discord

# python imports
import datetime
import asyncio
import requests
import json
import random
import os

import sqlalchemy

# kat specific imports
import utilities.KatCog as KatCog
from utilities.KatClasses import KatUser, KatMember, KatGuild, null

class Birthday(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.hidden = True

    # @commands.Cog.listener()
    # async def on_kat_day_event(self):
    #     self.log.info("Performing daily birthday checks")
        
    #     # select all those who have birthdays (NOT NULL)
    #     birthday_users = self.bot.sql_session.query(KatUser).filter(KatUser.birthday != null).all()

    #     current_date = datetime.datetime.date(datetime.datetime.now())  #Datetime Obj (month-day)
    #     for user in birthday_users:
    #         # if today is birthday
    #         if user.birthday.month == current_date.month and user.birthday.day == current_date.day:
    #             age = datetime.datetime.now().year - user.birthday.year
    #             # if user's DB age is not actual age
    #             if user.birthday_years != age:
    #                 # celebrate Bday
    #                 user.birthday_years = age
    #                 self.bot.sql_session.commit()
    #                 await self.send_birthday(user.user_id, user.birthday)


    async def _get_gif(self, search_query):
        """ Sends API call to tenor, for search_query. Returns a random gif from result."""
        r = requests.get(
        "https://api.tenor.com/v1/search?q={}&key=4KDPUPUVOVRW&limit=20&anon_id=312ced313baf42079d1588df7e032c69".format(search_query))
        if r.status_code == 200:
            
            # load the GIFs using the urls for the smaller GIF sizes
            raw = json.loads(r.content)['results']
            _ = raw[random.randrange(0, len(raw))]['media'][0]['gif']['url']
            
            while _ == "https://media.tenor.com/images/4bdc2faacb4abfc4fc6f9c8b759cd583/tenor.gif":
                _ = raw[random.randrange(0, len(raw))]['media'][0]['gif']['url']
            return _


    async def send_birthday(self, user_id, birthday: datetime):
        """Sends a birthday message to VVV channel"""
        # Kingdom of Reign / rm-chat
        #guild = discord.utils.get(self.bot.guilds, id=311612862554439692)
        #channel = discord.utils.get(guild.channels, id=432214639305162752)

        # KAT DEV SERVER / KAT-REPORTS TO TEST.
        guild = discord.utils.get(self.bot.guilds, id=438542169855361025)
        channel = discord.utils.get(guild.channels, id=495410881140621312)        
        
        
        age_map = {
            0:'th',
            1:'st',
            2:'nd',
            3:'rd',
            4:'th',
            5:'th',
            6:'th',
            7:'th',
            8:'th',
            9:'th',
        }
        
        # age = str(datetime.datetime.now().year - birthday.year)
        # age = age + age_map[int(age[-1:])]
        
        embed = discord.Embed(title=":confetti_ball: {}'s Birthday! :confetti_ball: ".format(guild.get_member(user_id).display_name),
                    colour=discord.Colour(0x739e85), description="Happy birthday to {}".format(guild.get_member(user_id).mention))
        embed.set_image(url=await self._get_gif("anime%20birthday"))
        embed.set_footer(text="Lots of love, from Bit and Kat xxx")
        await channel.send(embed=embed)


    @commands.command()
    async def bday(self, ctx):
        embed = discord.Embed(title=":confetti_ball: Alfie ❖'s Birthday! :confetti_ball: ",
                    colour=discord.Colour(0x739e85), description="everyone say Happy Birthday to Alfie ❖!")
        embed.set_image(url=await self._get_gif("anime%20birthday"))
        embed.set_footer(text="Lots of love, from Bit and Kat xxx")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = discord.utils.get(self.bot.guilds, id=311612862554439692)
        
        if (type(message.channel) is discord.channel.DMChannel and message.author in guild.members and message.author != self.bot.user):
            self.log.debug("Messaged from DMs")
            if message.content.startswith("BDAY "):
                # BDAY <anytyhing> (The date the user sent to Kat)
                raw_date = message.content.split(" ")[1]

                #format date into a datetime Obj for uniform formatting
                birthday = datetime.datetime.strptime(raw_date, "%Y-%m-%d") #YYYY-mm-dd         
                birthday_str = "{}-{}-{}".format(birthday.year, birthday.month, birthday.day)               
                
                user = self.bot.sql_session.query(KatUser).get(message.author.id)
                user.birthday = birthday_str
                self.bot.sql_session.commit()
                
                self.log.info("Updated Birthday information for [{}|{}]".format(message.author.name, message.author.id))
                await message.channel.send("Updated your Birthday information!")


def setup(bot):
    bot.add_cog(Birthday(bot))