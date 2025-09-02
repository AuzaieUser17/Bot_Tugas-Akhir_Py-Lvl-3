import discord
import random
import asyncio

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
        view.disable_button("end_turn")

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
            "3. Setelah pemain memilih salah satu aksi, pemain dapat memilih untuk mengakhiri gilirannya atau memilih aksi yang lain (NOTE: Pemain tidak bisa memiliih aksi yang sama)\n"
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
    def __init__(self, game, disabled_buttons=None):
        super().__init__(timeout=None)
        self.game = game
        self.updated_buttons = disabled_buttons or set()
        self.apply_disabled_buttons()

    @discord.ui.button(label="Menjelajah", style=discord.ButtonStyle.gray, custom_id="explore")
    async def explore(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Menjelajah.", ephemeral=True)

        chance = random.randint(1, 20)
        if chance == 1:
            await interaction.followup.send("Kamu tidak menemukan apa-apa saat menjelajah.")

            disabled = self.updated_buttons | {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.followup.send("Apa yang akan kamu lakukan selanjutnya?", view=view, ephemeral=True)
        else:
            enemy, enemy_hp, enemy_dmg = self.game.enemy_encounter()
            await interaction.followup.send(
                f"Kamu bertemu dengan {enemy}!\n"
                f"HP Musuh: {enemy_hp}\n"
                f"DMG Musuh: {enemy_dmg}\n",
                ephemeral=True
            )

            view = TombolCombat(enemy, enemy_dmg, enemy_hp, self.game.hp, self.game.dmg, self.game.defend)
            await interaction.followup.send("Apa yang akan kamu lakukan?", view=view, ephemeral=True)

    @discord.ui.button(label="Melawan Pemain", style=discord.ButtonStyle.gray, custom_id="fight")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Melawan Pemain.", ephemeral=True)

    @discord.ui.button(label="Pergi ke Tempat Kemah", style=discord.ButtonStyle.gray, custom_id="camp")
    async def camp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Pergi ke Tempat Kemah untuk beristirahat.", ephemeral=True)

        game = Game(self.game)
        game.hp = 100

        disabled = self.updated_buttons | {"camp"}
        view = TombolGame(self.game, disabled_buttons=disabled)
        view.enable_button("end_turn")

        await interaction.followup.send("Nyawa kamu telah pulih! Apa yang akan kamu lakukan selanjutnya?", view=view, ephemeral=True)

    @discord.ui.button(label="Buka Jurnal", style=discord.ButtonStyle.gray, custom_id="journal")
    async def journal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Buka Jurnal.", ephemeral=True)

    @discord.ui.button(label="Beraliansi", style=discord.ButtonStyle.gray, custom_id="ally")
    async def ally(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Beraliansi.", ephemeral=True)

    @discord.ui.button(label="Akhiri Giliran", style=discord.ButtonStyle.red, custom_id="end_turn")
    async def end_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Akhiri Giliran.", ephemeral=True)
        await interaction.followup.send(f"Giliran {interaction.user.mention} berakhir!")

        next_player = self.game.next_turn()
        if next_player:
            await interaction.followup.send(f"Giliran berikutnya adalah {next_player.mention}.")

            self.updated_buttons.clear()
            view = TombolGame(self.game)
            view.disable_button("end_turn")

    def apply_disabled_buttons(self):
        for item in self.children:
            if item.custom_id in self.updated_buttons:
                item.disabled = True

    def disable_button(self, custom_id: str):
        for item in self.children:
            if item.custom_id == custom_id:
                item.disabled = True
                self.updated_buttons.add(custom_id)
    
    def enable_button(self, custom_id: str):
        for item in self.children:
            if item.custom_id == custom_id:
                item.disabled = False
                self.updated_buttons.discard(custom_id)

class TombolCombat(discord.ui.View):
    def __init__(self, enemy, enemy_dmg, enemy_hp, hp, dmg, defend):
        super().__init__(timeout=None)
        self.enemy = enemy
        self.enemy_dmg = enemy_dmg
        self.enemy_hp = enemy_hp
        self.player_hp = hp
        self.player_dmg = dmg
        self.player_defend = defend
    
    @discord.ui.button(label="Serang", style=discord.ButtonStyle.red, custom_id="attack")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk menyerang!.", ephemeral=True)

        await self.combat_loop(interaction)
        if self.enemy_hp <= 0:
            await interaction.followup.send("Kamu menang! Musuh telah dikalahkan.", ephemeral=True)
            game = Game(players=[interaction.user])
            game.poin_kill_enemy(self.enemy)

            disabled = {"explore"}
            view = TombolGame(game, disabled_buttons=disabled)
            view.enable_button("end_turn")
            
            await interaction.followup.send("Pilih aksimu:", view=view, ephemeral=True)
        elif self.player_hp <= 0:
            await interaction.followup.send("Kamu kalah! HP-mu habis.", ephemeral=True)
            game = Game(players=[interaction.user])
            game.poin_lose()

            disabled = {"explore"}
            view = TombolGame(game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.followup.send("Pilih aksimu:", view=view, ephemeral=True)
        else:
            view = TombolCombat(self.enemy, self.enemy_dmg, self.enemy_hp, self.player_hp, self.player_dmg, self.player_defend)
            await interaction.followup.send("Apa yang akan kamu lakukan selanjutnya?", view=view, ephemeral=True)
    
    @discord.ui.button(label='Bertahan', style=discord.ButtonStyle.green, custom_id='defend')
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk bertahan!.", ephemeral=True)

        await self.do_defend(interaction)
        if self.player_hp <= 0:
            await interaction.followup.send("Kamu kalah! HP-mu habis.", ephemeral=True)
            game = Game(players=[interaction.user])
            game.poin_lose()

            disabled = {"explore"}
            view = TombolGame(game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.followup.send("Pilih aksimu:", view=view, ephemeral=True)
        else:
            view = TombolCombat(self.enemy_dmg, self.enemy_hp, self.player_hp, self.player_dmg, self.player_defend)
            await interaction.followup.send("Apa yang akan kamu lakukan selanjutnya?", view=view, ephemeral=True)
    
    async def combat_loop(self, interaction):
        self.enemy_hp -= self.player_dmg
        await asyncio.sleep(2)
        await interaction.followup.send(f"Serangan berhasil! Musuh kehilangan {self.player_dmg} HP.", ephemeral=True)

        self.player_hp -= self.enemy_dmg
        await asyncio.sleep(1)
        await interaction.followup.send(f"Musuh menyerang balik! Kamu kehilangan {self.enemy_dmg} HP.", ephemeral=True)
    
    async def do_defend(self, interaction):
        reduced_dmg = max(0, self.enemy_dmg - self.player_defend)
        self.player_hp -= reduced_dmg
        await asyncio.sleep(1)
        await interaction.followup.send(f"Kamu bertahan! Kamu hanya kehilangan {reduced_dmg} HP.", ephemeral=True)

class Game:
    rank_names = ['Pemula', 'Pendekar', 'Pejuang', 'Pejuang Elite', 'Master']
    rank_thresholds = [0, 100, 300, 600, 1000]

    enemy_types = ['Zombie', 'Zombie', 'Zombie', 'Zombie', 
                   'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 
                   'Penyihir', 'Penyihir', 'Penyihir', 'Penyihir', 
                   'Bandit', 'Bandit', 'Bandit', 'Bandit', 
                   'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 
                   'Naga', 'Naga', 'Robot', 'Robot', 'Sans']

    def __init__(self, players):
            self.players = players
            self.shuffled_players = []
            self.player_turn = None
            self.hp = 100
            self.dmg = 20
            self.defend = 10
            self.rank = 0
            self.points = 0
    
    def urutan_pemain(self):
        self.shuffled_players = self.players.copy()
        random.shuffle(self.shuffled_players)
        self.player_turn = self.shuffled_players[0] if self.shuffled_players else None

    def start(self):
        self.shuffled_players.clear()
        self.urutan_pemain()

    def next_turn(self):
        if not self.shuffled_players:
            return None
        current_index = self.shuffled_players.index(self.player_turn)
        next_index = (current_index + 1) % len(self.shuffled_players)
        self.player_turn = self.shuffled_players[next_index]
        return self.player_turn
    
    def enemy_encounter(self):
        enemy = random.choice(self.enemy_types)
        if enemy == 'Naga' or enemy == 'Robot':
            enemy_hp = random.randint(200, 300)
            enemy_dmg = random.randint(30, 50)
            return enemy, enemy_hp, enemy_dmg
        elif enemy == 'Sans':
            enemy_hp = 1
            enemy_dmg = 50
            return enemy, enemy_hp, enemy_dmg
        else:
            enemy_hp = random.randint(50, 100)
            enemy_dmg = random.randint(10, 20)
            return enemy, enemy_hp, enemy_dmg
    
    def poin_kill_enemy(self, enemy):
        if enemy in ['Naga', 'Robot']:
            poin = random.randint(100, 200)
        elif enemy == 'Sans':
            poin = 1
        else:
            poin = random.randint(20, 50)
        self.points += poin
        self.update_rank()

    def poin_kill_player(self):
        pass

    def poin_lose(self):
        poin = random.randint(10, 20)
        self.points = max(0, self.points - poin)
        if self.points == 0:
            self.rank = 0
        else:
            self.update_rank()

    def update_rank(self):
        for i, threshold in enumerate(self.rank_thresholds):
            if self.points >= threshold:
                self.rank = i
                self.hp += 50
                self.dmg += 20
                self.defend += 10