import discord
from discord.ext import commands
import asyncio
from discord.errors import HTTPException

logger_id = 950192276183875624
defaultcolour = 0x70f3f3
profcolours = [0x70f3f3, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class AttachmentLogger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def owner_or_permissions(**perms):
        original = commands.has_permissions(**perms).predicate
        async def extended_check(ctx):
            if ctx.guild is None:
                return False
            return ctx.guild.owner_id == ctx.author.id or  ctx.author.id == 283790768252911619 or await original(ctx)
        return commands.check(extended_check)

    @commands.Cog.listener()
    async def on_message(self,message):

        if message.guild == None or message.author.id == self.bot.user.id:
            return
        
        # force only SLime IM Memories 
        if message.guild.id != 885095339885989942:
            return

        if message.author != None:
            if len(message.attachments) > 0:
                imagelist = []
                imagelister = []
                for attachmenter in message.attachments:

                    try:
                        async def saveattach():
                            await attachmenter.save(f'cache/{attachmenter.filename}', use_cached=False)
                        await asyncio.wait_for(saveattach(), timeout=300.0)
                    except HTTPException:
                        try:
                            async def saveattacher():
                                await attachmenter.save(f'cache/{attachmenter.filename}', use_cached=True)
                            await asyncio.wait_for(saveattacher(), timeout=300.0)
                        except HTTPException:
                            continue
                        finally:
                            pass
                    finally:
                        pass

                    imagelist.append(f'cache/{attachmenter.filename}')
                    imagelister.append(attachmenter.filename)

                embed = discord.Embed(
                    description = f'[Link to message]({message.jump_url})\nImage sent by {message.author.mention} in {message.channel.mention}.',
                    colour = discord.Color.blue()
                )
                embed.set_author(name=str(message.author),icon_url=message.author.display_avatar.url)
                embed.set_footer(text=f'Message ID: {message.id}')
                if message.content != None and message.content != '':
                    embed.add_field(name='Message',value=message.content,inline=False)

                logchannel = self.bot.get_channel(logger_id)

                embed.add_field(name='Attachments',value='\n'.join(imagelister),inline=False)
                if len(imagelist) == 1:
                    await logchannel.send(file=discord.File(imagelist[0]),embed=embed)
                else:
                    await logchannel.send(files=[discord.File(i) for i in imagelist],embed=embed)

    @commands.command(brief='Check channels working with attachmentlog')
    @commands.guild_only()
    @owner_or_permissions(manage_guild=True)
    @commands.bot_has_permissions(read_messages=True,send_messages=True,add_reactions=True,embed_links=True)
    async def attachmentlogcheck(self,ctx):

        checkembed = discord.Embed(
            title = 'Attachment Log Checkup',
            description = 'Scanning in progress',
            color = discord.Color(defaultcolour)
        )
        botmsg = await ctx.send(embed=checkembed)

        checkembed = discord.Embed(
            title = 'Attachment Log',
            color = discord.Color.green()
        )
        
        channels = ctx.guild.text_channels
        badchannels = []
        for channel in channels:
            chanperms = channel.permissions_for(ctx.guild.get_member(self.bot.user.id))
            checkperms = discord.Permissions(read_messages=True)
            checkperms = dict(iter(checkperms))
            chanperms = dict(iter(chanperms))
            checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
            diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
            if diffperms != []:
                prep = [f'`{i}`' if i != 'read_messages' else f'`{i}`' for i in diffperms]
                prep = '|'.join(prep)
                badchannels.append(f'{channel.mention} Missing:\n[{prep}]')

        logchan = self.bot.get_channel(logger_id)
        chanperms = logchan.permissions_for(ctx.guild.get_member(self.bot.user.id))
        checkperms = discord.Permissions(read_messages=True)
        checkperms = dict(iter(checkperms))
        chanperms = dict(iter(chanperms))
        checkperms = {i:checkperms[i] for i in checkperms if checkperms[i] == True}
        diffperms = [i for i in checkperms if checkperms[i] != chanperms[i]]
        if diffperms != []:
            prep = [f'`{i}`' for i in diffperms]
            prep = '|'.join(prep)
            checkembed.add_field(name='Logging',value=f'{logchan.mention}\nMissing: {prep}',inline=False)
        else:
            checkembed.add_field(name='Logging',value=f'{logchan.mention}\n✅ All ok',inline=False)

        if len(badchannels) > 0:
            text = '\n'.join(badchannels)
            checkembed.description = "**Channels**\n" + f'{text}'
        else:
            checkembed.description = "**Channels**\n" + '✅ All channels able to access'

        checkembed.set_footer(text='Please check if channels that should be protected have permissions granted.\nYou can ignore channels where users do not use.\nmanage_messages is required at least to remove bad messages in protected channels.')
        await botmsg.edit(embed=checkembed)

async def setup(bot):
    await bot.add_cog(AttachmentLogger(bot))