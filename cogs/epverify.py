import discord
from discord.ext import commands, tasks
import os
import cv2
import numpy as np
import pytesseract
import asyncio

defaultcolour = 0x70f3f3

class EPVerification(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		self.looper.start()

	@tasks.loop(minutes=15,reconnect=False,count=None)
	async def looper(self):
		iseserver = self.bot.get_guild(885095339885989942)
		channel = iseserver.get_channel(918292285588914186)
		messages = [message async for message in channel.history(limit=None)]
		messages.reverse()

		newmessages = {msg.author.id:msg.id for msg in messages}
		oldmessages = [msg for msg in messages if msg.id not in newmessages.values() and msg.author.bot == False]
		for msg in oldmessages:
			await msg.delete()

		epurole = 918290858024005642
		guildepu = iseserver.get_role(epurole)
		epumembers = guildepu.members

		nonmembers = [mem for mem in epumembers if mem.id not in newmessages.keys()]
		for mem in nonmembers:
			await mem.remove_roles(guildepu,reason='Automatic action for removing screenshot')

	@commands.Cog.listener()
	async def on_message(self,message):

		# ignore dms
		if message.guild == None or message.author.id == self.bot.user.id:
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

	@commands.Cog.listener()
	async def on_message_delete(self,message):
		
		if message.guild == None or message.author.id == self.bot.user.id:
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

	@commands.command()
	@commands.is_owner()
	async def eptesting(self,ctx,psm:str):

		attachment = ctx.message.attachments[0]
		await attachment.save(attachment.filename)

		img = cv2.imread(attachment.filename)
		h,w,_ = img.shape

		(b, g, r) = img[0,0]
		count = 1
		if b < 3 and g < 3 and r < 3:
			for i in range(w):
				if img[:,i].mean() < 3.0:
					count+=1
				else:
					break
			
			img = img[:,count:w]

		if count == 1:
			ww = w-1
			(b, g, r) = img[0,ww]
			count = ww
			if b < 3 and g < 3 and r < 3:
				for i in range(ww,-1,-1):
					if img[:,i].mean() < 3.0:
						count = i
					else:
						break

				img = img[:,0:count]

		h,w,_ = img.shape
		await ctx.send(img.shape)
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

		colour1 = np.asarray([140, 140, 140])
		colour2 = np.asarray([255, 255, 255])
		mask = cv2.inRange(nimg, colour1, colour2)

		cv2.imwrite('test.png',mask)
		img_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
		text = pytesseract.image_to_string(img_rgb, config=f'--psm {psm}')
		await ctx.send(content=text,file=discord.File('test.png'))

async def setup(bot):
	await bot.add_cog(EPVerification(bot))
