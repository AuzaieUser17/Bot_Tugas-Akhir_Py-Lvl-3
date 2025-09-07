import random
import asyncio
import discord

class Game:
    rank_names = ['Pemula', 'Pendekar', 'Pejuang', 'Pejuang Elite', 'Master']
    rank_thresholds = [0, 100, 300, 600, 1000]

    enemy_types = ['Zombie', 'Zombie', 'Zombie', 'Zombie', 
                   'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 'Hewan Liar', 
                   'Penyihir', 'Penyihir', 'Penyihir', 'Penyihir', 
                   'Bandit', 'Bandit', 'Bandit', 'Bandit', 
                   'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 'Manusia Cyber', 
                   'Naga', 'Naga', 'Robot', 'Robot', 'Sans']

    def __init__(self, players: list = [discord.Member], host: discord.Member = None):
        self.players = players
        self.shuffled_players = []
        self.player_turn = None
        self.host = host
        self.game_over = False

        self.enemy = None
        self.enemy_hp = 0            
        self.enemy_dmg = 0

        self.hp = {p: 100 for p in players}
        self.max_hp = {p: 100 for p in players}
        self.dmg = {p: 20 for p in players}
        self.defend = {p: 10 for p in players}
        self.rank = {p: 0 for p in players}
        self.points = {p: 0 for p in players}
        self.last_enemy_fought = {p: "-" for p in players}
        self.last_player_fought = {p: "-" for p in players}

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
        if enemy in ['Naga', 'Robot']:
            enemy_hp = random.randint(200, 300)
            enemy_dmg = random.randint(30, 50)
        elif enemy == 'Sans':
            enemy_hp = 1
            enemy_dmg = 50
        else:
            enemy_hp = random.randint(50, 100)
            enemy_dmg = random.randint(10, 20)

        self.enemy = enemy
        self.enemy_hp = enemy_hp
        self.enemy_dmg = enemy_dmg

        return enemy, enemy_hp, enemy_dmg
    
    def poin_kill_enemy(self, player, enemy, interaction=None):
        if enemy in ['Naga', 'Robot']:
            poin = random.randint(100, 200)
        elif enemy == 'Sans':
            poin = 1
        else:
            poin = random.randint(20, 50)

        self.points[player] += poin
        self.last_enemy_fought[player] = enemy

        self.update_rank(player, interaction)

    def poin_kill_player(self, winner, loser, interaction=None):
        poin = 100

        self.points[winner] += poin
        self.last_player_fought[winner] = loser.display_name

        self.update_rank(winner, interaction)

    def poin_lose(self, player, versus_enemy=True, winner=None):
        if versus_enemy:
            poin = random.randint(10, 20)
            self.points[player] = max(0, self.points[player] - poin)
        else:
            poin = 50
            self.points[player] = max(0, self.points[player] - poin)
            if isinstance(winner, discord.Member):
                self.last_player_fought[player] = winner.display_name

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

        if self.rank[player] > prev_rank:
            self.max_hp[player] += 50
            self.hp[player] = self.max_hp[player]
            self.dmg[player] += 10
            self.defend[player] += 5

            if interaction is not None:
                asyncio.create_task(interaction.followup.send(
                    f"Selamat {player.display_name}! Kamu naik peringkat menjadi {self.rank_names[self.rank[player]]}!"
                ))

            if self.rank[player] == len(self.rank_names) - 1:
                self.game_over = True
                if interaction:
                    lb = self.leaderboard()
                    asyncio.create_task(interaction.channel.send(f"Permainan selesai!\n\n{lb}"))

    def get_jurnal(self, player, username):
        jurnal = (
            f"Jurnal {username}:\n"
            f"Peringkat: {self.rank_names[self.rank[player]]}\n"
            f"Total Poin: {self.points[player]}\n"
            f"HP: {self.hp[player]}/{self.max_hp[player]}\n"
            f"DMG: {self.dmg[player]}\n"
            f"Defend: {self.defend[player]}\n"
            f"Musuh Terakhir yang Dikalahkan: {self.last_enemy_fought[player]}\n"
            f"Pemain Terakhir yang Dilawan: {self.last_player_fought[player]}"
        )
        return jurnal

    def leaderboard(self):
        sorted_players = sorted(self.players, key=lambda p: self.points[p], reverse=True)
        lines = []

        for i, p in enumerate(sorted_players, start=1):
            lines.append(f"{i}. {p.display_name} - {self.points[p]} poin - {self.rank_names[self.rank[p]]}")

        return "\n".join(lines)

    async def end_game(self, user: discord.Member, ctx=None):
        if user == self.host:
            self.game_over = True
            lb = self.leaderboard()

            if ctx:
                await ctx.send(f"Permainan dihentikan oleh host!\n\n{lb}")
            return True
        
        return False
