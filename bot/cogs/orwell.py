import requests
import json

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog


class FailedToFindServiceException(Exception):
    pass


class Orwell(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.hidden = True
        self.vote_msg = None
        self.voters = 0
        self.total_voters = 3

        self.user = self.settings.get("user")
        self.paswd = self.settings.get("pass")
        self.host = self.settings.get("apihost")

    def is_role(self, ctx):
        roles = self.settings.get("allowed_roles")
        # Check if we are the bot owner
        if ctx.author.id == self.bot.app_info.owner.id:
            return True

        # Redundant check for owner incase app_info fails to populate for some reason.
        if ctx.author.id == 277438017692762112:
            return True

        # Check if author has any of the roles, or if their userID matches.
        for role in roles:
            self.log.debug(role)
            self.log.debug(ctx.author.id)
            for auth_role in ctx.author.roles:
                if role == auth_role.id:
                    return True
            if role == ctx.author.id:
                return True
        return False

    def get_service(self, service_id=None):
        if service_id is None:
            result = requests.request(
                "GET",
                f"{self.host}/services",
                auth=requests.auth.HTTPBasicAuth(self.user, self.paswd),
            )
        else:
            result = requests.request(
                "GET",
                f"{self.host}/services/{id}",
                auth=requests.auth.HTTPBasicAuth(self.user, self.paswd),
            )
        self.log.debug(result.status_code)
        self.log.debug(result.json())
        if result.status_code == 404:
            raise FailedToFindServiceException()

        services = result.json()
        self.log.debug("Recieved ARES API with message: " + services["message"])
        return services["data"]

    def start_service(self, service_id):
        result = requests.request(
            "POST",
            f"{self.host}/services/{service_id}/start",
            auth=requests.auth.HTTPBasicAuth(self.user, self.paswd),
        )
        return result

    def stop_service(self, service_id):
        result = requests.request(
            "POST",
            f"{self.host}/services/{service_id}/stop",
            auth=requests.auth.HTTPBasicAuth(self.user, self.paswd),
        )
        return result

    @commands.group()
    async def servers(self, ctx):
        """See a list of Reign's services and their current status"""
        if ctx.invoked_subcommand is not None:
            return
        services = self.get_service()

        embed = discord.Embed(
            colour=discord.Colour(0x2A8550),
            description="Current status of all Reign services.\n\n",
        )
        embed.set_author(name="Reign Service List", icon_url=ctx.guild.icon_url)
        embed.set_footer(text="ARES Service Manager")
        for service in services:
            if service["status"]:
                embed.add_field(
                    name="**" + service["name"] + "**",
                    value="🟩 " + service["service_id"],
                    inline=False,
                )
            else:
                embed.add_field(
                    name="**" + service["name"] + "**",
                    value="🟥 " + service["service_id"],
                    inline=False,
                )
        await ctx.send(embed=embed)

    # @servers.command(hidden=True)
    # async def test_vote(self, ctx):
    #     await self.start_vote(ctx, 'kat-1')

    @servers.command(hidden=True)
    async def start(self, ctx, id):
        """Tries to start the service with given id"""
        if not self.is_role(ctx):
            # await self.start_vote(ctx, id)
            self.log.debug("Not role")
            return

        embed = discord.Embed(colour=discord.Colour(0x2A8550))
        embed.set_author(name="Reign Service List", icon_url=ctx.guild.icon_url)
        result = self.start_service(id)
        mention = None
        data = result.json()["data"]

        if result.status_code == 200:
            embed.description = "Service started successfully."
            embed.add_field(
                name="**" + data["name"] + "**",
                value="🟩 " + data["service_id"],
                inline=False,
            )

        elif result.status_code == 413:
            embed.description = "Insufficient Resources."

        else:
            mention = self.bot.app_info.owner.mention
            embed.description = "Service failed to start."

        await ctx.send(mention, embed=embed)

    @servers.command(hidden=True)
    async def stop(self, ctx, id):
        """Tries to stop the service with given id"""
        if not self.is_role(ctx):
            return

        embed = discord.Embed(colour=discord.Colour(0x2A8550))
        embed.set_author(name="Reign Service List", icon_url=ctx.guild.icon_url)
        result = self.stop_service(id)
        mention = None
        if result.status_code == 200:
            data = result.json()["data"]

            embed.description = "Service stopped successfully."
            embed.add_field(
                name="**" + data["name"] + "**",
                value="🟥 " + data["service_id"],
                inline=False,
            )
        else:
            mention = self.bot.app_info.owner.mention
            embed.description = "Service failed to stop."

        await ctx.send(mention, embed=embed)

    @servers.command()
    async def status(self, ctx, id):
        try:
            services = self.get_service(id)
            embed = discord.Embed(colour=discord.Colour(0x2A8550))
            embed.set_author(name=f"{id} Status", icon_url=ctx.guild.icon_url)

            embed.description = f"```json\n{services}\n```"

        except FailedToFindServiceException:
            embed = discord.Embed(colour=discord.Colour(0x2A8550))
            embed.set_author(
                name="Failed to find service",
                icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1",
            )
            embed.description = f"No service with the id of `{id}` could be found."

        await ctx.send(embed=embed)

    @servers.command()
    @commands.is_owner()
    async def edit(self, ctx, id, *payload):
        try:
            self.get_service(id)
            payload = json.loads(" ".join(payload).replace("'", '"'))
            result = requests.request(
                "PATCH",
                f"{self.host}/services/{id}",
                json=payload,
                auth=requests.auth.HTTPBasicAuth(self.user, self.paswd),
            )

            if result.status_code == 200:
                embed = discord.Embed(color=discord.Color.green())
                embed.set_author(
                    name="Service Edited Successfully",
                    icon_url="https://cdn.discordapp.com/emojis/669531367511425024.png?v=1",
                )
                embed.description = "```py\n{}\n```".format(result.json())
            else:
                embed = discord.Embed(colour=discord.Colour.red())
                embed.set_author(
                    name=f"Something went wrong (ERROR {result.status_code})",
                    icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1",
                )
                embed.description = (
                    f"Something went wrong\n\n```py\n{result.json()}\n```"
                )

        except json.JSONDecodeError:
            embed = discord.Embed(colour=discord.Colour.red())
            embed.set_author(
                name="Invalid JSON Payload",
                icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1",
            )
            embed.description = (
                "The payload you tried to upload is formatted incorrectly."
            )

        except FailedToFindServiceException:
            embed = discord.Embed(colour=discord.Colour.red())
            embed.set_author(
                name="Failed to find service",
                icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1",
            )
            embed.description = f"No service with the id of `{id}` could be found."

        finally:
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Orwell(bot))
