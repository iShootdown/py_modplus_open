import discord
from discord.ext import commands
import asyncio
import re
# Use a service account

botprefix = 'm+'

def stringclean(string):
	string = string.strip(' \n')
	return string

def embederr(msg):
	embederror = discord.Embed (
		title = 'Error',
		description = str(msg),
		color = discord.Colour.red(),
	)
	return embederror

defaultcolour = 0xcaeffe
regions = ['North & South America', 'Europe and Others', 'Asia Pacific', 'Japan']
profcolours = [0xcaeffe, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class Embed(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
   
	@commands.group(brief='Create/edit embed messages', case_insensitive=True)
	@commands.guild_only()
	@commands.has_permissions(read_messages=True,send_messages=True,manage_messages=True,embed_links=True,attach_files=True)
	async def embed(self,ctx):
		''' Use subcommands below to modify embeds\nPlease set embed channel first using `embed channel <channel>`'''
		if ctx.invoked_subcommand is None:
			await ctx.invoke(self.bot.get_command('help'), cmdr=ctx.command.name)

	@embed.command()
	@commands.guild_only()
	@commands.has_permissions(read_messages=True,send_messages=True,manage_messages=True,embed_links=True,attach_files=True)
	async def create(self,ctx,guildchannel:discord.TextChannel=None):
		''' Create a message within channel from set embed channel '''
		if guildchannel == None:
			guildchannel = ctx.channel
	
		def verify(m):
			return m.author.id == ctx.author.id

		editembed = discord.Embed (
			title =  'Embed Editor',
			color = discord.Colour(defaultcolour),
			description = '''Setting up editor''',
		)
		editembed.set_footer(text='Channel: %s' % guildchannel.name)
		botmsg = await ctx.send(embed=editembed)

		parameters = ['Enter a title', 'Enter a description', 'Enter an image link', 'Enter a footer', 'Enter a hex code for colour or choose from list below \n ```List of preset colours: \n0. Default (Light blue)\n1. Red\n2. Orange\n3. Yellow\n4. Green\n5. Blue\n6. Purple\n7. Pink\n8. White\n9. Black```']
		input_parameters = []

		filer = None
		for i in range(len(parameters)):
			editembed = discord.Embed (
				title =  'Embed Editor (%d/%s)' % (i+1,len(parameters)),
				color = discord.Colour(defaultcolour),
				description = '%s \n\n Type `skip` to skip this stage.' % parameters[i],
			)
			editembed.set_footer(text='Channel: %s' % guildchannel.name)
			await botmsg.edit(embed=editembed)

			try:
				msginput = await self.bot.wait_for('message', check=verify, timeout=30.0)
			except asyncio.TimeoutError:
				print('timeout')
				return await botmsg.edit(embed=embederr('User took too long!'))

			if msginput.content.lower() == 'skip':
				await msginput.delete()
				if (i+1) == 5:
					input_parameters.append(defaultcolour)
				else:
					input_parameters.append(None)

			elif (i+1) == 3:

				if 'http://' in msginput.content or 'https://' in msginput.content:
					input_parameters.append(msginput.content)
					await msginput.delete()
				elif len(msginput.attachments) > 0:
					attachmenter = msginput.attachments[0]
					await attachmenter.save(f'cache/temp_image.png')
					filer = discord.File("cache/temp_image.png",filename="temp_image")
					input_parameters.append(f"file://temp_image")
					await msginput.delete()
				else:
					return await botmsg.edit(embed=embederr('Invalid image'))
			
			elif (i+1) == 5:
				if len(msginput.content) == 1 and msginput.content.isdigit:
					input_parameters.append(profcolours[int(msginput.content)])
					await msginput.delete()
					
				elif len(msginput.content) == 6 and re.search(r'^[0-9A-Fa-f]+$', msginput.content) != None:
					pickcolour = '0x' + msginput.content
					input_parameters.append(int(pickcolour, 16))
					await msginput.delete()

				else:
					await msginput.delete()
					return await botmsg.edit(embed=embederr('Invalid colour input.'))
			
			else:
				await msginput.delete()
				input_parameters.append(msginput.content)

		print(input_parameters)
		sendembed = discord.Embed (
			title = input_parameters[0],
			description = input_parameters[1],
			color = discord.Colour(input_parameters[4]),
		)
		if input_parameters[2] != None:
			sendembed.set_image(url=input_parameters[2])
		
		if input_parameters[3] != None:
			sendembed.set_footer(text=input_parameters[3])

		if filer == None:
			await guildchannel.send(embed=sendembed)
		else:
			await guildchannel.send(file=filer,embed=sendembed)

		yesembed = discord.Embed (
			title = 'Success',
			description = 'Embed message successfully sent.',
			color = discord.Colour.green(),
		)
		return await botmsg.edit(embed=yesembed)

	@embed.command()
	@commands.guild_only()
	@commands.has_permissions(read_messages=True,send_messages=True,manage_messages=True,embed_links=True,attach_files=True)
	async def edit(self,ctx,guildchannel:discord.TextChannel=None,messageid=None):
		''' Edit the message within channel from set embed channel '''

		if guildchannel == None:
			return await ctx.send(embed=embederr('No channel ID'))

		def verify(m):
			return m.author.id == ctx.author.id

		if messageid == None:
			editembed = discord.Embed (
				title =  'Embed Editor',
				color = discord.Colour(defaultcolour),
				description = 'Enter the message ID',
			)
			editembed.set_footer(text='To get Message ID, first make sure Settings > Apperance > Developer Mode is ON.\n Then, on the `...` for that message, click `Copy ID`.')
			botmsg = await ctx.send(embed=editembed)

			try:
				msginput = await self.bot.wait_for('message', check=verify, timeout=20.0)
			except asyncio.TimeoutError:
				print('timeout')
				return await botmsg.edit(embed=embederr('User took too long!'))

			if msginput.content.isdigit() and len(msginput.content) == 18:
				directmsg = await guildchannel.fetch_message(int(msginput.content))
				thatmsgid = int(msginput.content)
				directembed = directmsg.embeds
				directembed = directembed[0]
				msgdict = directembed.to_dict()
				print(msgdict)
				await msginput.delete()
			else:
				await msginput.delete()
				return await botmsg.edit(embed=embederr('Invalid input.'))
		else:
			messageid = int(messageid)

		editembed = discord.Embed (
			title =  'Embed Editor',
			color = discord.Colour(defaultcolour),
			description = 'Choose what to edit:\n```1. Title\n2. Description\n3. Image link\n4. Footer\n5. Colour```',
		)
		editembed.set_footer(text='Message ID: %s' % thatmsgid)
		await botmsg.edit(embed=editembed)

		try:
			msginput = await self.bot.wait_for('message', check=verify, timeout=20.0)
		except asyncio.TimeoutError:
			print('timeout')
			return await botmsg.edit(embed=embederr('User took too long!'))

		parameters = ['Enter a title', 'Enter a description', 'Enter an image link', 'Enter a footer', 'Enter a hex code for colour or choose from list below \n ```List of preset colours: \n0. Default (Light blue)\n1. Red\n2. Orange\n3. Yellow\n4. Green\n5. Blue\n6. Purple\n7. Pink\n8. White\n9. Black```']

		if msginput.content in ['1', '2', '3', '4', '5']:
			chosenfield = int(msginput.content) - 1
			await msginput.delete()
		else:
			await msginput.delete()
			return await botmsg.edit(embed=embederr('Invalid input.'))

		editembed = discord.Embed (
			title =  'Embed Editor',
			color = discord.Colour(defaultcolour),
			description = '%s \n\n Type `skip` to skip (this will become empty).' % parameters[chosenfield],
		)
		editembed.set_footer(text='Channel: %s Message: %s' % (guildchannel.name,thatmsgid))
		await botmsg.edit(embed=editembed)

		try:
			msginput = await self.bot.wait_for('message', check=verify, timeout=30.0)
		except asyncio.TimeoutError:
			print('timeout')
			return await botmsg.edit(embed=embederr('User took too long!'))

		pparameters = ['title', 'description', 'image', 'footer', 'color']

		if msginput.content.lower() == 'skip':
			await msginput.delete()
			if (chosenfield+1) == 5:
				msgdict[pparameters[chosenfield]] = defaultcolour
			else:
				msgdict.pop(pparameters[chosenfield])

		elif (chosenfield+1) == 3:
			if 'http://' in msginput.content or 'https://' in msginput.content:
				tempdict = {'url': msginput.content}
				msgdict[pparameters[chosenfield]] = tempdict
				await msginput.delete()
			else:
				return await botmsg.edit(embed=embederr('Invalid link'))

		elif (chosenfield+1) == 5:
			if len(msginput.content) == 1 and msginput.content.isdigit:
				msgdict[pparameters[chosenfield]] = profcolours[int(msginput.content)]
				await msginput.delete()
				
			elif len(msginput.content) == 6 and re.search(r'^[0-9A-Fa-f]+$', msginput.content) != None:
				pickcolour = '0x' + msginput.content
				msgdict[pparameters[chosenfield]] = int(pickcolour, 16)
				await msginput.delete()

			else:
				await msginput.delete()
				return await botmsg.edit(embed=embederr('Invalid colour input.'))

		elif (chosenfield+1) == 4:
			tempdict = {'text': msginput.content}
			msgdict[pparameters[chosenfield]] = tempdict
			await msginput.delete()

		else:
			await msginput.delete()
			msgdict[pparameters[chosenfield]] = msginput.content

		editedembed = discord.Embed.from_dict(msgdict)
		await directmsg.edit(embed=editedembed)
		print(msgdict)

		yesembed = discord.Embed (
			title = 'Success',
			description = 'Embed message successfully edited.',
			color = discord.Colour.green(),
		)
		return await botmsg.edit(embed=yesembed)

async def setup(bot):
	await bot.add_cog(Embed(bot))