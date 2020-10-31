import hashlib
import asyncio
import time
import os
import sys
import traceback
import requests
import json
import inspect
import re

import discord
from discord.ext import commands

import psutil

import utilities.KatCog as KatCog
import utilities.utils as utils
import utilities.permissions as perms
import utilities.KatClasses as KatClasses

#TODO: This definitely needs chopping up and re-writing
class Core(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.hidden = True
        ## Checksum Generation
        self.checksums = {}
        self.checksum_generation()

        self.bot.remove_command('help')

        ## self.output used for $kat exec. Need a better way to do this.
        self.output = None


    def collect_metrics(self):
        return {
            "Python Version": sys.version,
            "Discord-py Version": discord.__version__,
            "CPU Usage": utils.get_sys_cpu_usage(),
            "Mem Usage": utils.get_sys_mem_usage(),
            "Kat Mem Usage": utils.get_mem_usage(),
            "Loaded Cogs": ", ".join(self.bot.cogs.keys()),
            "Last exec_output": self.output
        }

    def checksum_generation(self):
        self.log.info("Generating checksums...")
        self.checksums = utils.generate_checksums(self.settings['ensure_file_integrity'])
        self.checksum_checks = 10
        self.modified = 0
        self.log.info("Generated checksums for core files.")


    


    @commands.Cog.listener()
    async def on_kat_minute_event(self):      
        checksums_now = utils.generate_checksums(self.settings['ensure_file_integrity'])
        if checksums_now != self.checksums:
            self.log.warning("CHECKSUM CHECK FAILED FOR AT LEAST 1 PROTECTED FILE [{}/{}]".format(10 - self.checksum_checks, 10))
            self.modified = 1
            self.bot.is_restart_scheduled = 1

        if self.modified and self.bot.is_restart_scheduled and not self.bot.maintenance_mode:
            game = discord.Game("Restart scheduled")
            await self.bot.change_presence(status=discord.Status.idle, activity=game)

            self.checksum_checks -= 1
            if self.checksum_checks <= 0:
                if not self.bot.is_launched_through_orwell:
                    os.startfile('start_kat.bat')
                await self.bot.logout()


    @commands.Cog.listener()
    async def on_kat_five_minute_event(self):
        if not self.bot.is_restart_scheduled:
            name = self.get_response("core.generic.kat_ready")

            # TODO: Change this to the new 'Custom Status' when discord-py is updated!
            # Update: Still no custom status' :( waiting for discord 
            game = discord.Game(name)
            await self.bot.change_presence(status=discord.Status.online, activity=game)

        if self.bot.maintenance_mode:
            await self.bot.change_presence(status=discord.Status.idle, activity=discord.Game(self.get_response('core.generic.kat_restart_scheduled')))

    
    #### Commands
    @commands.command(aliases=['?'])
    async def help(self, ctx):
        """Shows a link for this page"""
        embed = discord.Embed(title="How to use Kat", colour=discord.Colour(0xe08a04), description=self.get_response("core.command.help") + self.get_response("core.command.help_link", prefix=ctx.prefix))
        await ctx.send(embed=embed)


    @commands.command(hidden=True)
    @commands.is_owner()
    async def echo(self, ctx):
        channel = ctx.channel
        message = ctx.message.content[5:]
        msgs = await ctx.channel.history(limit=2).flatten()
        await msgs[0].delete()
        await channel.send(message)

    @commands.group(hidden=True)
    async def kat(self, ctx):
        if not perms.is_author(self.bot, ctx.author.id):
            return  

    def check(self, msg):
        if msg.author.id == self.bot.app_info.owner.id:
            return True
        return False

    @kat.command(hidden=True)
    @commands.is_owner()
    async def announce(self, ctx, *announcement):
        await ctx.send("CAUTION. Will message EVERY guild owner the following: \n {} \n Are you sure (Y/N)".format(announcement))
        msg = await self.bot.wait_for('message', check=self.check)

        if msg.content.lower().startswith('y'):
            msgd_owners = []
            for guild in self.bot.guilds:
                if guild.owner not in msgd_owners:
                    msgd_owners.append(guild.owner)
                    
                    if guild.owner.id == 172408031060033537:
                        await guild.owner.send(" ".join(announcement))

                    await ctx.send("Would have messaged : {}".format(guild.owner.name))
                    #await guild.owner.send(announcement)
        else:
            await ctx.send("Announcement Cancelled.")

    @kat.command()
    async def status(self, ctx):
        embed = discord.Embed(title="Kat `{}` Status Report".format(self.bot.version), color=discord.Color.dark_orange())

        timestamp = self.bot.start_time
        now = time.time() - timestamp
        if  now < 60:
            string = f"`{int(now)}` seconds."
        elif 60 < now < 3600 :
            string = f"around `{int(now / 60)}` minutes."
        else:
            string = f"around `{int(now / 60 / 60)}` hours."
        
        embed.description = f"Kat was started at `{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}`, and has been running for {string}."
        metrics = self.collect_metrics().items()
        for metric, value in metrics:
            embed.add_field(name=metric, value="```fix\n" + str(value) + "```", inline=False)
        await ctx.send(embed=embed)

    @kat.command(hidden=True)
    @commands.is_owner()
    async def stop(self, ctx):
        """
        $kat stop
            forces kat to stop.
        """
        await ctx.send(self.get_response("core.command.kat_stop"))
        await self.bot.logout()

    @kat.command(aliases=["restart"], hidden=True)
    @commands.is_owner()
    async def reboot(self, ctx):
        """
        $kat reboot
            forces kat to reboot.
        """
        await ctx.send(self.get_response("core.command.kat_restart"))
        try:
            if not self.bot.is_launched_through_orwell:
                os.startfile('start_kat.bat')
            await self.bot.logout()
        except Exception as err:
            await self.throw_command_error_to_message(ctx, err)

    @kat.command(hidden=True)
    @commands.is_owner()
    async def exec(self, ctx, *args):
        args = " ".join(args)
        try:
            exec("self.output = " + args)
            embed = discord.Embed(color=discord.Color.green())
            embed.set_author(name="Execution Succeeded", icon_url="https://cdn.discordapp.com/emojis/669531367511425024.png?v=1")
            embed.description = "```py\n{}\n```".format(self.output)
            await ctx.send(embed=embed)
        
        except Exception:
            embed = discord.Embed(color=discord.Color.red())
            embed.set_author(name="Execution Failed", icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1")
            embed.description = "```py\n{}\n```".format(traceback.format_exc())
            await ctx.send(embed=embed)
        

    @kat.command(hidden=True)
    @commands.is_owner()
    async def imp (self, ctx, arg):
        """Imports a python module for $exec use."""
        try:
            exec("import " + arg)
            _ = None
            exec("_ = " +arg + ".__version__")
            self.output = arg + _ 
            embed = discord.Embed(color=discord.Color.green())
            embed.set_author(name="Execution Succeeded", icon_url="https://cdn.discordapp.com/emojis/669531367511425024.png?v=1")
            embed.description = "```py\n{}\n```".format(self.output)
            await ctx.send(embed=embed)
        except Exception:
            embed = discord.Embed(color=discord.Color.red())
            embed.set_author(name="Execution Failed", icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1")
            embed.description = "```py\n{}\n```".format(traceback.format_exc())
            await ctx.send(embed=embed)
    

    @commands.command()
    async def join(self, ctx, fake_id):
        await self.bot.join_test(ctx, fake_id)


    def load_cog(self, cog_name) -> str:
        """Attempts to load a cog and returns its command list."""
        
        try:
            # Attempt to load the cog.
            name, cog = utils.load_cog(self.bot, cog_name)
            
            cmds = ""
            for k, j in zip([c.qualified_name for c in cog.walk_commands()], [c.signature for c in cog.walk_commands()]):
                cmds += "{} : {}\n".format(k, j)

            return self.get_response("core.command.kat_load", cmds=cmds, cog_name=cog.qualified_name)
            
        except commands.ExtensionNotFound:
            return self.get_response("core.error.ExtensionNotFound")
        except commands.ExtensionAlreadyLoaded:
            return self.get_response("core.error.ExtensionAlreadyLoaded")
        except commands.NoEntryPointError:
            return self.get_response("core.error.NoEntryPointError")
        except commands.ExtensionFailed:
            return self.get_response("core.error.ExtensionFailed")


    def unload_cog(self, cog_name):
        try:
            name, _ = utils.unload_cog(self.bot, cog_name)
            return self.get_response("core.command.kat_unload", cog_name=name)

        except commands.ExtensionNotLoaded as err:
            return self.get_response("core.error.ExtensionNotLoaded", err=err)



    @kat.command(hidden=True)
    async def load(self, ctx, cog_name):
        """ Load a cog """
        await ctx.send(self.load_cog(cog_name))

    @kat.command(hidden=True)
    async def unload(self, ctx, cog_name):
        """ Unload a loaded cog."""
        await ctx.send(self.unload_cog(cog_name))

    @kat.command(hidden=True)
    async def reload(self, ctx, cog_name):
        

        cog = ""
        if "." in cog_name:
            _ = cog_name.split('.')
            for string in _:
                cog += string.capitalize()
        else:
            cog = cog_name.capitalize()

        self.log.debug(cog)
        self.log.debug(cog_name)
        if cog not in self.bot.cogs:
            await ctx.send(self.load_cog(cog_name))
            return

        try:
            self.unload_cog(cog_name)
            await ctx.send(self.load_cog(cog_name))
        except commands.ExtensionError as err:
            await ctx.send(self.get_response("common.error.command_error", err=err))


    @kat.command(alias=['presence', 'changegame', 'game'], hidden=True)
    async def changepresence(self, ctx):
        if self.bot.is_restart_scheduled:
            return
        name = self.get_response("core.generic.kat_ready")
        game = discord.Game(name)
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @kat.command(hidden=True)
    async def maintenance(self, ctx, value: bool):
        if value:
            self.bot.maintenance_mode = True
            await ctx.send(self.get_response("core.command.kat_maintenance_on"))
            await self.bot.change_presence(status=discord.Status.idle, activity=discord.Game(self.get_response('core.generic.kat_maintenance_presence')))
        else:
            self.bot.maintenance_mode = False
            game = discord.Game(self.get_response("core.generic.kat_ready", bot=self.bot))
            await self.bot.change_presence(status=discord.Status.online, activity=game)
            await ctx.send(self.get_response("core.command.kat_maintenance_off"))

    @kat.command(hidden=True)
    async def dump(self, ctx, cog_name):
        cog = self.bot.get_cog(cog_name)
        _ = ',\n'.join("{}: {}".format(i, str(cog.__dict__[i])[:50]) for i in cog.__dict__ if not i.startswith('__') and not callable(cog.__dict__[i]))
        embed = discord.Embed()
        embed.set_author(name="Attribute Dump", icon_url="https://cdn.discordapp.com/emojis/669531367511425024.png?v=1")
        embed.description = "```py\n{}\n```".format(_)
        await ctx.send(embed=embed)

    
    @kat.command(hidden=True)
    async def reloadresp(self, ctx):
        for cog in self.bot.cogs:
            self.bot.get_cog(cog).load_responses()

    # New EventManager command
    @kat.command(hidden=True)
    async def eventlist(self, ctx):
        string = "```py\nMAIN\n"
        for k,v in self.bot.event_manager._events.items():
                string += "{}: {}\n\n".format(k,v)
        for cog in self.bot.cogs:
            if len(self.bot.get_cog(cog).event_manager._events) > 0: 
                string += "{}\n".format(cog)
                for k,v in self.bot.get_cog(cog).event_manager._events.items():
                    string += "{}: {}\n\n".format(k,v)
        string += "```"
        await ctx.send(string)
                        
def setup(bot):
    bot.add_cog(Core(bot))
