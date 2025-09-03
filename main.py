import discord
from discord.ext import commands
from logic import TombolMenu, Game
from config import TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

games = {}

@bot.event
async def on_ready():
    print(f"Berhasil login sebagai {bot.user.name}")

    channel_id = 0123456789012345678  # Ganti dengan ID channel yang diinginkan
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("Halo! Saya adalah bot permainan. Ketik !start untuk memulai permainan.")

@bot.command(name='start', aliases=['mulai', 'play', 'main'])
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

@bot.command()
async def get_points(ctx, points: int):
    user_id = ctx.author.id
    if user_id not in games:
        games[user_id] = Game(players=[ctx.author])

    game = games[user_id]
    await game.add_points(points, ctx)
    await ctx.send(f"Kamu mendapatkan {points} poin! Total poinmu sekarang adalah {game.points}.")

@bot.command()
async def get_channel_id(ctx):
    await ctx.send(f"Channel ID ini adalah: {ctx.channel.id}")

# Menjalankan Bot
bot.run(TOKEN)