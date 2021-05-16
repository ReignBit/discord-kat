from discord.ext import commands
import discord

from bot.utils.extensions import KatCog
from bot.utils.models import Guild
from bot.utils import constants


def is_subcommand():
    def predicate(ctx):
        return ctx.invoked_subcommand is None

    return commands.check(predicate)


class Configurator(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    def _config_embed_builder(self, ctx, command_path, fields, cog_name="Kat"):
        embed = discord.Embed()
        embed.color = constants.Color.invisible
        embed.set_author(name="{} Config for {}".format(cog_name, ctx.guild.name))
        embed.set_footer(
            text="Use `{}` to view and change settings.".format(
                ctx.prefix + command_path
            )
        )

        for field in fields:
            embed.add_field(
                name=field[0],
                value="`" + ctx.prefix + command_path + " " + field[1] + "`",
                inline=True,
            )
        return embed

    @commands.has_permissions(manage_guild=True)
    @commands.group()
    async def config(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        fields = [
            (":exclamation: Prefix", "prefix"),
            (":star: Levels", "level"),
            (":shield: Admin", "admin"),
            (":gear: Roles", "roles"),
        ]

        embed = self._config_embed_builder(ctx, "config", fields)
        await ctx.send(embed=embed)

    @config.group()
    async def roles(self, ctx):
        """Lists the current Administrator and Moderator roles for the guild"""

        if ctx.invoked_subcommand is not None:
            return

        guild = await Guild.get(ctx.guild.id, self.bot.session)
        roles = guild.get_setting("roles")
        self.log.debug(roles)
        self.log.debug(type(roles))

        mod_roles = []
        admin_roles = []

        # moderation role resolution
        for role in roles["moderators"]:
            try:
                role_obj = discord.utils.get(ctx.guild.roles, id=int(role))
            except ValueError:  # we are dealing with a role name...
                role_obj = discord.utils.get(ctx.guild.roles, name=role)

            if role_obj is not None:
                mod_roles.append(role_obj)

        # administrator role resolution
        for role in roles["administrators"]:
            try:
                role_obj = discord.utils.get(ctx.guild.roles, id=int(role))
            except ValueError:  # we are dealing with a role name...
                role_obj = discord.utils.get(ctx.guild.roles, name=role)

            if role_obj is not None:
                admin_roles.append(role_obj)

        mod_string = "\n".join([mod.name for mod in mod_roles])
        admin_string = "\n".join([admin.name for admin in admin_roles])

        if mod_string == "":
            mod_string = "`No Roles Added`"
        if admin_string == "":
            admin_string = "`No Roles Added`"

        await ctx.send(
            embed=discord.Embed.from_dict(
                self.get_embed(
                    "configurator.embeds.roles.list",
                    guild=ctx.guild.name,
                    mod_roles=mod_string,
                    admin_roles=admin_string,
                    prefix=ctx.prefix,
                )
            )
        )

    def _add_to_moderator(self, role: discord.Role, guild: Guild):
        mods = guild.get_setting(constants.GuildSettings.moderators)
        mods.append(role.id)
        guild.set_setting(constants.GuildSettings.moderators, mods)

    def _add_to_admin(self, role: discord.Role, guild: Guild):
        mods = guild.get_setting(constants.GuildSettings.admins)
        mods.append(role.id)
        guild.set_setting(constants.GuildSettings.admins, mods)

    @roles.command()
    async def add(self, ctx, role: discord.Role, group: str):
        self.log.debug("add")
        self.log.debug(role.name)
        guild = await Guild.get(ctx.guild.id, self.bot.session)

        if group == "mod":
            self._add_to_moderator(role, guild)
        elif group == "admin":
            self._add_to_admin(role, guild)

        await guild.save(self.bot.session)

        await ctx.send(
            "Set {} to {}".format(
                role.name,
                {"mod": "Moderator", "admin": "Administrator"}.get(group, "Unknown"),
            )
        )

    @config.command()
    async def prefix(self, ctx, new_prefix=None):
        if new_prefix is None:
            await ctx.send(
                self.get_response(
                    "configurator.command.prefix_none",
                    curr_prefix=(await self.bot.get_custom_prefix(self.bot, ctx))[2],
                )
            )
        else:
            if new_prefix not in constants.Configurator.banned_prefix_chars:
                # [name_mention, nickname_mention, prefix]
                old = (await self.bot.get_custom_prefix(self.bot, ctx))[2]
                guild = await Guild.get(ctx.guild.id, self.bot.session)
                self.log.debug(type(guild.settings))
                guild.prefix = new_prefix

                self.log.debug(guild.to_dict())
                await guild.save(self.bot.session)

                await ctx.send(
                    self.get_response(
                        "configurator.command.prefix_change",
                        old_prefix=old,
                        new_prefix=new_prefix,
                    )
                )
            else:
                await ctx.send(
                    self.get_response(
                        "configurator.error.prefix_banned", prefix=new_prefix
                    )
                )

    @config.group()
    async def level(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        guild = await Guild.get(ctx.guild.id, self.bot.session)
        fields = [
            (
                ":eight_spoked_asterisk:  XP Multiplier: "
                f"{guild.ensure_setting(constants.GuildSettings.level_xp_multi, 1.0)}",
                "multi <float>",
            ),
            (
                f":snowflake: Freeze Status: \
                {guild.ensure_setting(constants.GuildSettings.level_freeze, False)}",
                "freeze",
            ),
        ]
        embed = self._config_embed_builder(ctx, "config level", fields)
        await ctx.send(embed=embed)

    @level.command()
    async def freeze(self, ctx):
        guild = await Guild.get(ctx.guild.id, self.bot.session)
        new = guild.set_setting(
            constants.GuildSettings.level_freeze,
            not guild.get_setting(constants.GuildSettings.level_freeze),
        )
        await guild.save(self.bot.session)
        if new:
            await ctx.send(self.get_response("configurator.config.level.freeze"))
        else:
            await ctx.send(self.get_response("configurator.config.level.unfreeze"))

    @level.command()
    async def multi(self, ctx, mul: float):
        mul = min(max(0.0, mul), 2.5)

        guild = await Guild.get(ctx.guild.id, self.bot.session)
        guild.set_setting(constants.GuildSettings.level_xp_multi, mul)
        await guild.save(self.bot.session)
        await ctx.send(
            self.get_response("configurator.config.level.multi_success", multi=mul)
        )

    @multi.error
    async def multi_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument `multi`")
        if isinstance(error, TypeError):
            await ctx.send(self.get_response("configurator.error.level_multi_invalid"))


def setup(bot):
    bot.add_cog(Configurator(bot))
