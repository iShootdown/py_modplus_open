from discord.ext import commands, tasks
import os
from shutil import rmtree

defaultcolour = 0x70f3f3

class Loopers(commands.Cog):

	def __init__(self,bot):
		self.bot = bot
		self.cacheclear.start()

	def cog_unload(self):
		self.cacheclear.stop()

	@tasks.loop(hours=1,count=None)
	async def cacheclear(self):
		folder = './cache'
		for filename in os.listdir(folder):
			file_path = os.path.join(folder, filename)
			try:
				if os.path.isfile(file_path) or os.path.islink(file_path):
					os.unlink(file_path)
				elif os.path.isdir(file_path):
					rmtree(file_path)
			except Exception as e:
				print('Failed to delete %s. Reason: %s' % (file_path, e))

async def setup(bot):
	await bot.add_cog(Loopers(bot))