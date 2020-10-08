import discord
import discord.errors
import discord.ext.commands as commands
import json
import asyncio
import time

import utilities.KatCog as KatCog
import utilities.permissions as permissions
import utilities.utils as utils

class Admin(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
    
    # Moved to cogs/moderation/misc.py
    # @commands.command()
    # async def clear(self, ctx, amount=2):
    #     """[Manage Messages] Clear messages in a text channel"""
    #     if not permissions.has_permission(self.bot, ctx.author, ctx.channel, "manage_messages"):
    #         await ctx.send(self.get_response('common.error.permission_error'))
    #         return
    #     amount += 1
    #     if amount > 100:
    #         amount = 100

    #     messages = await ctx.channel.history(limit=amount).flatten()
    #     try:
    #         await ctx.channel.delete_messages(messages)
    #     except discord.errors.HTTPException as e:
    #         self.log.warn("Failed to delete message: " + str(e))
    #         await ctx.send(self.get_response("admin.error.clear_fail"), delete_after=10)
    #         return
    #     await ctx.send(self.get_response("admin.command.clear", amount=amount-1), delete_after=10)
    
    @commands.group()
    async def config(self, ctx):
        """[Administrator] Change the guild's config for Kat"""
        if not permissions.has_permission(self.bot, ctx.author, ctx.channel, "Administrator"):
            await ctx.send(self.get_response("common.error.permission_error"))
            return

        if ctx.invoked_subcommand is not None:
            return

        prefix = "`" + self.bot.get_custom_prefix(self.bot, ctx)[2] + "config "

        embed = discord.Embed(description="Use the format {}<option>` to view their setting.".format(prefix), color=7800635)
        embed.set_author(name="Kat's Config for {}".format(ctx.guild.name), icon_url=ctx.guild.icon_url)

        # prefix setting
        embed.add_field(name=":exclamation: Prefix", value=prefix + "prefix`")

        # Levels settings
        if 'Level' in self.bot.cogs.keys():
            embed.add_field(name=":star: Levels", value=prefix + "level`")

        #admin settings
        if 'Admin' in self.bot.cogs.keys():
            embed.add_field(name=":shield: Admin", value=prefix + "admin`")

        await ctx.send(embed=embed)


    @config.command()
    async def prefix(self, ctx, new_prefix=None):
        if new_prefix is None:
            await ctx.send(self.get_response("admin.command.prefix_none", curr_prefix=self.bot.get_custom_prefix(self.bot, ctx)[2]))
        else:
            if new_prefix not in self.settings['configurator']['banned_prefix_chars']:
                # we need to access the third one since commands.when_mentioned_or() adds the name mention and nickname mention prefixes.
                old = self.bot.get_custom_prefix(self.bot, ctx)[2]
                self.sql.edit_prefix(ctx.guild.id, new_prefix)
                await ctx.send(self.get_response("admin.command.prefix_change", old_prefix=old, new_prefix=new_prefix))
            else:
                await ctx.send(self.get_response("admin.error.prefix_banned", prefix=new_prefix))


    @config.group()
    async def level(self, ctx):
        """[Administrator] Change the guild's level config for Kat"""
        if not permissions.has_permission(self.bot, ctx.author, ctx.channel, "Administrator"):
            await ctx.send(self.get_response("common.error.permission_error"))
            return
        if ctx.invoked_subcommand is not None:
            return

        guild_settings = self.sql.ensure_exists("KatGuild", guild_id=ctx.guild.id).settings
        guild_settings = guild_settings['level']

        # embed creation
        prefix = "`" + self.bot.get_custom_prefix(self.bot, ctx)[2] + "config level "
        embed = discord.Embed(description="Use the format {}<option>` to view their setting.".format(prefix), color=7800635)
        embed.set_author(name="Level Config for {}".format(ctx.guild.name), icon_url=ctx.guild.icon_url)
        embed.add_field(name=":eight_spoked_asterisk:  XP Multiplier: {}".format(guild_settings['xp_multi']), value=prefix + "multiplier <float>`")
        embed.add_field(name=":snowflake: Freeze Status: {}".format(guild_settings['freeze']), value=prefix + "freeze <true/false>`")

        await ctx.send(embed=embed)

    @level.command()
    async def freeze(self, ctx, freeze_status):
        guild_settings = self.sql.ensure_exists("KatGuild", guild_id=ctx.guild.id).settings
        guild_settings = guild_settings['level']
        try:
            guild_settings = bool(freeze_status)
        except TypeError:
            await ctx.send("Must be `True` or `False`")
        _ = "freeze" if guild_settings['freeze'] else "unfreeze"
        embed = discord.Embed(description=self.get_response("admin.config.level.{}".format(_)), color=7800635)
        embed.set_author(name="Level Freeze Status for {}".format(ctx.guild.name), icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Admin(bot))
