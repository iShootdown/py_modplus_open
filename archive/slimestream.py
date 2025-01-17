import discord
from discord.ext import commands, tasks
from firebase_admin import firestore
import subprocess
import aiohttp
from datetime import datetime
import pytz
from yt_dlp import YoutubeDL

db = firestore.client()
botprefix = 'm+'
yt_channel_id = "UCqly9F4Fr_jf2Y1Cy5hacRg"

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

def auth():
	return "AIzaSyAQyArX8FSXGR1cjhJhNG7yY9VVKKaLiY0"

def generate_headers():
	return {
		"Accept": "application/json"
	}

def generate_post(epoch, title, stream_id):

	convert = datetime.utcfromtimestamp(epoch).replace(tzinfo=pytz.utc)
	jst_time = convert.astimezone(pytz.timezone('Asia/Tokyo'))
	jst_str = jst_time.strftime("%d/%b (%a), %H:%M")

	return f"Upcoming Broadcast...\n**{title}**\n\nStart Time: {jst_str} JST\n\n_Time Zone Conversions_\n(The below widget is automatically adjusted to your local timezone)\n<t:{epoch}:F>\n\n*_Stream Link_*\n> https://www.youtube.com/live/{stream_id} """

defaultcolour = 0xcaeffe
regions = ['North & South America', 'Europe and Others', 'Asia Pacific', 'Japan']
profcolours = [0xcaeffe, 0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db, 0x9b59b6, 0xff548d, 0xfffffe, 0x000001]

class StreamUtils(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.stream_chat = self.bot.get_channel(892220039225286716)
		self.stream_feed = self.bot.get_channel(893646563228921916)
		self.stream_stream = self.bot.get_channel(892220093956759582)
		self.slime_guild = self.bot.get_guild(885095339885989942)
		self.stream_id = db.collection("stream").document("stream").get().to_dict().get("stream")
		self.stream_start = db.collection("stream").document("stream").get().to_dict().get("stream_start")
		self.stream_time = db.collection("stream").document("stream").get().to_dict().get("stream_time")

		if self.stream_start != None:
			self.auto_unlock.start()
		else:
			self.check_stream.start()

		print(self.stream_id)

	@commands.group(brief='Stream Utilities', case_insensitive=True)
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	async def stream(self, ctx):
		''' Turn on/off/set livestream mode for game releases '''
		if ctx.invoked_subcommand is None:
			await ctx.invoke(self.bot.get_command('stream'), cmdr=ctx.command.name)

	@stream.command(name="unlock", aliases=["on"])
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
	async def unlock(self, ctx):
		''' Stream mode on (unlock channels) '''

		await self.stream_chat.set_permissions(self.slime_guild.default_role, send_messages=True, reason=f"Stream on requested by {ctx.author}")
		await self.stream_stream.set_permissions(self.slime_guild.default_role, connect=True, reason=f"Stream on requested by {ctx.author}")
		embed = discord.Embed(
			color=discord.Color(defaultcolour),
			description="Stream mode turned on, channels unlocked"
		)

		self.auto_lock.start()

		await ctx.message.delete()
		return await ctx.send(embed=embed, delete_after=5.0)
		
	@stream.command(name="lock", aliases=["off"])
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	@commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
	async def lock(self,ctx):
		''' Stream mode off (lock channels) '''

		await self.stream_chat.set_permissions(self.slime_guild.default_role, send_messages=False, reason=f"Stream off requested by {ctx.author}")
		await self.stream_stream.set_permissions(self.slime_guild.default_role, connect=False, reason=f"Stream off requested by {ctx.author}")

		for user_id in self.stream_stream.voice_states.keys():
			member = self.slime_guild.get_member(user_id)
			await member.move_to(None)

		embed = discord.Embed(
			color=discord.Color(defaultcolour),
			description="Stream mode turned off, channels locked"
		)
		await ctx.message.delete()
		return await ctx.send(embed=embed, delete_after=5.0)

	@stream.command()
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	async def set(self,ctx,link:str):
		''' Set new stream '''

		if "watch?v=" in link:
			stream_id = link.split("watch?v=")[1].split("&")[0]
		elif "live" in link:
			stream_id = link.split("live/")[1].split("?")[0]
		else:
			return await ctx.send(embed=embederr("Invalid link"), delete_after=5.0)
		
		async with aiohttp.ClientSession() as session:
			async with session.get(url=f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id={stream_id}&key={auth()}") as response:
				print(response.status)
				if response.status == 200:
					resp_dict = dict(await response.json())
					cc = resp_dict["items"][0]["liveStreamingDetails"].get("scheduledStartTime")
					if cc != None:
						stream_time = datetime.strptime(cc, '%Y-%m-%dT%H:%M:%SZ').timestamp()
						stream_start = int(stream_time) - 60
						stream_title = resp_dict["items"][0]["snippet"].get("title")

						db.collection("stream").document("stream").set({"stream": stream_id, "stream_time": int(stream_time), "stream_start": stream_start})
						self.stream_start = stream_start
						self.stream_id = stream_id
						self.stream_time = int(stream_time)

						# poster = generate_post(epoch=int(stream_time), title=title, stream_id=stream_id)
						# msg = await self.stream_chat.send(poster)
						# await msg.pin()

					print("Grab start time channels")
				else:
					print(response.status)

		embed = discord.Embed(
			colour=discord.Colour.green(),
			description=f"Stream link set to https://www.youtube.com/live/{stream_id}"
		)
		await ctx.send(embed=embed, delete_after=5.0)
		self.stream_id = stream_id
		self.check_stream.cancel()

	@stream.command()
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	async def update(self,ctx,message_id:str,title:str):
		''' Set new stream '''

		if self.stream_start == None or self.stream_id == None:
			return await ctx.send(embed=embederr("No stream set, please set one first"), delete_after=5.0)

		message_id = int(message_id)
		msg = await self.stream_chat.get_partial_message(message_id)
		poster = generate_post(epoch=self.stream_time, title=title, stream_id=self.stream_id)
		await msg.edit(poster)

	@stream.command()
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	async def delete(self,ctx):
		''' Delete current stream '''

		db.collection("stream").document("stream").set({"stream": None, "stream_time": None, "stream_start": None})
		embed = discord.Embed(
			colour=discord.Colour.green(),
			description=f"Stream info deleted"
		)
		self.auto_lock.cancel()
		self.auto_unlock.cancel()
		return await ctx.send(embed=embed, delete_after=5.0)
		
	@commands.command(brief="Screen capture current livestream")
	@commands.guild_only()
	@commands.has_permissions(manage_channels=True)
	async def streamcap(self, ctx):
		''' Screen capture timing at current stream '''

		if self.stream_id == None:
			return await ctx.send(embed=embederr("No stream link set, please set in `m+stream set`"))

		with YoutubeDL() as ydl:
			info = ydl.extract_info(f"https://www.youtube.com/live/{self.stream_id}", download=False)
			formats_list = info.get("formats")

			for formater in formats_list:
				if formater["format_id"] == "301":
					internal_stream = formater.get("url")

			print(internal_stream)

			if internal_stream != None:
				# ffmpeg -i $(cat stream-url) -f image2 -frames:v 1 img22.jpeg
				subprocess.run(["ffmpeg", "-i", internal_stream, "-f", "image2", "-frames:v", "1", "-y", "tempscreenshot.png"])
			else:
				print(internal_stream)
				return

		await ctx.message.delete()
		screencap = discord.File("tempscreenshot.png", filename="tempscreenshot.png")

		if self.stream_feed == None:
			self.stream_feed = self.bot.get_guild(885095339885989942).get_channel(893646563228921916)

		return await self.stream_feed.send(file=screencap)
		
	@tasks.loop(hours=1,reconnect=False,count=None)
	async def check_stream(self):

		# Upcoming livestreams

		async with aiohttp.ClientSession() as session:
			async with session.get(url=f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId=UCqly9F4Fr_jf2Y1Cy5hacRg&eventType=upcoming&maxResults=5&type=video&key={auth()}") as response:
				if response.status == 200:
					resp_dict = dict(await response.json())

					if len(resp_dict["items"]) > 0:
						for video_dict in resp_dict["items"]:
							title = video_dict["snippet"]["title"]
							if "転生したらスライムだった件 魔王と竜の建国譚 まおりゅう" in title:
								stream_id = video_dict["id"].get("videoId")
								stream_time_long = video_dict["liveStreamingDetails"].get("scheduledStartTime")

								if stream_id == None or stream_time == None:
									print(f"Stream grab error: {stream_id} {stream_time}")
									continue
								else:
									stream_time = datetime.strptime(stream_time_long, '%Y-%m-%dT%H:%M:%SZ').timestamp()
									stream_start = int(stream_time) - 60

									if stream_id != self.stream_id:
										db.collection("stream").document("stream").set({"stream": stream_id, "stream_time": int(stream_time), "stream_start": int(stream_start)})
										self.stream_start = stream_start
										self.stream_id = stream_id
										self.stream_time = int(stream_time)

										poster = generate_post(epoch=int(stream_time), title=title, stream_id=stream_id)
										msg = await self.stream_chat.send(poster)
										await msg.pin()
							else:
								continue
				else:
					print(response.status)

	@tasks.loop(minutes=1,reconnect=False,count=None)
	async def auto_unlock(self):

		if self.auto_unlock.current_loop == 0:
			self.check_stream.cancel()

		if self.stream_start != None:
			if datetime.now().timestamp() >= float(self.stream_start):
				await self.stream_chat.set_permissions(self.slime_guild.default_role, send_messages=True, reason=f"Automatic unlock of stream channels")
				await self.stream_stream.set_permissions(self.slime_guild.default_role, connect=True, reason=f"Automatic unlock of stream channels")
				self.auto_lock.start()

	@tasks.loop(minutes=1,reconnect=False,count=None)
	async def auto_lock(self):

		async with aiohttp.ClientSession() as session:
			async with session.get(url=f"https://youtube.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={self.stream_id}&key={auth()}", headers=generate_headers()) as response:
				if response.status == 200:
					resp_dict = dict(await response.json())
					cc = resp_dict.get("items")
					if len(cc) > 0:
						cc = cc[0]
						cc = cc.get("liveStreamingDetails")
						if cc != None:
							cc = cc.get("actualEndTime")
							if cc != None:
								await self.stream_chat.set_permissions(self.slime_guild.default_role, send_messages=False, reason=f"Automatic lock of stream channels")
								await self.stream_stream.set_permissions(self.slime_guild.default_role, connect=False, reason=f"Automatic lock of stream channels")

								for user_id in self.stream_stream.voice_states.keys():
									member = self.slime_guild.get_member(user_id)
									await member.move_to(None)
								print("Auto-lock stream channels")
								self.check_stream.start()
								return
				else:
					print(response.status)

async def setup(bot):
	await bot.add_cog(StreamUtils(bot))