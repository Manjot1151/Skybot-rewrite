import discord
from utils import logging
from inspect import Parameter
from discord.ext import commands
from utils.skypy import skypy

async def on_user_verified(ctx, bot: commands.Bot, name):
    try:
        if await bot.guilds_db["settings"].find_one({"_id": ctx.guild.id})["banscammers"]:
            name, uuid = await skypy.fetch_uuid_uname(name)
            if await bot.scammer_db["scammer_list"].find_one({"_id": uuid}):
                await ctx.author.ban("verified as scammer")
    except (KeyError, discord.Forbidden) as e:
        if isinstance(e, discord.Forbidden):
            await ctx.send(f"{ctx.guild.owner.mention}:\n{ctx.author.mention} just successfully verifed as a known scammer, but I do not have permission to ban them.")

    #TODO make this do stuff lel


class ServerConfig(commands.Cog, name="ServerConfig"):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot
        


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def cog_unload(self):
        pass

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.group(name="prefix", description="Set the prefix that triggers the bot.", aliases=["pre"], usage="[set/reset/get]")
    async def prefix(self, ctx : commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command("help show_command"), arg="prefix")

    @prefix.command()
    async def set(self, ctx, arg):
        prefixes_coll = self.bot.guilds_db["prefixes"]
        guild_db = await prefixes_coll.find_one({"guild_id" : ctx.guild.id})
        if guild_db:
            await prefixes_coll.update_one(guild_db, {"$set" : {"prefix" : arg}})
            return await ctx.send(f"Your server's prefix has been set to `{arg}`")
        await prefixes_coll.insert_one({"guild_id" : ctx.guild.id, "prefix" : arg})
        return await ctx.send(f"Your server's prefix has been set to `{arg}`")

    @prefix.command()
    async def reset(self, ctx):
        result = await self.bot.guilds_db["prefixes"].delete_one({"guild_id" : ctx.guild.id})
        if result.deleted_count > 0:
            return await ctx.send("Prefix has been reset to `" + self.bot.config["default_prefix"] + "`")
        return await ctx.send("Nothing changed. You haven't changed the prefix yet, use the `set` argument.")
        
    @prefix.command()
    async def get(self, ctx):
        prefix = await self.bot.guilds_db["prefixes"].find_one({"guild_id" : ctx.guild.id})
        if prefix:
            return await ctx.send("My prefix here is `" + prefix["prefix"] + "`")
        return await ctx.send("My prefix here is `" + self.bot.config["default_prefix"] + "`")


    @commands.command(name="scammerChannel", description="Set a scammer list channel for your server. Leave [channel] blank to remove the channel", usage="[channel]")
    @commands.has_guild_permissions(administrator=True)
    async def scammerChannel(self, ctx, channel:discord.TextChannel=None):
        guild = await self.bot.scammer_db["channels"].find_one({"_id": ctx.guild.id})
        if channel:
            if guild:
                await self.bot.scammer_db["channels"].update_one({guild, {"$set": {"list_channel": channel.id}}})
            else:
                await self.bot.scammer_db["channels"].insert_one({"_id": ctx.guild.id, "list_channel": channel.id})
            return await ctx.send(f"Set the scammer list channel to {channel.mention}")
        else:
            if guild:
                await self.bot.scammer_db["channels"].delete_one(guild)
            return await ctx.send("Removed the scammer list channel")

    @commands.command(name="banscammers", description="Automatically ban users who successfully verify as a known scammer", aliases=["banscammer"], usage="[on|off]")
    @commands.has_guild_permissions(administrator=True)
    async def banscammers(self, ctx, toggle:str="off"):
        if toggle.lower() == "on":
            choice = True
        elif toggle.lower() == "off":
            choice = False
        else:
            return await ctx.send("Invalid choice. Choose either `on` or `off`")
        if await self.bot.guilds_db["settings"].find_one({"_id": ctx.guild.id}):
            await self.bot.guilds_db["settings"].update_one({"_id": ctx.guild.id}, {"$set": {"banscammers": choice}})
        else:
            await self.bot.guilds_db["settings"].insert_one({"_id": ctx.guild.id, "banscammers": choice})
        await ctx.send(f"Setting `banscammers` is now `{toggle.lower()}` in this server")


def setup(bot):
    bot.add_cog(ServerConfig(bot))