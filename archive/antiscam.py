import discord
from discord.ext import commands, tasks
import asyncio
from firebase_admin import firestore
import requests
import aiohttp
import re
# Use a service account

db = firestore.client()
botprefix = 'm+'

def getprefix(bot, message):
    if message.guild != None:
        return bot.guildprefixes[str(message.guild.id)]
    else: # for DMs
        return botprefix

def embederr(msg):
    embederror = discord.Embed (
        title = 'Error',
        description = str(msg),
        color = discord.Colour.red(),
    )
    return embederror

def stringclean(string):
    string = string.strip(' \n')
    return string

def localupdate(bot,guild,dicter):
    gdict = bot.serverdicters[str(guild)]
    for key in dicter.keys():
        gdict[key] = dicter[key]
    
    dicts = bot.serverdicters
    dicts[str(guild)] = gdict
    bot.serverdicters = dicts

    db.collection(u'servers').document(f'{guild}').update(dicter)

def localdelete(bot,guild,key):
    gdict = bot.serverdicters[str(guild)]
    del gdict[key]
    
    dicts = bot.serverdicters
    dicts[str(guild)] = gdict
    bot.serverdicters = dicts

    db.collection(u'servers').document(f'{guild}').update({key:firestore.DELETE_FIELD})

defaultcolour = 0x70f3f3
profcolours = [0x70f3f3, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class AntiScam(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        bot.scamlinks = []        
        r = requests.get('https://phish.sinking.yachts/all', headers = {u"X-Identity":  u'discord-bot'})
        if r.status_code == 200:
            self.bot.scamlinks = r.json()
        self.updatescamlinks.start()
        bot.antiscam = [int(i) for i in bot.serverdicters if bot.serverdicters[i].get('antiscam') == True]

    def cog_unload(self):
        self.updatescamlinks.cancel()

    def owner_or_permissions(**perms):
        original = commands.has_permissions(**perms).predicate
        async def extended_check(ctx):
            if ctx.guild is None:
                return False
            return ctx.guild.owner_id == ctx.author.id or  ctx.author.id == 283790768252911619 or await original(ctx)
        return commands.check(extended_check)

    @tasks.loop(minutes=5,reconnect=False,count=None)
    async def updatescamlinks(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://phish.sinking.yachts/all', headers = {u"X-Identity":  u'discord-bot'}) as r:
                if r.status == 200:
                    self.bot.scamlinks = await r.json()

    @commands.Cog.listener()
    async def on_message(self,message):

        if message.guild == None:
            return

        if self.bot.serverdicters.get(str(message.guild.id)) == None:
            return
        
        if self.bot.serverdicters[str(message.guild.id)].get('antiscam') == True:
            newmessager = re.findall(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]", message.content)
            matches = [i for i in self.bot.scamlinks if i in newmessager]

            if len(matches) > 0:
                guilddict = self.bot.serverdicters[str(message.guild.id)]
                delete = '⚠️ Failed'
                try:
                    await message.delete()
                    delete = '✅ Success'
                    scamembed = discord.Embed(
                        title = '⚠️ Scam link detected ⚠️',
                        description = 'A scam link was detected in deleted message and was removed successfully.',
                        colour = discord.Color.red()
                    )
                    scamembed.set_footer(text=f'Message sent by {message.author}',icon_url=message.author.display_avatar.url)
                    await message.channel.send(embed=scamembed,delete_after=10.0)
                
                except discord.HTTPException:
                    pass

                if guilddict.get('antiscamaction') != None:
                    action = guilddict.get('antiscamaction')
                    if action == None:
                        action = 'kick'
                    acted = '⚠️ Failed'
                    try:
                        if action == 'kick':
                            await message.author.kick(reason='Scam link detected. Automatic action.')
                        elif action == 'ban':
                            await message.author.ban(reason='Scam link detected. Automatic action.')
                        acted = '✅ Success'

                        dmembed = discord.Embed(
                            tile = '⚠️ Warning',
                            description = f'You were {action} from {message.guild.name} as you have posted a scam link.\n\nPlease note that you should restore your account by changing your password, and removing the affected client immediately.',
                            colour = discord.Color.red()
                        )

                        try:
                            await message.author.send(embed=dmembed)
                        except Exception as e:
                            print(e)
                            pass
                    except discord.HTTPException:
                        pass
                else:
                    action = 'delete only'

                if guilddict.get('antiscamlog') != None:
                    logchannel = self.bot.get_channel(guilddict.get('antiscamlog'))
                    logembed = discord.Embed(
                        title = 'Scam Link Found',
                        color = discord.Color.red()
                    )
                    logembed.add_field(name='Channel',value=message.channel.mention,inline=False)
                    logembed.add_field(name='User',value=f'{message.author.mention} [{message.author.id}]',inline=False)
                    logembed.add_field(name='Link detected',value=f"||{matches}\n||Original message:\n||{message.content}||",inline=False)
                    actiontext = f'Delete [{delete}]'
                    if action != 'delete only':
                        actiontext = actiontext + '\n' + f'{action.capitalize()} [{acted}]'

                    logembed.add_field(name='Action',value=actiontext,inline=False)
                    await logchannel.send(embed=logembed)

    @commands.group(brief='Configure antiscam', case_insensitive=True)
    @commands.guild_only()
    @owner_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def antiscam(self,ctx,inchannel:discord.TextChannel=None):
        '''Allows server admins to configure antiscam for current server.
        This will show current configurations and channels for antiscam.
        Do not run the subcommmands, they will not work for now.'''

        if ctx.invoked_subcommand is None:

            if inchannel == None:
                inchannel = ctx.channel
            else:
                inchannel = inchannel

            chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, manage_messages=True, add_reactions=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                prep = [f'`{i}`' for i in diffperms]
                prep = '|'.join(prep)
                return await inchannel.send(content=f'Missing permissions [{prep}]')

            serverdict = db.collection(u'servers').document(f'{ctx.guild.id}').get().to_dict()
            
            if serverdict.get('antiscam') != None:
                antiscam = bool(serverdict.get('antiscam'))
            else:
                antiscam = False

            if antiscam == False:
                msgs = {'✅': 'Enable'}
            else:
                msgs = {'1️⃣': 'Action', '2️⃣': 'Logging Channel', '3️⃣': 'Reset'}
            msgs['🚫'] = 'Cancel'
            texter = '\n'.join([f'{o} {msgs[o]}' for o in msgs])
            reactions = list(msgs.keys())

            configembed = discord.Embed(
                title = 'Antiscam Configurations',
                description = f'**React below to configure**\n{texter}',
                colour = discord.Colour(defaultcolour)
            )
            configembed.set_author(name=f'Currently configuring for #{inchannel.name}')

            configmsg = await ctx.send(embed=configembed)
            for i in reactions:
                await configmsg.add_reaction(i)

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in reactions

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                configembed = discord.Embed(
                    title = 'Antiscam Configurations',
                    colour = discord.Colour(defaultcolour)
                )
                configembed.set_author(name=f'Currently configuring for #{inchannel.name}')
                await configmsg.edit(embed=configembed)
                return await configmsg.clear_reactions()
            else:
                if str(reaction.emoji) == '✅':

                    embed = discord.Embed (
                        title = 'Activating AntiScam',
                        description = f'Please go through the setup process, it will take a short while.',
                        colour = discord.Colour(defaultcolour)
                    )
                    await configmsg.edit(embed=embed)
                    await configmsg.clear_reactions()
                    await asyncio.sleep(3)

                    embed = discord.Embed (
                        title = 'Logging channel',
                        description = f'Set {inchannel.mention} as logging channel?\n✅ Yes | 🚫 No',
                        colour = discord.Colour(defaultcolour)
                    )
                    embed.set_author(name=f'Currently configuring for #{inchannel.name}')
                    await configmsg.edit(embed=embed)
                    await configmsg.add_reaction('✅')
                    await configmsg.add_reaction('🚫')
                    
                    def check(reaction, user):
                        reactions = ['✅','🚫']
                        return user == ctx.author and str(reaction.emoji) in reactions

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        print('timeout')
                        return await configmsg.edit(embed=embederr('User took too long!'),delete_after=10.0)

                    await configmsg.clear_reactions()

                    if str(reaction.emoji) == '✅':
                        pass
                    elif str(reaction.emoji) == '🚫':
                        embed = discord.Embed (
                            title = 'Logging channel',
                            description = f'Please mention the logging channel.',
                            colour = discord.Colour(defaultcolour)
                        )
                        await configmsg.edit(embed=embed)

                        def verify(m):
                            return m.author.id == ctx.author.id

                        try:
                            msginput = await self.bot.wait_for('message', check=verify, timeout=180.0)
                        except asyncio.TimeoutError:
                            print('timeout')
                            return await configmsg.edit(embed=embederr('User took too long!'),delete_after=10.0)

                        if len(msginput.channel_mentions) == 1 or int(stringclean(msginput.content)) in [i.id for i in ctx.guild.text_channels]:
                            await msginput.delete()
                            if len(msginput.channel_mentions) == 1:
                                inchannel = msginput.channel_mentions[0]
                            else:
                                inchannel = self.bot.get_channel(int(stringclean(msginput.content)))
                        else:
                            await msginput.delete()
                            return await configmsg.edit(embed=embederr('Invalid input.'),delete_after=10.0)

                    choices = {'1️⃣': 'Kick', '2️⃣': 'Ban', '3️⃣': 'Delete only'}
                    texter = '\n'.join([f'{o} {choices[o]}' for o in choices])

                    nline = '\n'
                    embed = discord.Embed (
                        title = 'Choose Anti-scam Action',
                        description = f"React to choose action taken when scam link detected.{nline}Delete will be done automatcially{nline}{texter}",
                        colour = discord.Colour(defaultcolour)
                    )
                    embed.set_author(name=f'Currently configuring for #{inchannel.name}')
                    await configmsg.edit(embed=embed)
                    for i in choices:
                        await configmsg.add_reaction(i)

                    def check(reaction, user):
                        reactions = choices.keys()
                        return user == ctx.author and str(reaction.emoji) in reactions

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        print('timeout')
                        return await configmsg.edit(embed=embederr('User took too long!'),delete_after=10.0)

                    action = choices[str(reaction.emoji)].lower()
                    if action == 'kick':
                        chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
                        checkperms = discord.Permissions(kick_members=True)
                        checkperms = dict(iter(checkperms))
                        chanperms = dict(iter(chanperms))
                        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
                        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
                        if diffperms != []:
                            return await configmsg.edit(embed=embederr('Missing permissions: `kick_members`.\nPlease provide perms and rerun command.'),delete_after=10.0)
                    
                    elif action == 'ban':
                        chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
                        checkperms = discord.Permissions(ban_members=True)
                        checkperms = dict(iter(checkperms))
                        chanperms = dict(iter(chanperms))
                        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
                        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
                        if diffperms != []:
                            return await configmsg.edit(embed=embederr('Missing permissions: `ban_members`\nPlease provide perms and rerun command.'),delete_after=10.0)

                    localupdate(self.bot,ctx.guild.id,{u'antiscamlog': inchannel.id, u'antiscamaction': action.lower(), 'antiscam': True})

                    okembed = discord.Embed (
                        title='Success',
                        colour = discord.Colour.green(),
                        description = f'Current antiscam Logging channel: {inchannel.mention}'+'\n'+f'Current antiscam Action: `{action}`',
                    )
                    await configmsg.clear_reactions()
                    return await configmsg.edit(embed=okembed)

                elif str(reaction.emoji) == '1️⃣':
                    await configmsg.delete()
                    return await ctx.invoke(self.bot.get_command('antiscam action'), inchannel=inchannel)
                
                elif str(reaction.emoji) == '2️⃣':
                    await configmsg.delete()
                    return await ctx.invoke(self.bot.get_command('antiscam logger'), inchannel=inchannel)

                elif str(reaction.emoji) == '3️⃣':
                    await configmsg.delete()
                    return await ctx.invoke(self.bot.get_command('antiscam reset'), inchannel=inchannel)

                elif str(reaction.emoji) == '🚫':
                    configembed = discord.Embed(
                        title = 'Antiscam Configurations',
                        colour = discord.Colour(defaultcolour)
                    )
                    await configmsg.edit(embed=configembed)
                    return await configmsg.clear_reactions()

    @antiscam.command(brief='Set channel for logging')
    @commands.guild_only()
    @owner_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def logger(self,ctx,inchannel:discord.TextChannel=None):
        '''Sets the notice for current channel'''

        if inchannel == None:
            inchannel = ctx.channel
        else:
            inchannel = inchannel

        chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
        checkperms = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True)
        checkperms = dict(iter(checkperms))
        chanperms = dict(iter(chanperms))
        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
        if diffperms != []:
            prep = [f'`{i}`' for i in diffperms]
            prep = '|'.join(prep)
            return await inchannel.send(content=f'Missing permissions [{prep}]')

        inchannel = inchannel.id

        logger = db.collection(u'servers').document(f'{ctx.guild.id}').get().to_dict().get('antiscamlog')

        embed = discord.Embed (
            title = 'Logging channel',
            description = f'Set {self.bot.get_channel(inchannel).mention} as logging channel?\n✅ Yes | 🚫 No',
            colour = discord.Colour(defaultcolour)
        )
        embed.set_author(name=f'Currently configuring for #{self.bot.get_channel(inchannel).name}')
        if logger != None:
            embed.set_footer(text=f'Note: This will replace #{self.bot.get_channel(logger).name} as the logging channel.')
        botmsg = await ctx.send(embed=embed)
        await botmsg.add_reaction('✅')
        await botmsg.add_reaction('🚫')
        
        def check(reaction, user):
            reactions = ['✅','🚫']
            return user == ctx.author and str(reaction.emoji) in reactions

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            print('timeout')
            return await botmsg.edit(embed=embederr('User took too long!'),delete_after=10.0)

        if str(reaction.emoji) == '✅':
            pass
        elif str(reaction.emoji) == '🚫':
            return await botmsg.edit(embed=embederr('Command cancelled.'),delete_after=10.0)

        localupdate(self.bot,ctx.guild.id,{u'antiscamlog': inchannel})

        donembed = discord.Embed (
            title = 'Success',
            color = discord.Colour.green(),
            description = f'Current antiscam Logging channel: {self.bot.get_channel(inchannel).mention}',
            )
        return await botmsg.edit(embed=donembed)

    @antiscam.command(brief='Sets action to take')
    @commands.guild_only()
    @owner_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def action(self,ctx,inchannel:discord.TextChannel=None):

        if inchannel == None:
            inchannel = ctx.channel
        else:
            inchannel = inchannel

        chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
        checkperms = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True)
        checkperms = dict(iter(checkperms))
        chanperms = dict(iter(chanperms))
        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
        if diffperms != []:
            prep = [f'`{i}`' for i in diffperms]
            prep = '|'.join(prep)
            return await inchannel.send(content=f'Missing permissions [{prep}]')

        actioner = db.collection(u'servers').document(f'{ctx.guild.id}').get().to_dict().get('antiscamaction')
        
        choices = {'1️⃣': 'Kick', '2️⃣': 'Ban', '3️⃣': 'Delete only'}
        texter = '\n'.join([f'{o} {choices[o]}' for o in choices])

        nline = '\n'
        embed = discord.Embed (
            title = 'Choose Anti-scam Action',
            description = f"Current action: `{actioner}`{nline}{nline}React to choose action taken when scam link detected.{nline}Delete will be done automatcially{nline}{texter}",
            colour = discord.Colour(defaultcolour)
        )
        embed.set_author(name=f'Currently configuring for #{inchannel.name}')
        botmsg = await ctx.send(embed=embed)
        for i in choices:
            await botmsg.add_reaction(i)

        def check(reaction, user):
            reactions = choices.keys()
            return user == ctx.author and str(reaction.emoji) in reactions

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            print('timeout')
            return await botmsg.edit(embed=embederr('User took too long!'),delete_after=10.0)

        action = choices[str(reaction.emoji)].lower()

        if action == 'kick':
            chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(kick_members=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                return await botmsg.edit(embed=embederr('Missing permissions: `kick_members`.\nPlease provide perms and rerun command.'),delete_after=10.0)
        
        elif action == 'ban':
            chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(ban_members=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                return await botmsg.edit(embed=embederr('Missing permissions: `ban_members`\nPlease provide perms and rerun command.'),delete_after=10.0)

        localupdate(self.bot,ctx.guild.id,{u'antiscamaction': action})

        okembed = discord.Embed (
            title='Success',
            colour = discord.Colour.green(),
            description = f'Current antiscam Action: `{action.capitalize()}`',
        )
        return await botmsg.edit(embed=okembed)

    @antiscam.command(brief='Resets antiscam for server')
    @commands.guild_only()
    @owner_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def reset(self,ctx,inchannel:discord.TextChannel=None):
        '''To reset for either notices or notifs'''

        if inchannel == None:
            inchannel = ctx.channel
        else:
            inchannel = inchannel

        chanperms = inchannel.permissions_for(ctx.guild.get_member(self.bot.user.id))
        checkperms = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True)
        checkperms = dict(iter(checkperms))
        chanperms = dict(iter(chanperms))
        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
        if diffperms != []:
            prep = [f'`{i}`' for i in diffperms]
            prep = '|'.join(prep)
            return await inchannel.send(content=f'Missing permissions [{prep}]')

        inchannel = inchannel.id
            
        doc = db.collection(u'servers').document(f'{ctx.guild.id}').get()
        if doc.exists:
            serverdict = db.collection(u'servers').document(f'{ctx.guild.id}').get().to_dict()
            action = serverdict.get('antiscamaction')
            log = serverdict.get('antiscamlog')
        else:
            return await ctx.send(embed=embederr('No configurations for this server found!'),delete_after=10.0)

        reactions = []
        if log == None:
            reactions = reactions + ['1️⃣']
        reactions = reactions + ['2️⃣']
        reactions = reactions + ['🚫']

        msgs = {'1️⃣': 'Logging', '2️⃣': 'Disable Antiscam for server', '🚫': 'Cancel'}
        texter = '\n'.join([f'{o} {msgs[o]}' for o in msgs if o in reactions])

        configembed = discord.Embed(
            title = 'Reset Configurations',
            description = f'React to reset that configuration\n{texter}',
            colour = discord.Colour(defaultcolour)
        )
        configembed.set_author(name=f'Currently configuring for {self.bot.get_channel(inchannel).name}')
        configmsg = await ctx.send(embed=configembed)
        for i in reactions:
            await configmsg.add_reaction(i)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await configmsg.clear_reactions()
            return await configmsg.edit(embed=embederr('Timeout'),delete_after=10.0)
        else:
            await configmsg.clear_reactions()
            if str(reaction.emoji) == '1️⃣':
                
                localdelete(self.bot,ctx.guild.id,'antiscamlog')
            
            elif str(reaction.emoji) == '2️⃣':
                
                localdelete(self.bot,ctx.guild.id,'antiscamaction')
                localdelete(self.bot,ctx.guild.id,'antiscamlog')
                localdelete(self.bot,ctx.guild.id,'antiscam')

            elif str(reaction.emoji) == '🚫':
                return await configmsg.edit(embed=embederr('Command cancelled'),delete_after=10.0)

            successembed = discord.Embed(
                title = 'Reset success',
                description = f'{msgs[str(reaction.emoji)]} reset for {self.bot.get_channel(inchannel).mention} successful',
                colour = discord.Colour(defaultcolour)
            )
            return await configmsg.edit(embed=successembed)

    @commands.command(brief='Check channels working with antiscam')
    @commands.guild_only()
    @owner_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def antiscamcheck(self,ctx):

        guilddict = self.bot.serverdicters[str(ctx.guild.id)]

        checkembed = discord.Embed(
            title = 'Antiscam Checkup',
            description = 'Scanning in progress',
            color = discord.Color(defaultcolour)
        )
        botmsg = await ctx.send(embed=checkembed)

        checkembed = discord.Embed(
            title = 'Antiscam Checkup',
            color = discord.Color.green()
        )
        
        channels = ctx.guild.text_channels
        badchannels = []
        for channel in channels:
            chanperms = channel.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(manage_messages=True, embed_links=True, read_messages=True, send_messages=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                prep = [f'`{i}`' if i != 'manage_messages' else f'⚠️`{i}`' for i in diffperms]
                prep = '|'.join(prep)
                badchannels.append(f'{channel.mention} Missing:\n[{prep}]')

        if guilddict.get('antiscamlog') != None:
            logchan = self.bot.get_channel(int(guilddict.get('antiscamlog')))
            chanperms = logchan.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(read_messages=True, send_messages=True, embed_links=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                prep = [f'`{i}`' for i in diffperms]
                prep = '|'.join(prep)
                checkembed.add_field(name='Logging',value=f'{logchan.mention}\n⚠️ Missing: {prep}',inline=False)
            else:
                checkembed.add_field(name='Logging',value=f'{logchan.mention}\n✅ All ok',inline=False)

        if guilddict.get('antiscamaction') != None:
            if guilddict.get('antiscamaction') != 'delete only':
                action = guilddict.get('antiscamaction')
                chanperms = logchan.permissions_for(ctx.guild.get_member(self.bot.user.id))
                if action == 'kick':
                    checkperms = discord.Permissions(kick_members=True)
                elif action == 'ban':
                    checkperms = discord.Permissions(ban_members=True)
                checkperms = dict(iter(checkperms))
                chanperms = dict(iter(chanperms))
                checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
                diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
                if diffperms != []:
                    prep = [f'`{i}`' for i in diffperms]
                    prep = '|'.join(prep)
                    checkembed.add_field(name='Action',value=f'⚠️ Missing: {prep}',inline=False)
                else:
                    checkembed.add_field(name='Action',value=f'✅ All ok',inline=False)

        if len(badchannels) > 0:
            text = '\n'.join(badchannels)
            checkembed.description = "**Channels**\n" + f'{text}'
        else:
            checkembed.description = "**Channels**\n" + '✅ All channels able to access'

        checkembed.set_footer(text='Please check if channels that should be protected have permissions granted.\nYou can ignore channels where users do not use.\nmanage_messages is required at least to remove bad messages in protected channels.')
        await botmsg.edit(embed=checkembed)

async def setup(bot):
    await bot.add_cog(AntiScam(bot))
