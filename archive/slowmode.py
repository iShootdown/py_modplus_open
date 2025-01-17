import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Range, Choice
from firebase_admin import firestore
from typing import Optional
from time import time as nowtime

### ONLY WORKS FOR ONE SERVER ###

# Use a service account
db = firestore.client()

def embederr(msg):
	embederror = discord.Embed (
		title = 'Error',
		description = str(msg),
		color = discord.Colour.red(),
	)
	return embederror

def localupdate(bot,guild,dicter):
	gdict = bot.serverdicters[str(guild)]
	for key in dicter.keys():
		gdict[key] = dicter[key]
	
	dicts = bot.serverdicters
	dicts[str(guild)] = gdict
	bot.serverdicters = dicts

	db.collection(u'servers').document(f'{guild}').update(dicter)

def localslowupdate(bot,userid,dicter):
	gdict = bot.slowdicters.get(str(userid))
	setter = False
	if gdict == None:
		gdict = dicter
		setter = True
	for key in dicter.keys():
		gdict[key] = dicter[key]
	
	dicts = bot.slowdicters
	dicts[str(userid)] = gdict
	bot.slowdicters = dicts

	if setter:
		db.collection(u'slowmode').document(f'{userid}').set(dicter)
	else:
		db.collection(u'slowmode').document(f'{userid}').update(dicter)

def localslowdelete(bot,userid,key):
	gdict = bot.slowdicters[str(userid)]
	if key in gdict:
		del gdict[key]
	else:
		return
	
	dicts = bot.slowdicters
	dicts[str(userid)] = gdict
	bot.slowdicters = dicts

	db.collection(u'slowmode').document(f'{userid}').update({key:firestore.DELETE_FIELD})

defaultcolour = 0xcaeffe
regions = ['North & South America', 'Europe and Others', 'Asia Pacific', 'Japan']
profcolours = [0xcaeffe, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class Slowmode(commands.GroupCog, group_name='slowmode'):

	def __init__(self, bot):
		self.bot = bot

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def messages(self,interaction:discord.Interaction,slowuser:discord.Member,count:Range[int,1,None],hours:Optional[int]=0,minutes:Optional[int]=0,seconds:int=0):
		''' Slowmode for x number of messages sent in x amount of time '''

		time = hours*60*60 + minutes*60 + seconds
		if time < 1:
			return await interaction.response.send_message(embed=embederr("No time specified"), ephemeral=True)
		
		updatedict = {"messages": {"count": count, "time": time, "firsttime": None, "countremain": None}}
		localslowupdate(self.bot,slowuser.id,updatedict)

		success_embeed = discord.Embed(
			colour = discord.Colour.green(),
			title = "Messages Slowmode"
		)
		success_embeed.add_field(name="User",value=slowuser.mention)
		success_embeed.add_field(name="Slowmode",value=f"`{count}` message(s) per `{time}` seconds")

		return await interaction.response.send_message(embed=success_embeed)
		
	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def characters(self,interaction:discord.Interaction,slowuser:discord.Member,count:Range[int,1,None],hours:Optional[int]=0,minutes:Optional[int]=0,seconds:int=0):
		''' Slowmode for x number of characters sent in x amount of time '''

		time = hours*60*60 + minutes*60 + seconds
		if time < 1:
			return await interaction.response.send_message(embed=embederr("No time specified"), ephemeral=True)
		
		updatedict = {"characters": {"count": count, "time": time, "firsttime": None, "countremain": None}}
		localslowupdate(self.bot,slowuser.id,updatedict)

		success_embeed = discord.Embed(
			colour = discord.Colour.green(),
			title = "Characters Slowmode"
		)
		success_embeed.add_field(name="User",value=slowuser.mention)
		success_embeed.add_field(name="Slowmode",value=f"`{count}` character(s) per `{time}` seconds")

		return await interaction.response.send_message(embed=success_embeed)

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def charpermsg(self,interaction:discord.Interaction,slowuser:discord.Member,count:Range[int,1,None]):
		''' Limit character amount in messages '''
		
		updatedict = {"charpermsg": {"count": count}}
		localslowupdate(self.bot,slowuser.id,updatedict)

		success_embeed = discord.Embed(
			colour = discord.Colour.green(),
			title = "Characters Per Message Limit"
		)
		success_embeed.add_field(name="User",value=slowuser.mention)
		success_embeed.add_field(name="Limit",value=f"`{count}` characters per message")

		return await interaction.response.send_message(embed=success_embeed)

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def check(self,interaction:discord.Interaction,slowuser:discord.Member):
		''' Check slowmode for user '''

		slowdicter = self.bot.slowdicters.get(str(slowuser.id))
		if slowdicter == None:
			return await interaction.response.send_message(embed=embederr("No slowmode configuration found"))
		
		showembed = discord.Embed(
			title="Slowmode",
			description=f"Showing slowmode for {slowuser.id}",
			color=discord.Colour(defaultcolour)
		)
		if "messages" in slowdicter:
			messagedicter = slowdicter["messages"]
			if messagedicter['firsttime'] != None:
				time_left = int(nowtime()) - messagedicter['firsttime']
				if time_left < 0:
					time_left = None
			else:
				time_left = None
			showembed.add_field(name="Messages", value=f"`{messagedicter['count']}` messages per `{messagedicter['time']}` seconds\nRemaining count: `{messagedicter['countremain']}`\nTime left: `{time_left}`")

		if "characters" in slowdicter:
			chardicter = slowdicter["characters"]
			if chardicter['firsttime'] != None:
				time_left = int(nowtime()) - chardicter['firsttime']
				if time_left < 0:
					time_left = None
			else:
				time_left = None
			showembed.add_field(name="Characters", value=f"`{chardicter['count']}` characters per `{chardicter['time']}` seconds\nRemaining count: `{chardicter['countremain']}`\nTime left: `{time_left}`")

		if "charpermsg" in slowdicter:
			showembed.add_field(name="Char Per Msg", value=f"`{slowdicter['charpermsg']['count']}` characters per message")

		serverdicter = self.bot.serverdicters.get(str(interaction.guild_id))
		if serverdicter.get("slowrole") == None:
			slowrole = None
		else:
			slowrole = interaction.guild.get_role(serverdicter["slowrole"])
			if slowrole in slowuser.roles:
				slowmode_active = True
			else:
				slowmode_active = False
		showembed.add_field(name="Slowmode Role", value=f"{slowrole.mention}")
		showembed.add_field(name="Slowmode Active", value=f"{slowmode_active}")

		return await interaction.response.send_message(embed=showembed)

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def setrole(self,interaction:discord.Interaction,role:discord.Role):
		''' Set role to assign when slowmode active '''

		localupdate(self.bot,interaction.guild_id,{"slowrole": role.id})
		return await interaction.response.send_message(f"Slowmode role set to {role.mention}")

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def setlogs(self,interaction:discord.Interaction,channel:discord.TextChannel):
		''' Set channel to send logs when slowmode active '''

		localupdate(self.bot,interaction.guild_id,{"slowlogger": channel.id})
		return await interaction.response.send_message(f"Slowmode logs channel set to {channel.mention}")

	@app_commands.command()
	@app_commands.guild_only()
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.choices(
		kind = [Choice(name=u,value=u) for u in ["messages", "characters", "charpermsg", "all"]]
		)
	async def delete(self,interaction:discord.Interaction,slowuser:discord.Member,kind:Choice[str]):
		''' Delete selected slowmode per user '''

		slowdicter = self.bot.slowdicters.get(str(slowuser.id))
		if slowdicter == None or slowdicter == {}:
			return await interaction.response.send_message(embed=embederr("No slowmode configuration found"),ephemeral=True)
		
		if kind.value == 'all':
			db.collection("slowmode").document(str(slowuser.id)).delete()
			del self.bot.slowdicters[str(slowuser.id)]
			return await interaction.response.send_message(f"Delete {slowuser.mention} {kind.value} slowmode success")
		elif kind.value in slowdicter.keys():
			localslowdelete(self.bot,slowuser.id,kind.value)
			return await interaction.response.send_message(f"Delete {slowuser.mention} {kind.value} slowmode success")
		else:
			return await interaction.response.send_message(embed=embederr(f"No {kind.value} slowmode configuration found"),ephemeral=True)

async def setup(bot):
	await bot.add_cog(Slowmode(bot))