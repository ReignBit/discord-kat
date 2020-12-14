from discord.ext import commands
import discord

from bot.utils.extensions import KatCog
import bot.utils.permissions as permissions


class Welcomer(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        raise DeprecationWarning("This Cog has been disabled. Needs SQL Rework added.")

    def generate_embed(self, welcome_data, user, guild):
        if len(welcome_data) > 0:
            welcome_msg = welcome_data[0]
            if welcome_msg['channel_id']:
                embed = discord.Embed(description=welcome_msg['text'], color=discord.Color.blue())
                embed.title = f"Welcome to {guild.name}"
                embed.set_image(url=welcome_msg['image'])
                embed.set_author(name=user.display_name, icon_url=user.avatar_url)
                return embed
        return None


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.sql.custom_query("INSERT INTO `cog_welcomer_guild_data`(`guild_id) VALUES ({})".format(guild.id))
        self.bot.sql.commit()

    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        welcome_msg = self.bot.sql.custom_query("SELECT * FROM `cog_welcomer_guild_data` WHERE `guild_id` = {}".format(guild.id), doesReturn=True)
        self.log.debug(welcome_msg)
        if len(welcome_msg) > 0:
            embed = self.generate_embed(welcome_msg, member, guild)
            await guild.get_channel(welcome_msg[0]['channel_id']).send(member.mention, embed=embed)

    @commands.group()
    async def welcome(self, ctx):
        """Tests the welcome message"""
        if not permissions.has_permission(self.bot, ctx.author, ctx.channel, "Administrator"):
            await ctx.send(self.get_response("common.error.permisson_error", ctx=ctx))
            return
        if ctx.invoked_subcommand is not None:
            return
        welcome_msg = self.bot.sql.custom_query("SELECT * FROM `cog_welcomer_guild_data` WHERE `guild_id` = {}".format(ctx.guild.id), doesReturn=True)
        self.log.debug(welcome_msg)
        if len(welcome_msg) > 0:
            embed = self.generate_embed(welcome_msg, ctx.author, ctx.guild)
            try:
                await ctx.guild.get_channel(welcome_msg[0]['channel_id']).send(ctx.author.mention, embed=embed)
            except AttributeError:
                await ctx.send(":x: | Invalid channel set.")
        
        else:
            self.bot.sql.custom_query("INSERT INTO `cog_welcomer_guild_data` (`guild_id`) VALUES ({})".format(ctx.guild.id))
            self.bot.sql.commit()
            await ctx.send("A welcome message has not been set!\n```\n1)$welcome channel <#>    To set the welcoming channel\n2)$welcome text <text>   To set the welcome text\n3)$welcome image <link to image>    To set a welcoming image.```")


    @welcome.command()
    async def enable(self, ctx, value: bool):
        """Enables/Disables showing the welcome message to new users."""
        self.bot.sql.custom_query('UPDATE `cog_welcomer_guild_data` SET `enabled`={} WHERE `guild_id` = {}'.format(value, ctx.guild.id))
        self.bot.sql.commit()
        await ctx.send(self.bot.sql.custom_query("SELECT `enabled` FROM cog_welcomer_guild_data WHERE guild_id = {}".format(ctx.guild.id), doesReturn=True))


    @welcome.command()
    async def channel(self, ctx, channel_id: discord.TextChannel=None):
        """Set the channel where the welcome message will show"""
        if channel_id == None:
            await ctx.send(self.bot.sql.custom_query("SELECT `channel_id` FROM `cog_welcomer_guild_data` WHERE `guild_id` = {}".format(ctx.guild.id), doesReturn=True))
            return

        self.bot.sql.custom_query('UPDATE `cog_welcomer_guild_data` SET `channel_id`={} WHERE `guild_id` = {}'.format(channel_id.id, ctx.guild.id))
        self.bot.sql.commit()
        await ctx.send(self.bot.sql.custom_query("SELECT `channel_id` FROM cog_welcomer_guild_data WHERE guild_id = {}".format(ctx.guild.id), doesReturn=True))



    @welcome.command()
    async def text(self, ctx, *text):
        """Sets the welcome text"""
        if len(text) == 0:
            await ctx.send(self.bot.sql.custom_query("SELECT `text` FROM `cog_welcomer_guild_data` WHERE `guild_id` = {}".format(ctx.guild.id), doesReturn=True))
        else:
            text = " ".join(text)
            #self.log.debug(text)
            self.bot.sql.custom_query('UPDATE `cog_welcomer_guild_data` SET `text`="{}" WHERE `guild_id` = {}'.format(text, ctx.guild.id))
            self.bot.sql.commit()
            await ctx.send(self.bot.sql.custom_query("SELECT `text` FROM cog_welcomer_guild_data WHERE guild_id = {}".format(ctx.guild.id), doesReturn=True))

    @welcome.command()
    async def image(self, ctx, link=None):
        """Sets the welcome image"""
        if link == "none":
            self.bot.sql.custom_query('UPDATE `cog_welcomer_guild_data` SET `image`=NULL WHERE `guild_id` = {}'.format(ctx.guild.id))
            self.bot.sql.commit()
            await ctx.send("Removed the welcome image!")
            return
        elif link == None:
            await ctx.send(self.bot.sql.custom_query("SELECT `image` FROM cog_welcomer_guild_data WHERE guild_id = {}".format(ctx.guild.id), doesReturn=True))
            return


        self.bot.sql.custom_query('UPDATE `cog_welcomer_guild_data` SET `image`="{}" WHERE `guild_id` = {}'.format(link, ctx.guild.id))
        self.bot.sql.commit()
        await ctx.send(self.bot.sql.custom_query("SELECT `image` FROM cog_welcomer_guild_data WHERE guild_id = {}".format(ctx.guild.id), doesReturn=True))


def setup(bot):
    bot.add_cog(Welcomer(bot))
