# Kat Discord Bot (Version 3.1.0) 
A customizable administration bot originally designed for Reign Network, complete with an interactive webpanel for easy configuring for user's guilds.

For more information about Kat: https://kat.reign-network.co.uk

Join Kat's Dev Server: https://discord.gg/VFBy7faTPP



## Self-Hosting
Kat has not been tested for self-hosting, and is only on GitHub for version control. \
We strongly recommend to instead add our instance of Kat to your discord server:

https://kat.reign-network.co.uk/invite

However, if you want to attempt to run Kat on your own hardware, here's how to setup her up.

### Step 1: Dependencies
Kat comes with requirements.txt which includes all dependencies needed to get her running. Install them using pip. 

```
pip install -r requirements.txt
```

### Step 2: Config file
Rename `config-default.json` in the `config/` folder and change the settings suitable for your setup. Note that some settings will be of no use to you, these are marked with `wont work for public release`. These config settings will not work since you will be missing the backend Kat uses.

It is up to you to recreate the backend.

### Step 3: Recreate the backend
Unfortunately since Kat is not meant to be a public release, I have not created any auto-installer or such thing to create the Database and other backend things. For this reason you will need to create your own backends.

Changes to the following files are needed:
```
    utilites/KatClasses.py
    utilites/orm_utilities.py
```
Good luck!