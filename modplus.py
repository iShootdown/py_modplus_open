#general packages
import logging
import discord
from discord.ext import commands
import asyncio
import json

#system managements
import os
import traceback

#use a service account
botprefix = 'm+' #=========================================================================|

def getprefix(bot, message):
    return botprefix

#intents because Discord gae
intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, guild_messages=True, message_content=True)

#bot almost acts as client = discord.Client()
class MyBot(commands.Bot):

    async def setup_hook(self):
        discord.utils.setup_logging(level=logging.INFO, root=False)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

    async def close(self):
        await self.change_presence(self,status=discord.Status.offline)
        print('stopping')
        await super().close()

bot = MyBot(command_prefix=commands.when_mentioned_or("m+"), intents=intents, case_insensitive=True, status=discord.Status.online)
bot.remove_command('help')

def embederr(msg):
    embederror = discord.Embed (
        title = 'Error',
        description = str(msg),
        color = discord.Colour.red(),
    )
    return embederror

defaultcolour = 0x70f3f3

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
@commands.is_owner()
async def synccmds(ctx):
    await bot.tree.sync()

@bot.command(brief='Shows this message',name='commands')
@commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True)
async def cmdlist(ctx, cmdr:str=None, subcmdr:str=None):
    if cmdr == None and subcmdr == None:
        coggers = bot.cogs
        cogcmds = [o.get_commands() for o in list(coggers.values())]
        cognames = [*coggers]
        cogdict = {}
        for i in range(len(cognames)):
            cogdict[cognames[i]] = cogcmds[i]

        for i in [*cogdict]:
            tempname = []
            temptxt = []
            for u in cogdict[i]:
                try:
                    canrun = await u.can_run(ctx)
                except (discord.ext.commands.CheckFailure, discord.ext.commands.CommandError):
                    pass
                else:
                    if canrun is True and u.hidden is False:
                        tempname.append(u.name)
                        temptxt.append(u.brief)

            cogdict[i] = [tempname, temptxt]

        for i in [*cogdict]:
            hol = []
            cmdlist = cogdict[i][0]
            if cmdlist == []:
                del cogdict[i]
                continue
            else:
                cmddesc = cogdict[i][1]

                for o in range(len(cmdlist)):
                    if cmddesc[o] != None:
                        hol.append('`%s` %s' % (cmdlist[o],cmddesc[o]))
                    elif cmdlist[o] != None:
                        hol.append('`%s`' % (cmdlist[o]))
                    else:
                        continue

                cogdict[i] = hol

        nilcmds = []
        niltxt = []
        nilcmd = [p for p in bot.commands if p.cog is None]
        for i in nilcmd:
            try:
                canrun = await i.can_run(ctx)
            except discord.ext.commands.CommandError:
                pass
            else:
                if canrun is True and i.hidden is False:
                    nilcmds.append(i.name)
                    niltxt.append(i.brief)

        nilpara = []
        for i in range(len(nilcmds)):
            if niltxt[i] != None:
                nilpara.append('`%s` %s' % (nilcmds[i],niltxt[i]))
            else:
                nilpara.append('`%s`' % (nilcmds[i]))

        prefixprint = botprefix

        helpembed = discord.Embed (
            title = 'Commands List',
            description = f'Guild Prefix: `{prefixprint}`',
            colour = discord.Colour(defaultcolour),
        )
        for i in [*cogdict]:
            helpembed.add_field(name=i, value='\n'.join(cogdict[i]), inline=False)
        helpembed.add_field(name='General', value='\n'.join(nilpara), inline=False)
        helpembed.set_footer(text=f"Use {prefixprint}commands <command> to see more info and subcommands\nPlease don't include the <> when typing out command")
        return await ctx.send(embed=helpembed)

    else:
        cmdr = cmdr.strip(' ').lower()
        if subcmdr != None:
            subcmdr = subcmdr.strip(' ').lower()
        cmds = bot.commands
        cmdnames = [p.name for p in bot.commands]
        cmdict = dict(zip(cmdnames, cmds))

        if cmdr not in [*cmdict]:
            return await ctx.send(embed=embederr('Command does not exist.'),delete_after=5.0)
        elif cmdict[cmdr].hidden is True:
            return await ctx.send(embed=embederr('CoMmaND dOeS nOt ExIst.'),delete_after=5.0)
        else:
            cmd = cmdict[cmdr]
            try:
                canrun = await cmd.can_run(ctx)
            except discord.ext.commands.CommandError:
                return await ctx.send(embed=embederr('You do not have the required permissions.'),delete_after=5.0)
            else:
                if canrun is not True or cmd.hidden is not False:
                    return await ctx.send(embed=embederr('You do not have the required permissions.'),delete_after=5.0)

        try:
            subcmds = cmd.commands
        except AttributeError:
            subcmds = None
            subcmdpara = []
            subcmdict = {}
        else:
            subcmdnames = [p.name for p in cmd.commands]
            subcmdict = dict(zip(subcmdnames, subcmds))
            subcmdpara = []
            for i in [*subcmdict]:
                if subcmdict[i] != None:
                    subcmdpara.append('`%s` %s' % (i,subcmdict[i].help))
                else:
                    subcmdpara.append('`%s`' % (i))

        if subcmdr != None:
            if subcmdr in [*subcmdict]:
                subcmd = subcmdict[subcmdr]
                try:
                    canrun = await subcmd.can_run(ctx)
                except discord.ext.commands.CommandError:
                    return await ctx.send(embed=embederr('You do not have the required permissions.'),delete_after=10.0)
                else:
                    if canrun is not True or subcmd.hidden is not False:
                        return await ctx.send(embed=embederr('You do not have the required permissions.'),delete_after=10.0)
            else:
                subcmd = None
        else:
            subcmd = None

        if subcmd is None:
            cmdnamer = cmd.name
            cmdhelp = cmd.help
            usager = f'{botprefix}{cmd.name}'
            params = [*dict(cmd.clean_params)]
            params = ['<'+i+'>' for i in params]
            brief = cmd.brief

        else:
            cmdnamer = f'{cmd.name} {subcmd.name}'
            cmdhelp = subcmd.help
            usager = f'{botprefix}{cmd.name} {subcmd.name}'
            params = [*dict(subcmd.clean_params)]
            params = ['<'+i+'>' for i in params]
            brief = subcmd.brief

        if subcmds != None and subcmdr is None:
            usager += ' <subcommand>'
        if params != []:
            usager += ' ' + ' '.join(params)

        usager = f'`{usager}`'

        qembed = discord.Embed (
            title = cmdnamer,
            description = cmdhelp,
            colour = discord.Colour(defaultcolour)
        )
        qembed.set_author(name='Showing help for command')
        qembed.add_field(name='Description',value=brief,inline = False)
        qembed.add_field(name='Usage',value=usager,inline = False)
        if subcmdpara != [] and subcmd is None:
            qembed.add_field(name='Subcommands available',value='\n'.join(subcmdpara),inline = False)

        return await ctx.send(embed=qembed)

@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx,cog:str='all'):
    if cog == 'all':
        #os.system('git pull')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                bot.reload_extension(f'cogs.{filename[:-3]}')
    else:
        bot.reload_extension(name=f'cogs.{cog}')

@bot.command(hidden=True)
@commands.is_owner()
async def botleave(ctx,gid:int):

    gguild = bot.get_guild(gid)
    await gguild.leave()
    print(f'Left guild {gguild.name}')

@bot.event
async def on_command(ctx):
    if ctx.guild == None:
        print(f'{ctx.author} from DMs used {ctx.command} at {ctx.message.created_at}')
    else:
        print(f'{ctx.author} from {ctx.guild.name} used {ctx.command} at {ctx.message.created_at}')

@bot.event
async def on_command_error(ctx,error):
    if ctx.guild == None:
        guilder = 'DMs'
    else:
        guilder = ctx.guild.name

    print(f'{error} from {guilder}')
    traceback.print_tb(error.__traceback__)

    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    errorstr = None
    footerstr = None

    if isinstance(error, commands.NotOwner):
        errorstr = 'Owner only command.'
    elif isinstance(error, commands.NoPrivateMessage):
        errorstr = 'Guild only command.'
    elif isinstance(error, commands.MissingRequiredArgument):
        missingargs = error.param
        errorstr = 'Missing `%s` parameter.' % missingargs
        footerstr = f"Use {botprefix}commands {ctx.command.name} for usage info"
    elif isinstance(error, commands.BotMissingPermissions):
        missingperms = error.missing_perms
        errorstr = f'Bot missing permission `{" | ".join(missingperms)}`.'
        footerstr = f"Use {botprefix}commands {ctx.command.name} for usage info"
    elif isinstance(error, commands.MissingPermissions):
        missingperms = error.missing_perms
        errorstr = f'User missing permission `{" | ".join(missingperms)}`.'
    elif isinstance(error, commands.CommandNotFound):
        invokedcmd = str(error).split(' ')[1].strip('"')
        if invokedcmd.isalpha() == True:
            errorstr = f'Command `{invokedcmd}` is not found.'
            footerstr = f"Use {botprefix}help or {botprefix}commands for valid commands"
    else:
        errorstr = f'Unexpected error has occurred.'
        footerstr = f'Dev notified of error. You can check updates via {botprefix}support.'

    try:
        if errorstr is not None:
            embedrr = embederr(errorstr)
            if footerstr is not None:
                embedrr.set_footer(text=footerstr)
            return await ctx.send(embed=embedrr,delete_after=10.0)
    except discord.errors.Forbidden:
        errorembed = discord.Embed (
            title = 'Bot missing permissions',
            colour = discord.Colour.red(),
            description = '`send_messages` | `embed_links`'
        )
        if errorstr is not None:
            errorembed.add_field(name='Additional errors',value=errorstr,inline=False)
        errorembed.set_footer(text="If you don't have permissions to edit permissions for bot, please contact your server moderators")
        return await ctx.author.send(embed=errorembed)

async def starter(bot):
    with open('./secrets/bot_token.json') as f:
        json_dict = json.load(f)
        
        if json_dict["discord_token"] == "":
            print("Please insert bot token into secrets/bot_token.json")
            exit()

        await bot.start(json_dict["discord_token"])

asyncio.run(starter(bot=bot))