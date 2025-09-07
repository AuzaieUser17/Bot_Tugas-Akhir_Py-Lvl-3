import discord
from discord.ext import commands
from logic import Game
from button import TombolMenu
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

current_game = None

@bot.command(name='start', aliases=['mulai', 'play', 'main'])
async def startgame(ctx):
    text_start = (
        f'Halo {ctx.author.mention}! Selamat datang di World Collide.\n'
        'Tempat dimana Dunia dari berbagai Realita bertabrakan!\n'
        'Kamu bisa mulai permainan dengan menekan tombol "Mulai Permainan" di bawah ini.\n\n'
        'NOTE: Pastikan kamu sudah membaca peraturan sebelum permainan dimulai!'
    )
    await ctx.send(text_start)

    global current_game

    if current_game and not current_game.game_over:
        await ctx.send("Permainan sudah berlangsung.")
        return
    
    current_game = Game(players=[ctx.author], host=ctx.author)
    current_game.start()

    view = TombolMenu(current_game)
    await ctx.send(view=view)

@bot.command()
async def endgame(ctx):
    global current_game

    if not current_game:
        await ctx.send("Tidak ada permainan yang sedang berlangsung.")
        return
    
    ended = await current_game.end_game(ctx.author, ctx=ctx)

    if not ended:
        await ctx.send("Hanya host yang bisa menghentikan permainan atau permainan belum selesai.")

bot.run(TOKEN)