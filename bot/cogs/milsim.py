from requests import get
import datetime
import os
import re

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog


class Milsim(KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.hidden = True

        self.notify_list = []
        self.write_list = []
        self.announcement_message = discord.Message
        self.operation_name = self.settings['operation_name']
        self.test_mode = False
        self.is_milsim_scheduled = False

    #TODO: $milsim <date> 7:0 works when should be invalid.
    #TODO: Also, creating 2 milsim events right after each other whithout calling $m n will break notifications.

    @commands.command(aliases=['m'], hidden=True)
    async def milsim(self, ctx, date="", time=""):
        if date == "cancel" or date == "c":
            self.notify_list = []
            self.write_list = []
            self.log.info("Milsim announcement has been cancelled.")

            embed = discord.Embed(colour=discord.Colour(0xf1c40f),
                                  description="This milsim session has been cancelled.")

            self.is_milsim_scheduled = False
            await self.announcement_message.channel.send("@here", embed=embed)
            await self.announcement_message.delete()
            
        if date == "" or time == "":
            await ctx.send("You have not specified a date and/or time. `$milsim <date DD/MM/YY> <time HH:MM UTC>`")
            return
        else:
            
            if self.is_milsim_scheduled:
                await ctx.send("A milsim session has already been scheduled. To start a new one, you must first cancel the existing session.\n`$milsim cancel`")

            try:
                datetime.datetime.strptime(date, "%d/%m/%y")
            except ValueError as err:
                try:
                    assert int(date)
                    date = datetime.datetime.today() + datetime.timedelta(days=int(date))
                    date = "{}/{}/{}".format(date.day, date.month, date.year)
                except Exception as err:
                    self.log.warn(err)
                    await ctx.send(date + " is in an invalid format. `dd/mm/yy` is the accepted format.")
                    return

            if len(time.split(':')[1]) is not 2:
                await ctx.send(time + "is an invalid format. HH:MM is the accepted format.")
                return

            string = "**" + date + " @ " + time + "**"
            time = time.replace(":", "%3A")
            time += "%20UK"
            ip = get('https://api.ipify.org').text

            embed = discord.Embed(colour=discord.Colour(0xf1c40f),
                                  description="There will be a Milsim session hosted at the following time:\n\n **{0}** ***UK TIME***\n\nIn your timezone, this is:\nhttps://www.google.com/search?q={1} "
                                              "\n\nPlease ensure you have the latest mod preset installed and updated.\n Check [#modpack-support](https://discord.com/channels/485578455795367967/528565872755736586) for help."
                                              "\n\nIf you are able to attend, please react with   <:white_check_mark:613273290374643723>"
                                              "\nIf you are unable to attend, please react with <:x:615775632139223061>"
                                  .format(string, time))
            embed.set_author(name="Milsim Session Announcement")
            embed.set_footer(text="TS IP: ||{0}|| | {1}".format(ip, self.operation_name))

            self.is_milsim_scheduled = True

            guild = discord.utils.get(self.bot.guilds, id=485578455795367967)
            channel = discord.utils.get(guild.channels, id=530314685065461760)

            await channel.send("@everyone", embed=embed)


            async for message in channel.history(limit=1):      # change this in prod stage
                self.announcement_message = message

                await self.announcement_message.add_reaction("✅")
                await self.announcement_message.add_reaction("❌")


    @commands.command(hidden=True)
    async def milsim_getaddons(self, ctx):
        mods = []
        for file in os.listdir("C:\\FTP\\game_servers\\arma"):
            if file.startswith("@"):
                mods.append(file)

        await ctx.send(";".join(mods))

    @commands.command()
    async def milsim_testmode(self, ctx):
        self.test_mode = not self.test_mode
        await ctx.send("self.test_mode = " + str(self.test_mode))

    @commands.command(hidden=True)
    async def milsim_setmods(self, ctx, file_name):
        """Fetches File file_name from resources/milsim_modpacks
            File should be a .html with the generated Arma 3 Modpack Export page.
        """

        with open('resources/'+file_name+".html", 'r') as f:
            page = f.read()
            data = re.match(r"(?<=>)(.*)(?=<)", page)
            print(data)


def setup(bot):
    bot.add_cog(Milsim(bot))
