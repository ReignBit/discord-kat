# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
import utilities.KatCog as KatCog

def is_subcommand():
    def predicate(ctx):
        return ctx.invoked_subcommand == None
    return commands.check(predicate)

class Configurator(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    def _config_embed_builder(self, ctx, command_path, fields, cog_name="Kat"):
        embed = discord.Embed()
        embed.set_author(name="{} Config for {}".format(cog_name, ctx.guild.name))
        embed.set_footer(text="Use `{}` to view and change settings.".format(ctx.prefix + command_path))

        for field in fields:
            embed.add_field(name=field[0], value="`" + ctx.prefix + command_path + " " + field[1] + "`", inline=True)
        return embed


    @commands.has_permissions(manage_guild=True)
    @commands.group()
    async def config(self, ctx):
        if ctx.invoked_subcommand is not None: return

        fields = [
                (":exclamation: Prefix", "prefix"),
                (":star: Levels", "level"),
                (":shield: Admin", "admin")
        ]

        embed = self._config_embed_builder(ctx, "config", fields)
        await ctx.send(embed=embed)


    @config.command()
    async def prefix(self, ctx, new_prefix=None):
        if new_prefix is None:
            await ctx.send(self.get_response("configurator.command.prefix_none", curr_prefix=self.bot.get_custom_prefix(self.bot, ctx)[2]))
        else:
            if new_prefix not in self.settings['banned_prefix_chars']:
                old = self.bot.get_custom_prefix(self.bot, ctx)[2]  #[name_mention, nickname_mention, prefix]
                self.sql.edit_prefix(ctx.guild.id, new_prefix)

                await ctx.send(self.get_response("configurator.command.prefix_change", old_prefix=old, new_prefix=new_prefix))
            else:
                await ctx.send(self.get_response("configurator.error.prefix_banned", prefix=new_prefix))

    @config.group()
    async def level(self, ctx):
        if ctx.invoked_subcommand is not None: return

        guild = self.sql.query("KatGuild").get(ctx.guild.id)
        fields = [
            (f":eight_spoked_asterisk:  XP Multiplier: {guild.ensure_setting('settings.level.xp_multi', 1.0)}", "multi <float>"),
            (f":snowflake: Freeze Status: {guild.ensure_setting('settings.level.freeze', False)}", "freeze")
        ]
        embed = self._config_embed_builder(ctx, "config level", fields)
        await ctx.send(embed=embed)

    @level.command()
    async def freeze(self, ctx):
        guild = self.sql.query("KatGuild").get(ctx.guild.id)
        new = guild.set_setting("settings.level.freeze", not guild.get_setting('settings.level.freeze'))
        if new:
            await ctx.send(self.get_response("configurator.config.level.freeze"))
        else:
            await ctx.send(self.get_response("configurator.config.level.unfreeze"))


    @level.command()
    async def multi(self, ctx, mul):
        guild = self.sql.query("KatGuild").get(ctx.guild.id)
        if type(mul) is not float:
            raise TypeError
        if mul < 0.0 or mul > 2.5:
            raise TypeError
        guild.set_setting("settings.level.xp_multi", mul)
        await ctx.send(self.get_response("configurator.config.level.multi_success", multi=mul))

    @multi.error
    async def multi_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument `multi`")
        if isinstance(error, TypeError):
            await ctx.send(self.get_response("configurator.error.level_multi_invalid"))




def setup(bot):
    bot.add_cog(Configurator(bot))