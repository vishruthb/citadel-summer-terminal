import gamelib
import random
import math
import warnings
from sys import maxsize
import json

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        self.lastRoundEnemyHealth = 30
        self.side = 'right'

    def on_game_start(self, config):
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)
        self.starter_strategy(game_state)
        game_state.submit_turn()

    def starter_strategy(self, game_state):
        self.build_defences(game_state)
        self.attack(game_state)

    def build_defences(self, game_state):
        starting_turrets = [[7, 11], [19, 11]]
        starting_supports = [[13,2]]
        core_turrets = [[7, 11], [19, 11], [24,12], [3,12], [13,11]]
        core_supports = [[13,2],[14,2]]
        secondary_supports = [[13,3],[14,3],[13,4],[14,4]]
        secondary_turrets = [[10,11],[16,11],[23,11],[4,11],[24,11],[3,11],[10,10], [13,10],[14,11],[9,11],[15,11],[12,11],[17,11],[18,11]]
        corner_walls = [[0,13], [27,13],[1, 12], [2, 12], [26,12],[25,12]]
        turret_walls = [[23, 12],[4, 12],[22,12],[6, 12], [7, 12], [8, 12], [12, 12], [13, 12], [14, 12], [18, 12], [19, 12], [20, 12], [24, 12],[10,12],[16,12],[5,12],[21,12],[8,12],[9,12],[18,12],[17,12],[11,9],[15,12]]
        final_supports = [[12,3],[15,3],[12,4],[15,4],[13,5],[14,5],[13,6],[14,6]]
        
        if game_state.turn_number == 0:
            game_state.attempt_spawn(TURRET, starting_turrets)
            game_state.attempt_spawn(SUPPORT, starting_supports)
            game_state.attempt_upgrade(starting_turrets[0])
            game_state.attempt_upgrade(starting_turrets[1])
        
        else:        
            game_state.attempt_spawn(TURRET, core_turrets)
            game_state.attempt_spawn(SUPPORT, core_supports)
            game_state.attempt_spawn(WALL, corner_walls)
            if game_state.turn_number > 25:
                for wall in corner_walls:
                    game_state.attempt_upgrade(wall)
            do_secondary = True
            for unit in core_turrets+core_supports:
                game_state.attempt_upgrade(unit)
                if not self.is_upgraded(game_state,unit):
                    do_secondary = False
            
            if do_secondary and game_state.get_resource(SP) >= 1:
                ok = True
                game_state.attempt_spawn(WALL, turret_walls)
                if ok:
                    game_state.attempt_spawn(SUPPORT, secondary_supports)
                    for support in secondary_supports:
                        game_state.attempt_upgrade(support)
                        if not self.is_upgraded(game_state,support):
                            ok = False
                if ok:
                    game_state.attempt_spawn(TURRET, secondary_turrets)
                    for turret in secondary_turrets:
                        game_state.attempt_upgrade(turret)
                        if not self.is_upgraded(game_state,turret):
                            ok = False

                if ok:
                    game_state.attempt_spawn(SUPPORT, final_supports)
                    for support in final_supports:
                        game_state.attempt_upgrade(support)
                
    def attack(self,game_state):
        scoredLastRound = (not (self.lastRoundEnemyHealth == game_state.enemy_health)) or game_state.turn_number == 0
        mp = game_state.get_resource(MP)
        if game_state.turn_number < 15 or mp >= min(game_state.turn_number - 10, 20):
            if (self.side == 'right' and scoredLastRound) or (self.side == 'left' and not scoredLastRound):
                self.side = 'right'
                spawn = [14,0]
            else:
                self.side = 'left'
                spawn = [13,0]
            if not scoredLastRound:
                game_state.attempt_spawn(SCOUT, [spawn[0], spawn[1]+1], int(mp / 3))
                game_state.attempt_spawn(SCOUT, spawn, 1000)
            else:
                game_state.attempt_spawn(SCOUT, spawn, 1000)
            self.lastRoundEnemyHealth = game_state.enemy_health

    def is_upgraded(self,game_state, unit):
        x = unit[0]
        y = unit[1]
        return len(game_state.game_map[x,y]) and game_state.game_map[x,y][0].upgraded

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()