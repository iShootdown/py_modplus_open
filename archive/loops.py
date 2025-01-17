import discord
from discord.ext import commands, tasks
from firebase_admin import firestore
import os
import shutil
import cv2
import numpy as np
import pytesseract
import asyncio
from time import time as nowtime

db = firestore.client()

def embederr(msg):
	embederror = discord.Embed (
		title = 'Error',
		description = str(msg),
		color = discord.Colour.red(),
	)
	return embederror

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

	return bot

def localonslowupdate(bot,userid,dicter):
	gdict = bot.onslowmodedicters.get(str(userid))
	setter = False
	if gdict == None:
		gdict = dicter
		setter = True
	for key in dicter.keys():
		gdict[key] = dicter[key]
	
	dicts = bot.onslowmodedicters
	dicts[str(userid)] = gdict
	bot.onslowmodedicters = dicts

	if setter:
		db.collection('onslowmode').document(f'{userid}').set(dicter)
	else:
		db.collection('onslowmode').document(f'{userid}').update(dicter)

def localonslowdocdelete(bot,userid):
	del bot.onslowmodedicters[userid]
	db.collection(u'onslowmode').document(f'{userid}').delete()

defaultcolour = 0x70f3f3
profcolours = [0x70f3f3, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class Loopers(commands.Cog):

	def __init__(self,bot):
		self.bot = bot
		self.remove_slowmode.start()
		self.cacheclear.start()

	def cog_unload(self):
		self.remove_slowmode.stop()
		self.cacheclear.stop()

	@commands.Cog.listener()
	async def on_message(self,message):

		# ignore dms
		if message.guild == None or message.author.id == self.bot.user.id:
			return

		serverdicter = self.bot.serverdicters.get(str(message.guild.id))
		if serverdicter == None:
			return

		# ignore author
		if message.author.bot:
			return

		# epverify
		if message.channel.id == 918292285588914186:
			epurole = 918290858024005642
			guildepu = message.guild.get_role(epurole)
			iseserver = self.bot.get_guild(885095339885989942)
			groles = iseserver.roles
			grolesid = [i.id for i in groles]
			epuroles = groles[grolesid.index(889811580265562113)+1:grolesid.index(918998439658926082)]

			if len(message.attachments) != 1:
				await message.channel.send(f'{message.author.mention} No attachments found, please upload an image.')
				await message.delete()
				return
			
			num = 0
			try:
				attachmenter = message.attachments[0]
				if not os.path.isdir('./cache'):
					os.mkdir('./cache')
					
				await attachmenter.save(f'cache/{attachmenter.filename}')
				img = cv2.imread(f'cache/{attachmenter.filename}')

				h,w,_ = img.shape

				(b, g, r) = img[0,0]
				count = 0
				if b < 3 and g < 3 and r < 3:
					for i in range(w):
						if img[:,i].mean() < 3.0:
							count+=1
						else:
							break
					
				if count != 0:
					img = img[:,count:w]
				else:
					ww = w-1
					(b, g, r) = img[0,ww]
					count = ww
					if b < 3 and g < 3 and r < 3:
						for i in range(ww,-1,-1):
							if img[:,i].mean() < 3.0:
								count = i
							else:
								break
					
					if count != ww:
						img = img[:,0:count]

				h,w,_ = img.shape
				#finding 16/9

				currentres = w/h
				if currentres == 16/9:
					pass

				elif currentres > 16/9:
					midw = int(round(w/2,0))
					neww = h/9*16
					sw = midw-int(round(neww/2,0))
					img = img[:,sw:sw+int(round(neww,0))]

				elif currentres < 16/9:
					midh = int(round(h/2,0))
					newh = w/16*9
					sh = midh-int(round(newh/2,0))
					img = img[sh:sh+int(round(newh,0)),:]
				h,w,_ = img.shape
				nimg = img[int(round(h/1.74,0)):int(round(h*0.636,0)),int(round(w/3.1,0)):int(round(w/2.45,0))]

				colour1 = np.asarray([160, 160, 160]) # improve visibility
				colour2 = np.asarray([255, 255, 255])
				mask = cv2.inRange(nimg, colour1, colour2)
				img_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
				await asyncio.sleep(0.5)
				text = pytesseract.image_to_string(img_rgb, config='--psm 7')
				if text != '':
					num = int(''.join([str(i) for i in text if i.isnumeric()]))

				epuroles.reverse()
				epurolesdict = {int(role.name.lower().split('k')[0])*1000:role for role in epuroles}
				
				neweprole = None
				for key in epurolesdict.keys():
					if num > key:
						neweprole = epurolesdict[key]
						break

			except Exception as e:
				print(e)
				return

			if num > 10000:
				botmsg = await message.channel.send(f'{message.author.mention} Your EP is {num}, role will be given shortly...')
			else:
				botmsg = await message.channel.send(f'Bot failed to read your EP, role will be assigned manually.')
				return await message.delete()

			try:
				repuroles = epuroles
				await message.author.remove_roles(*repuroles,reason='Automatic action for adding screenshot')
				if neweprole == None:
					await message.author.add_roles(guildepu,reason='Automatic action for adding screenshot')
				else:
					bporoles = [guildepu,neweprole]
					await message.author.add_roles(*bporoles,reason='Automatic action for adding screenshot')
				
				await botmsg.edit(content=f'Your EP is {num}, EP role given', delete_after=10.0)

			except Exception as e:
				print(e)
				return
			
			return
		
		# check for slowmode
		slowdicter = self.bot.slowdicters.get(str(message.author.id))
		if slowdicter == None:
			return
		
		# flags
		deletemsg = False
		slowmode_on = False

		now_time = int(nowtime())

		if "charpermsg" in slowdicter:
			counter = slowdicter['charpermsg']["count"]
			if len(message.content) > counter:
				deletemsg = True

		lasttime = None

		if "messages" in slowdicter:
			messagedict = slowdicter['messages']
			timer = messagedict["time"]
			firsttime = messagedict["firsttime"]
			counter = messagedict["count"]
			remainder = messagedict["countremain"]

			if remainder == None:
				firsttime = now_time
				remainder = counter-1
			else:
				remainder -= 1

			if now_time < firsttime + timer:
				if remainder <= 0:
					slowmode_on = True
					lasttime = firsttime + timer
			else:
				firsttime = now_time
				remainder = counter-1
				if remainder <= 0:
					slowmode_on = True
					lasttime = firsttime + timer

			messagedict["time"] = timer
			messagedict["firsttime"] = firsttime
			messagedict["count"] = counter
			messagedict["countremain"] = remainder
			localslowupdate(self.bot,message.author.id,{"messages": messagedict})
					
		if "characters" in slowdicter:
			characterdict = slowdicter['characters']
			timer = characterdict["time"]
			firsttime = characterdict["firsttime"]
			counter = characterdict["count"]
			remainder = characterdict["countremain"]

			msglen = sum(not chr.isspace() for chr in message.content)

			if remainder == None:
				firsttime = now_time
				remainder = counter - msglen
			else:
				remainder -= msglen

			if remainder <= 0:
				if now_time < firsttime + timer:
					slowmode_on = True
					lasttime = firsttime + timer
				else:
					firsttime = now_time
					remainder = counter - msglen
					if remainder <= 0:
						slowmode_on = True
						lasttime = firsttime + timer

			characterdict["time"] = timer
			characterdict["firsttime"] = firsttime
			characterdict["count"] = counter
			characterdict["countremain"] = remainder
			localslowupdate(self.bot,message.author.id,{"characters": characterdict})
		
		if slowmode_on:
			slowlogger = serverdicter.get("slowlogger")
			slowrole = serverdicter.get("slowrole")
			if slowrole != None:
				localonslowupdate(self.bot,message.author.id,{"guild_id": message.guild.id, "lasttime": lasttime, "role_id": slowrole})
				await message.author.add_roles(message.guild.get_role(slowrole),reason="Slowmode applied")
				await message.guild.get_channel(slowlogger).send(embed=discord.Embed(description=f"Slowmode applied for {message.author.mention}, expiring <t:{lasttime}:R>"))
			else:
				if slowlogger != None:
					await message.guild.get_channel(slowlogger).send(embed=embederr(f"No role to apply slowmode for {message.author.mention}"))

		if deletemsg:
			await message.delete()

	@commands.Cog.listener()
	async def on_message_delete(self,message):
		
		if message.guild == None or message.author.id == self.bot.user.id:
			return
		
		serverdicter = self.bot.serverdicters.get(str(message.guild.id))
		if serverdicter == None:
			return

		if message.author.bot:
			return

		if message.channel.id == 918292285588914186:
			epurole = 918290858024005642
			iseserver = self.bot.get_guild(885095339885989942)
			groles = iseserver.roles
			grolesid = [i.id for i in groles]
			epuroles = groles[grolesid.index(889811580265562113)+1:grolesid.index(918998439658926082)]
			memberroles = [i.id for i in message.author.roles]
			epuroler = [i for i in memberroles if i in epuroles]
			guildepu = message.guild.get_role(epurole)
			cepuroles = [guildepu]+epuroler
			await message.author.remove_roles(*cepuroles,reason='Automatic action for removing screenshot')
			return

	@tasks.loop(seconds=1,count=None)
	async def remove_slowmode(self):
		''' Remove slowmode after time passed '''

		onslowmodedicters = self.bot.onslowmodedicters
		keys = list(onslowmodedicters.keys())
		for userid in keys:
			if onslowmodedicters[userid].get("lasttime") != None:
				
				onslowdict = onslowmodedicters[userid]
				
				if int(nowtime()) > onslowdict["lasttime"]:
					
					guilder = self.bot.get_guild(onslowdict["guild_id"])
					slowuser = guilder.get_member(int(userid))
					slowrole = guilder.get_role(onslowdict["role_id"])
					await slowuser.remove_roles(slowrole, reason="Remove slowmode role")
					
					serverdicter = self.bot.serverdicters.get(str(onslowdict["guild_id"]))
					slowlogger = serverdicter.get("slowlogger")
					if slowlogger != None:
						await guilder.get_channel(int(slowlogger)).send(embed=discord.Embed(description=f"Slowmode removed for {slowuser.mention}"))
					
					localonslowdocdelete(self.bot,userid)
					
					slowdicter = self.bot.slowdicters[userid]
					if "messages" in slowdicter:
						slowdicter["messages"]["countremain"] = None
						slowdicter["messages"]["firsttime"] = None
					if "characters" in slowdicter:
						slowdicter["characters"]["countremain"] = None
						slowdicter["characters"]["firsttime"] = None
					localslowupdate(self.bot,userid,slowdicter)

	# @tasks.loop(minutes=5,count=None)
	# async def clocktiming(self):
	#     # now_utc = datetime.datetime.now(pytz.timezone('UTC'))
	#     # now_utc_str = now_utc.strftime("%H:%M")
	#     now_pst = datetime.datetime.now(pytz.timezone('PST8PDT'))
	#     now_pst_str = now_pst.strftime("%H:%M")
	#     now_cet = datetime.datetime.now(pytz.timezone('CET'))
	#     now_cet_str = now_cet.strftime("%H:%M")
	#     now_jst = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
	#     now_jst_str = now_jst.strftime("%H:%M")

	#     iseserver = self.bot.get_guild(885095339885989942)
	#     nachan = iseserver.get_channel(973493394540232724)
	#     euchan = iseserver.get_channel(973493394120794112)
	#     aschan = iseserver.get_channel(973493475024703508)

	#     await nachan.edit(name=f'NA(PST) {now_pst_str}')
	#     await euchan.edit(name=f'EU(CET) {now_cet_str}')
	#     await aschan.edit(name=f'AS(JST) {now_jst_str}')

	@tasks.loop(hours=1,count=None)
	async def cacheclear(self):
		folder = './cache'
		for filename in os.listdir(folder):
			file_path = os.path.join(folder, filename)
			try:
				if os.path.isfile(file_path) or os.path.islink(file_path):
					os.unlink(file_path)
				elif os.path.isdir(file_path):
					shutil.rmtree(file_path)
			except Exception as e:
				print('Failed to delete %s. Reason: %s' % (file_path, e))

async def setup(bot):
	await bot.add_cog(Loopers(bot))