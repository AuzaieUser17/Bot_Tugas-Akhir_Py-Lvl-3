import discord
import random
import asyncio

class TombolMenu(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="Mulai Permainan", style=discord.ButtonStyle.green, custom_id="game_on")
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.game_over:
            await interaction.response.send_message("Permainan sudah dihentikan.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"{interaction.user.mention} memulai permainan.",
            ephemeral=True
        )
        view = TombolGame(self.game)
        view.disable_button("end_turn")

        await interaction.channel.send(f"Giliran pertama adalah {self.game.player_turn.mention}")
        await interaction.channel.send("Pilih aksimu:", view=view)

    @discord.ui.button(label="Lihat Peraturan", style=discord.ButtonStyle.secondary, custom_id="rules")
    async def view_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.game_over:
            await interaction.response.send_message("Permainan sudah dihentikan.", ephemeral=True)
            return

        rules_text = (
            "**Peraturan Permainan World Collide:**\n"
            "1. Setiap pemain akan mendapatkan giliran berdasarkan urutan\n"
            "2. Setiap giliran, pemain dapat memilih satu dari lima aksi yang tersedia:\n"
            "   - `Pergi ke Tempat Kemah` Disini, pemain bisa beristirahat dan menyembuhkan diri setelah Menjelajah atau Melawan Pemain lain.\n"
            "   - `Menjelajah` Pemain bisa pergi menjelajah dan bakalan melawan berbagai macam musuh. Jika pemain berhasi mengalahkan musuh, pemain bakal mendapatkan 20-50 poin, jika gagal, pemain akan kehilangnan 10-20 poin.\n"
            "   - `Melawan Pemain` Pemain bisa menantang pemain lain untuk bertarung. Jika pemain menang, pemain akan mendapatkan 100 poin, jika kalah, pemain akan kehilangan 50 poin.\n"
            "   - `Buka Jurnal` Setiap pemain punya jurnal masing-masing. Di dalam jurnal, pemain bisa melihat progres mereka, mulai dari peringkat mereka, total musuh dan pemain yang dikalahkan dan musuh atau pemian yang baru saja dilawan.\n"
            "3. Setelah pemain memilih salah satu aksi, pemain dapat memilih untuk mengakhiri gilirannya atau memilih aksi yang lain (NOTE: Pemain tidak bisa memiliih aksi yang sama)\n"
            "4. Permainan berakhir ketika salah satu pemain mencapai peringkat Master"
        )

        self.update_buttons("rules")
        await interaction.message.edit(content=rules_text, view=self)

    def update_buttons(self, custom_id):
        for item in self.children:
            item.disabled = (item.custom_id == custom_id)

class TombolGame(discord.ui.View):
    def __init__(self, game, disabled_buttons=None):
        super().__init__(timeout=None)
        self.game = game
        self.updated_buttons = disabled_buttons or set()
        self.apply_disabled_buttons()

    def check_game_over(self, interaction: discord.Interaction):
        if self.game.game_over:
            asyncio.create_task(
                interaction.message.edit(content="Permainan sudah dihentikan.", view=None)
            )
            return True
        return False

    @discord.ui.button(label="Menjelajah", style=discord.ButtonStyle.gray, custom_id="explore")
    async def explore(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return

        await interaction.response.defer()
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
            
            await interaction.channel.send("Kamu bertemu dengan Musuh!", embed=embed, view=view)

    @discord.ui.button(label="Melawan Pemain", style=discord.ButtonStyle.gray, custom_id="fight")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        players = [p for p in self.game.players if p != interaction.user]

        if not players:
            await interaction.response.send_message("Tidak ada pemain lain untuk dilawan.", ephemeral=True)
            return

        view = discord.ui.View(timeout=None)

        for target in players:
            @discord.ui.button(label=f"Lawan {target.display_name}", style=discord.ButtonStyle.red)
            async def choose_target(inner_interaction: discord.Interaction, inner_button: discord.ui.Button, t=target):
                combat_view = TombolCombatPVP(self.game, interaction.user, t)

                await inner_interaction.response.edit_message(content=f"Pertarungan dimulai! {interaction.user.display_name} vs {t.display_name}", view=combat_view)

            view.add_item(choose_target)

        await interaction.response.send_message("Pilih pemain yang ingin kamu lawan:", view=view, ephemeral=True)


    @discord.ui.button(label="Pergi ke Tempat Kemah", style=discord.ButtonStyle.gray, custom_id="camp")
    async def camp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return

        await interaction.response.defer()

        self.game.hp[interaction.user] = self.game.max_hp[interaction.user]

        disabled = self.updated_buttons | {"camp"}
        view = TombolGame(self.game, disabled_buttons=disabled)
        view.enable_button("end_turn")

        await interaction.message.edit(content="Nyawamu telah pulih! Apa yang akan kamu lakukan selanjutnya?", view=view)

    @discord.ui.button(label="Buka Jurnal", style=discord.ButtonStyle.gray, custom_id="journal")
    async def journal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return

        username = interaction.user.display_name
        jurnal = self.game.get_jurnal(interaction.user, username)

        disabled = self.updated_buttons | {"journal"}
        view = TombolGame(self.game, disabled_buttons=disabled)
        view.enable_button("end_turn")

        await interaction.message.edit(content=f"{jurnal}\n\nApa yang akan kamu lakukan selanjutnya?", view=view)

    @discord.ui.button(label="Akhiri Giliran", style=discord.ButtonStyle.red, custom_id="end_turn")
    async def end_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return

        next_player = self.game.next_turn()
        if next_player:
            await interaction.channel.send(f"Giliran berikutnya adalah {next_player.mention}")

        self.updated_buttons.clear()
        view = TombolGame(self.game)
        view.disable_button("end_turn")

        await interaction.channel.send("Pilih aksimu:", view=view)

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
    def __init__(self, game, enemy, enemy_dmg, enemy_hp, hp, dmg, defend):
        super().__init__(timeout=None)
        self.game = game
        self.enemy = enemy
        self.enemy_dmg = enemy_dmg
        self.enemy_hp = enemy_hp
        self.player_hp = hp
        self.player_dmg = dmg
        self.player_defend = defend
    
    def check_game_over(self, interaction: discord.Interaction):
        if self.game.game_over:
            asyncio.create_task(
                interaction.message.edit(content="Permainan sudah dihentikan.", view=None)
            )
            return True
        return False

    @discord.ui.button(label="Serang", style=discord.ButtonStyle.red, custom_id="attack")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return
        await interaction.response.defer()

        self.enemy_hp -= self.player_dmg
        self.player_hp -= self.enemy_dmg
        self.game.hp[interaction.user] = self.player_hp

        desc = (
            f"{interaction.user.mention} menyerang!\n"
            f"Musuh {self.enemy} kehilangan {self.player_dmg} HP.\n"
            f"HP Musuh: {self.enemy_hp}\n\n"
            f"Musuh menyerang balik! Kamu kehilangan {self.enemy_dmg} HP.\n"
            f"HP Kamu: {self.player_hp}"
        )

        embed = discord.Embed(description=desc, color=discord.Color.red())

        if self.enemy_hp <= 0:
            self.game.poin_kill_enemy(interaction.user, self.enemy, interaction)

            disabled = {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.message.edit(content="Kamu menang! Musuh dikalahkan.\nPilih aksimu:", embed=None, view=view)
        elif self.player_hp <= 0:
            self.game.poin_lose(interaction.user)

            disabled = {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.message.edit(content="Kamu kalah! HP habis.\nPilih aksimu:", embed=None, view=view)
        else:
            view = TombolCombat(self.game, self.enemy, self.enemy_dmg, self.enemy_hp, 
                                self.player_hp, self.player_dmg, self.player_defend)
            
            await interaction.message.edit(content="Apa yang akan kamu lakukan selanjutnya?", embed=embed, view=view)

    @discord.ui.button(label="Bertahan", style=discord.ButtonStyle.green, custom_id="defend")
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return
        await interaction.response.defer()

        reduced_dmg = max(0, self.enemy_dmg - self.player_defend)
        self.player_hp -= reduced_dmg
        self.game.hp[interaction.user] = self.player_hp

        desc = (
            f"{interaction.user.mention} bertahan!\n"
            f"Serangan musuh {self.enemy} berkurang!\n"
            f"Kamu hanya kehilangan {reduced_dmg} HP.\n"
            f"HP Kamu: {self.player_hp}\n"
            f"HP Musuh: {self.enemy_hp}"
        )

        embed = discord.Embed(description=desc, color=discord.Color.green())

        if self.player_hp <= 0:
            self.game.poin_lose(interaction.user)

            disabled = {"explore"}
            view = TombolGame(self.game, disabled_buttons=disabled)
            view.enable_button("end_turn")

            await interaction.message.edit(content="Kamu kalah! HP habis.\nPilih aksimu:", embed=None, view=view)
        else:
            view = TombolCombat(self.game, self.enemy, self.enemy_dmg, self.enemy_hp, 
                                self.player_hp, self.player_dmg, self.player_defend)
            
            await interaction.message.edit(content="Apa yang akan kamu lakukan selanjutnya?", embed=embed, view=view)

class TombolCombatPVP(discord.ui.View):
    def __init__(self, game, attacker, defender):
        super().__init__(timeout=None)
        self.game = game
        self.attacker = attacker
        self.defender = defender
        self.attacker_hp = game.hp[attacker]
        self.defender_hp = game.hp[defender]

    def check_game_over(self, interaction: discord.Interaction):
        if self.game.game_over:
            asyncio.create_task(interaction.message.edit(content="Permainan sudah dihentikan!", view=None))
            return True
        return False

    @discord.ui.button(label="Serang", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return
        
        if interaction.user != self.attacker:
            await interaction.response.send_message("Bukan giliranmu!", ephemeral=True)
            return

        await interaction.response.defer()

        dmg = self.game.dmg[self.attacker]
        self.defender_hp -= dmg
        self.game.hp[self.defender] = self.defender_hp

        desc = (
            f"{self.attacker.display_name} menyerang {self.defender.display_name}!\n"
            f"{self.defender.display_name} kehilangan {dmg} HP.\n"
            f"HP {self.defender.display_name}: {self.defender_hp}"
        )
        embed = discord.Embed(description=desc, color=discord.Color.red())

        if self.defender_hp <= 0:
            self.game.poin_kill_player(self.attacker, self.defender, interaction)
            self.game.poin_lose(self.defender, self.attacker, self.defender, versus_enemy=False)

            await interaction.message.edit(content=f"{self.attacker.display_name} menang melawan {self.defender.display_name}!", embed=None, view=None)
            return

        self.attacker, self.defender = self.defender, self.attacker
        await interaction.message.edit(content=f"{self.attacker.display_name}, giliranmu untuk menyerang!", embed=embed, view=self)

    @discord.ui.button(label="Bertahan", style=discord.ButtonStyle.blurple)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.check_game_over(interaction):
            return
        
        if interaction.user != self.attacker:
            await interaction.response.send_message("Bukan giliranmu!", ephemeral=True)
            return

        await interaction.response.defer()

        reduced_dmg = max(0, self.game.dmg[self.defender] - self.game.defend[self.attacker])
        self.attacker_hp -= reduced_dmg
        self.game.hp[self.attacker] = self.attacker_hp

        desc = (
            f"{self.attacker.display_name} bertahan!\n"
            f"Serangan {self.defender.display_name} berkurang!\n"
            f"{self.attacker.display_name} hanya kehilangan {reduced_dmg} HP.\n"
            f"HP {self.attacker.display_name}: {self.attacker_hp}"
        )
        embed = discord.Embed(description=desc, color=discord.Color.green())

        if self.attacker_hp <= 0:
            self.game.poin_kill_player(self.defender, self.attacker, interaction)
            self.game.poin_lose(self.attacker, self.defender, self.attacker, versus_enemy=False)

            await interaction.message.edit(content=f"{self.defender.display_name} menang melawan {self.attacker.display_name}!", embed=None, view=None)
            return

        self.attacker, self.defender = self.defender, self.attacker

        await interaction.message.edit(content=f"{self.attacker.display_name}, giliranmu untuk menyerang!", embed=embed, view=self)