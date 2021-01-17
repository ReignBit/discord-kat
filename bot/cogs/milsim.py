import datetime

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog


class Milsim(KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.hidden = True

        self.notify_list = []
        self.write_list = []
        self.announcement_message: discord.Message = None
        self.test_mode = False
        self.is_session_scheduled = False

    # TODO: $milsim <date> 7:0 works when should be invalid.
    # TODO: Also, creating 2 milsim events right after each
    # other whithout calling $m n will break notifications.

    @commands.command(aliases=["m", "milsim", "announce"])
    async def session(self, ctx, date="", time=""):
        if date == "cancel" or date == "c":
            self.notify_list = []
            self.write_list = []
            self.log.info("Announcement has been cancelled.")

            embed = discord.Embed(
                colour=discord.Colour(0xF1C40F),
                description="This session has been cancelled.",
            )

            self.is_session_scheduled = False
            await self.announcement_message.channel.send("@here", embed=embed)
            await self.announcement_message.delete()

        if date == "" or time == "":
            await ctx.send(self.get_response("command.session.blank"))
            return
        else:

            if self.is_session_scheduled:
                await ctx.send(self.get_response("command.session.already"))

            try:
                datetime.datetime.strptime(date, "%d/%m/%y")
            except ValueError:
                try:
                    assert int(date)
                    date = datetime.datetime.today() + datetime.timedelta(
                        days=int(date)
                    )
                    date = "{}/{}/{}".format(date.day, date.month, date.year)
                except Exception as err:
                    self.log.warn(err)
                    await ctx.send(
                        self.get_response("command.session.invalid", date=date)
                    )
                    return

            if len(time.split(":")[1]) != 2:
                await ctx.send(
                    self.get_response("command.session.invalid_time", time=time)
                )
                return

            string = "**" + date + " @ " + time + "**"
            time = time.replace(":", "%3A")
            time += "%20UK"

            embed = discord.Embed(
                colour=discord.Colour(0xF1C40F),
                description="There will be a Milsim session hosted at the following time:\n\n "
                f"{string} ***UK TIME***\n\nIn your timezone, this is:\n"
                f"https://www.google.com/search?q={time} "
                "\n\nPlease ensure you have the latest mod preset installed and updated.\n Check "
                "[#modpack-support]" +
                "(https://discord.com/channels/485578455795367967/528565872755736586) for help."
                "\n\nIf you are able to attend, please react with   "
                "<:white_check_mark:613273290374643723>"
                "\nIf you are unable to attend, please react with <:x:615775632139223061>",
            )
            embed.set_author(name="Milsim Session Announcement")

            self.is_session_scheduled = True

            guild = discord.utils.get(self.bot.guilds, id=485578455795367967)
            channel = discord.utils.get(guild.channels, id=530314685065461760)

            await channel.send("@everyone", embed=embed)

            async for message in channel.history(limit=1):  # change this in prod stage
                self.announcement_message = message

                await self.announcement_message.add_reaction("✅")
                await self.announcement_message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Milsim(bot))
