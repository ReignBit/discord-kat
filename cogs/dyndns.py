# discord specific imports
from discord.ext import commands
import discord

# python imports
import requests
import asyncio
# third party imports

# kat specific imports
import utilities.KatCog as KatCog



class Dyndns(KatCog.KatCog):

    """Cog to update our Dynamic IP to GoDaddy's DNS records for REIGN-NETWORK.CO.UK"""
    """Updates A record for host @ with KAT'S CURRENT EXTERNAL IP ADDRESS."""

    def __init__(self, bot):
        super().__init__(bot)
        
        self.url = f"https://api.godaddy.com/v1/domains/{self.settings['domain']}/records/A/@"
        self.session = requests.Session()

        self.session.headers.update(
            {'Authorization': 'sso-key ' + self.settings["auth_key"]})


    def update_ips(self):
        ip = requests.get('https://api.ipify.org').text
        dad_ip = self.session.get(self.url).json()[0]['data']
        #self.log.debug("CURRENT IP: {}   |   DNS IP: {}".format(ip, dad_ip))
        return ip, dad_ip


    @commands.Cog.listener()
    async def on_kat_hour_event(self):
        if not self.run:
            return
        
        self.log.info("Updating IP...")
        self.current_ip, self.daddy_ip = self.update_ips()

        if self.daddy_ip != self.current_ip:
            self.log.info(
                "GoDaddy's DNS A record is not up to date! Attempting to change...")

            # Creates and executes the PUT request for DNS record type A for host @
            data = '[ { "data": "' + str(self.current_ip) + '" }]'
            res = self.session.put(self.url, data, headers={
                                    'Content-Type': 'application/json'})
            self.log.debug(res.status_code)
            if res.status_code == "200":
                self.log.info("Updated DNS Record. Checking if changed...")
                self.log.warn(res.status_code)
                self.log.debug(res)
            else:
                self.log.warn(
                    "Did not receive 200 status code. Something went wrong and the IP was probably not updated.")
            # Update current ip and godaddys ip
            self.current_ip, self.daddy_ip = self.update_ips()

            # Test to see if the request worked.
            if self.daddy_ip != self.current_ip:
                self.log.warn(
                    "GoDaddy DNS did not update successfully. The API Gateway could be down or the request failed somehow.")
        


def setup(bot):
    bot.add_cog(Dyndns(bot))
