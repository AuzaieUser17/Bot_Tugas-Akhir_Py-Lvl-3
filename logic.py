import discord
import random

class TombolMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mulai Permainan", style=discord.ButtonStyle.green, custom_id="game_on")
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"{interaction.user.mention} memulai permainan! Selamat bermain!",
            ephemeral=True
        )

        game = Game(players=[interaction.user])
        game.start()

        await interaction.followup.send(f"Giliran pertama adalah {game.player_turn.mention}.")
        
        view=TombolGame(game)
        view.update_buttons("end_turn")

        await interaction.followup.send("Pilih aksimu:", view=view, ephemeral=True)

    @discord.ui.button(label="Lihat Peraturan", style=discord.ButtonStyle.secondary, custom_id="rules")
    async def view_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        rules_text = (
            "**Peraturan Permainan World Collide:**\n"
            "1. Setiap pemain akan mendapatkan giliran berdasarkan urutan\n"
            "2. Setiap giliran, pemain dapat memilih satu dari lima aksi yang tersedia:\n"
            "   - `Pergi ke Tempat Kemah` Disini, pemain bisa beristirahat dan menyembuhkan diri setelah Menjelajah atau Melawan Pemain lain.\n"
            "   - `Menjelajah` Pemain bisa pergi menjelajah dan bakalan melawan berbagai macam musuh. Jika pemain berhasi mengalahkan musuh, pemain bakal mendapatkan 20-50 poin, jika gagal, pemain akan kehilangnan 10-20 poin.\n"
            "   - `Melawan Pemain` Pemain bisa menantang pemain lain untuk bertarung. Jika pemain menang, pemain akan mendapatkan 100 poin, jika kalah, pemain akan kehilangan 50 poin.\n"
            "   - `Buka Jurnal` Setiap pemain punya jurnal masing-masing. Di dalam jurnal, pemain bisa melihat progres mereka, mulai dari peringkat mereka, total musuh dan pemain yang dikalahkan dan musuh atau pemian yang baru saja dilawan.\n"
            "   - `Beraliansi` Pemain bisa beraliansi dengan pemain lain. Jika pemain yang beraliansi mengalahkan Musuh/Pemain lain, aliansinya akan mendapatkan setengah dari poin yang didapatkan.\n"
            "3. Setelah pemain memilih salah satu aksi, pemain dapat memilih untuk mengakhiri gilirannya atau memilih aksi yang lain\n"
            "(NOTE: Pemain tidak bisa memiliih aksi yang sama)\n"
            "4. Permainan berakhir ketika salah satu pemain mencapai peringkat Master"
        )
        await interaction.response.send_message(rules_text)

        view = TombolMenu()
        view.update_buttons("rules")

        await interaction.followup.send(view=view)

    def update_buttons(self, custom_id):
        for item in self.children:
            if item.custom_id == custom_id:
                item.disabled = True
            else:
                item.disabled = False

class TombolGame(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="Menjelajah", style=discord.ButtonStyle.gray, custom_id="explore")
    async def explore(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Menjelajah.", ephemeral=True)

    @discord.ui.button(label="Melawan Pemain", style=discord.ButtonStyle.gray, custom_id="fight")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Melawan Pemain.", ephemeral=True)

    @discord.ui.button(label="Pergi ke Tempat Kemah", style=discord.ButtonStyle.gray, custom_id="camp")
    async def camp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Pergi ke Tempat Kemah.", ephemeral=True)

    @discord.ui.button(label="Buka Jurnal", style=discord.ButtonStyle.gray, custom_id="journal")
    async def journal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Buka Jurnal.", ephemeral=True)

    @discord.ui.button(label="Beraliansi", style=discord.ButtonStyle.gray, custom_id="ally")
    async def ally(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Beraliansi.", ephemeral=True)

    @discord.ui.button(label="Akhiri Giliran", style=discord.ButtonStyle.red, custom_id="end_turn")
    async def end_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Akhiri Giliran.", ephemeral=True)

    def update_buttons(self, custom_id):
        for item in self.children:
            if item.custom_id == custom_id:
                item.disabled = True
            else:
                item.disabled = False

class Game:
    rank_names = ['Pemula', 'Pendekar', 'Pejuang', 'Pejuang Elite', 'Master']

    def __init__(self, players):
            self.players = players
            self.shuffled_players = []
            self.player_turn = None
            self.hp = 100
            self.dmg = 20
            self.defend = 10
            self.rank = 0
    
    def urutan_pemain(self):
        self.shuffled_players = self.players.copy()
        random.shuffle(self.shuffled_players)
        self.player_turn = self.shuffled_players[0] if self.shuffled_players else None

    def start(self):
        self.urutan_pemain()

    def next_turn(self):
        if not self.shuffled_players:
            return None
        current_index = self.shuffled_players.index(self.player_turn)
        next_index = (current_index + 1) % len(self.shuffled_players)
        self.player_turn = self.shuffled_players[next_index]
        return self.player_turn
    
    def poin_kill_enemy(self):
        pass

    def poin_kill_player(self):
        pass