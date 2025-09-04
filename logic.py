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

        view = TombolGame(game)
        view.disable_button("end_turn")

        # pesan publik (bisa diedit), hanya pemain giliran bisa klik
        await interaction.followup.send("Pilih aksimu:", view=view)

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

        view = TombolMenu()
        view.update_buttons("rules")

        await interaction.response.send_message(rules_text, view=view)

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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.game.player_turn:
            await interaction.response.send_message(
                "Bukan giliranmu!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Menjelajah", style=discord.ButtonStyle.gray, custom_id="explore")
    async def explore(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"{interaction.user.mention} memilih untuk Menjelajah.")

        chance = random.randint(1, 20)
        if chance == 1:
            disabled = self.updated_buttons | {"explore"}

            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.message.edit(content="Kamu tidak menemukan apa-apa saat menjelajah.\nApa yang akan kamu lakukan selanjutnya?", view=view)
        else:
            enemy, enemy_hp, enemy_dmg = self.game.enemy_encounter()
            embed = discord.Embed(
                description=f"Musuh: {enemy}\nHP Musuh: {enemy_hp}\nDMG Musuh: {enemy_dmg}", 
                color=discord.Color.red()
            )

            player = interaction.user
            view = TombolCombat(self.game, enemy, enemy_dmg, enemy_hp, 
                                self.game.hp[player], self.game.dmg[player], self.game.defend[player])

            msg = await interaction.followup.send("Kamu bertemu dengan Musuh!", embed=embed, view=view)
            view.msg = msg

    @discord.ui.button(label="Melawan Pemain", style=discord.ButtonStyle.gray, custom_id="fight")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Melawan Pemain.", ephemeral=True)

    @discord.ui.button(label="Pergi ke Tempat Kemah", style=discord.ButtonStyle.gray, custom_id="camp")
    async def camp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Kamu memilih untuk Pergi ke Tempat Kemah untuk beristirahat.")

        self.game.hp[interaction.user] = self.game.max_hp[interaction.user]

        disabled = self.updated_buttons | {"camp"}
        view = TombolGame(self.game, disabled_buttons=disabled)
        view.enable_button("end_turn")

        await interaction.message.edit(content="Nyawa kamu telah pulih! Apa yang akan kamu lakukan selanjutnya?", view=view)

    @discord.ui.button(label="Buka Jurnal", style=discord.ButtonStyle.gray, custom_id="journal")
    async def journal(self, interaction: discord.Interaction, button: discord.ui.Button):
        username = interaction.user.name
        enemy = self.game.enemy
        jurnal = self.game.get_jurnal(interaction.user, username, enemy)

        disabled = self.updated_buttons | {"journal"}
        view = TombolGame(self.game, disabled_buttons=disabled)
        view.enable_button("end_turn")

        await interaction.response.edit_message(
            content=f"Kamu membuka jurnalmu:\n{jurnal}\n\nApa yang akan kamu lakukan selanjutnya?", 
            view=view
            )

    @discord.ui.button(label="Beraliansi", style=discord.ButtonStyle.gray, custom_id="ally")
    async def ally(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kamu memilih untuk Beraliansi.", ephemeral=True)

    @discord.ui.button(label="Akhiri Giliran", style=discord.ButtonStyle.red, custom_id="end_turn")
    async def end_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        next_player = self.game.next_turn()
        if next_player:
            await interaction.channel.send(f"Giliran berikutnya adalah {next_player.mention}.")

        self.updated_buttons.clear()
        view = TombolGame(self.game)
        view.disable_button("end_turn")

        await interaction.message.edit(
            content=f"{self.game.player_turn.mention}, sekarang giliranmu. Pilih aksimu:", view=view
            )


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
    def __init__(self, game, enemy, enemy_dmg, enemy_hp, player_hp, player_dmg, player_defend):
        super().__init__(timeout=None)
        self.game = game
        self.enemy = enemy
        self.enemy_dmg = enemy_dmg
        self.enemy_hp = enemy_hp
        self.player_hp = player_hp
        self.player_dmg = player_dmg
        self.player_defend = player_defend
        self.msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.game.player_turn:
            await interaction.response.send_message(
                "Bukan giliranmu!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Serang", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.combat_loop(interaction)

    @discord.ui.button(label="Bertahan", style=discord.ButtonStyle.blurple)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.do_defend(interaction)
    
    async def combat_loop(self, interaction: discord.Interaction):
        self.enemy_hp -= self.player_dmg
        await asyncio.sleep(1)

        embed = discord.Embed(
            description=f"{interaction.user.mention} menyerang!\n"
                        f"Musuh {self.enemy} kehilangan {self.player_dmg} HP.\n"
                        f"HP Musuh: {self.enemy_hp}",
            color=discord.Color.orange()
        )
        await self.msg.edit(embed=embed, view=self)

        if self.enemy_hp <= 0:
            self.game.poin_kill_enemy(interaction.user, self.enemy)

            disabled = {"explore"}  # tandai tombol explore sudah dipakai
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            embed = discord.Embed(
                description=
                        f"{interaction.user.mention} menyerang!\n"
                        f"Musuh {self.enemy} dikalahkan!\n"
                        f"Kamu mendapat poin!", 
                color=discord.Color.green()
            )

            await self.msg.edit(content="Pilih aksi berikutnya:", embed=embed, view=view)
            return
        
        await asyncio.sleep(1)
        self.player_hp -= self.enemy_dmg
        self.game.hp[interaction.user] = self.player_hp

        embed.description += f"\n\nMusuh menyerang balik! {interaction.user.mention} kehilangan {self.enemy_dmg} HP.\nHP Kamu: {self.player_hp}"
        await self.msg.edit(embed=embed, view=self)

        if self.player_hp <= 0:
            self.game.poin_lose(interaction.user)

            disabled = {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            embed.description += f"\n\n{interaction.user.mention} kalah!"

            await self.msg.edit(embed=embed, view=view)
    
    async def do_defend(self, interaction: discord.Interaction):
        reduced_dmg = max(0, self.enemy_dmg - self.player_defend)

        self.player_hp -= reduced_dmg
        self.game.hp[interaction.user] = self.player_hp

        embed = discord.Embed(
            description=f"{interaction.user.mention} bertahan!\n"
                        f"Serangan musuh dikurangi {self.player_defend}.\n"
                        f"Kamu hanya kehilangan {reduced_dmg} HP.\n"
                        f"HP Kamu: {self.player_hp}",
            color=discord.Color.blue()
        )
        await asyncio.sleep(1)
        await self.msg.edit(embed=embed, view=self)

        if self.player_hp <= 0:
            self.game.poin_lose(interaction.user)

            disabled = {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            embed.description += f"\n\n{interaction.user.mention} kalah!"
            await self.msg.edit(embed=embed, view=view)

class Game:
    # Rank
    rank_names = ['Pemula', 'Pendekar', 'Pejuang', 'Pejuang Elite', 'Master']
    rank_thresholds = [0, 100, 300, 600, 1000]

    # Tipe musuh
    enemy_types = ['Zombie', 'Zombie', 'Zombie', 'Zombie', 
                   'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 
                   'Penyihir', 'Penyihir', 'Penyihir', 'Penyihir', 
                   'Bandit', 'Bandit', 'Bandit', 'Bandit', 
                   'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 
                   'Naga', 'Naga', 'Robot', 'Robot', 'Sans']

    def __init__(self, players: list =[discord.Member]):
            self.players = players
            self.shuffled_players = []
            self.player_turn = None

            # Status musuh
            self.enemy = None
            self.enemy_hp = 0            
            self.enemy_dmg = 0

            # Status pemain
            self.hp = {players: 100 for players in players}
            self.max_hp = {players: self.hp[players] for players in players}
            self.dmg = {players: 20 for players in players}
            self.defend = {players: 10 for players in players}
            self.rank = {players: 0 for players in players}
            self.points = {players: 0 for players in players}
    
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
        next_index = current_index + 1

        if next_index >= len(self.shuffled_players):
            next_index = 0
        self.player_turn = self.shuffled_players[next_index]
        return self.player_turn
    
    def enemy_encounter(self):
        enemy = random.choice(self.enemy_types)
        if enemy == 'Naga' or enemy == 'Robot':
            enemy_hp = random.randint(200, 300)
            enemy_dmg = random.randint(30, 50)

            self.enemy = enemy
            self.enemy_hp = enemy_hp
            self.enemy_dmg = enemy_dmg
            return enemy, enemy_hp, enemy_dmg
        elif enemy == 'Sans':
            enemy_hp = 1
            enemy_dmg = 50

            self.enemy = enemy
            self.enemy_hp = enemy_hp
            self.enemy_dmg = enemy_dmg
            return enemy, enemy_hp, enemy_dmg
        else:
            enemy_hp = random.randint(50, 100)
            enemy_dmg = random.randint(10, 20)

            self.enemy = enemy
            self.enemy_hp = enemy_hp
            self.enemy_dmg = enemy_dmg
            return enemy, enemy_hp, enemy_dmg
    
    def poin_kill_enemy(self, player, enemy):
        if enemy in ['Naga', 'Robot']:
            poin = random.randint(100, 200)
        elif enemy == 'Sans':
            poin = 1
        else:
            poin = random.randint(20, 50)
        self.points[player] += poin
        self.update_rank(player)

    def poin_kill_player(self):
        pass

    def poin_lose(self, player):
        poin = random.randint(10, 20)
        self.points[player] = max(0, self.points[player] - poin)
        if self.points[player] <= 0:
            self.rank[player] = 0
            self.points[player] = 0
        else:
            self.update_rank(player)

    def update_rank(self, player, interaction=None):
        prev_rank = self.rank[player]
        for i, threshold in enumerate(self.rank_thresholds):
            if self.points[player] >= threshold:
                self.rank[player] = i
        if self.rank[player] > prev_rank and interaction is not None:
            asyncio.create_task(
                interaction.followup.send(
                    f"Selamat! Kamu naik peringkat menjadi {self.rank_names[self.rank[player]]}!"
                    )
                )
            self.hp[player] += 50
            self.max_hp[player] = self.hp[player]
            self.dmg[player] += 10
            self.defend[player] += 5
            
    def get_jurnal(self, player, username, enemy):
        jurnal = (
            f"**Jurnal {username}:**\n"
            f"Peringkat: {self.rank_names[self.rank[player]]}\n"
            f"Total Poin: {self.points[player]}\n"
            f"HP: {self.hp[player]}/{self.max_hp[player]}\n"
            f"DMG: {self.dmg[player]}\n"
            f"Defend: {self.defend[player]}\n"
            f"Musuh Terakhir yang Dikalahkan: {enemy}\n"
            f"Pemain Terakhir yang Dikalahkan: -\n"
        )
        return jurnal
    
    # Tes sistem mendapatkan poin lewat command
    async def add_points(self, points: int, ctx=None):
        prev_points = self.points
        self.points += points
        prev_points += self.points
        await self.update_rank_ctx(ctx)
    
    async def update_rank_ctx(self, ctx=None):
        prev_rank = self.rank
        for i, threshold in enumerate(self.rank_thresholds):
            if self.points >= threshold:
                self.rank = i
        if self.rank > prev_rank and ctx is not None:
            await ctx.send(
                f"Selamat! Kamu naik peringkat menjadi {self.rank_names[self.rank]}!"
                )
            self.hp += 50
            self.max_hp = self.hp
            self.dmg += 10
            self.defend += 5