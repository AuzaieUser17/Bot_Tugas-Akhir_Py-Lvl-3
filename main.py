import discord
from discord.ext import commands
from logic import TombolMenu
from config import TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Berhasil login sebagai {bot.user.name}")

@bot.command(name='start', aliases=['mulai', 'play'])
async def startgame(ctx):
    text_start = (
        f'Halo {ctx.author.mention}! Selamat datang di World Collide.\n'
        'Tempat dimana Dunia dari berbagai Realita bertabrakan!\n'
        'Kamu bisa mulai permainan dengan menekan tombol "Mulai Permainan" di bawah ini.\n\n'
        'NOTE: Pastikan kamu sudah membaca peraturan sebelum permainan dimulai!'
    )
    await ctx.send(text_start)

    view = TombolMenu()
    await ctx.send(view=view)

# Menjalankan Bot
bot.run(TOKEN)