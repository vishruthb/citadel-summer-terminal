import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import deque


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
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
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.gaps = [] # Keeping track of gaps in their defense.
                       # Could also expand to keep track of tiles not covered by turrets.
        #self.corner_defenses = {'TURRET': [[3,12], [24,12]], 'WALL': [[0, 13], [1, 13], [2,13], [3,13], [24, 13], [25, 13], [26, 13], [27,13]]}
        #self.middle_defenses = {"TURRET": [], 'WALL': []} # Add to these whenever adding defenses to middle and corners. 
        self.defense_by_importance = {1: {"TURRET": [[3,12], [24,12], [9, 10], [18,10]], "WALL": [[3, 13], [24, 13], [9,11], [18,11], [0,13], [27,13], [1, 13], [26,13], [25,13], [2,13]], "SUPPORT": [], "UPGRADE": []},
                                      2: {"TURRET": [[4,12], [23,12]], "WALL": [[8,10], [19,10], [5,12], [22,12], [23,13], [4,13],[10,10], [17,10]], "SUPPORT": [], "UPGRADE": [[23,13], [24,13], [3,13], [4,13]]},
                                      3: {"TURRET": [], "WALL": [[6,11], [7,10], [20,10], [21, 11], [11,9], [12,9], [15,9], [16,9], [13,10], [14,10]] , "SUPPORT": [[12,6], [13,6], [14,6]], "UPGRADE": [[9,11], [18,11], [17,10], [10,10]]},
                                      4: {"TURRET": [], "WALL": [[1,12], [2,12], [25,12], [26,12]],"SUPPORT": [[4,11], [5,10], [6,9], [21,9], [22,10], [23, 11], [7,8], [13,7], [20,8], [12,5], [13,5], [14,5]], "UPGRADE": [[19,10], [8,10], [12,6], [13,6], [14,6]]},
                                      5: {"TURRET": [[13,9], [14,9]], "WALL": [], "SUPPORT": [], "UPGRADE": [[13,10], [14,10], [13,9], [14,9], [4,11], [5,10], [6,9], [21,9], [22,10], [23, 11], [7,8], [13,7], [20,8], [12,5], [13,5], [14,5]]}} 
                                      # This will contain all of the hardcoding for our defense. Goes in decreasing importance.
        self.check_left_corner = {"X": [0, 1, 2, 3, 4], "Y": [14, 15, 16]}
        self.check_right_corner = {"X": [23,24,25,26,27], "Y": [14,15,16]}
        self.unupgraded_turrets = deque() 
    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def spawn_edge(self, game_state, unit_type, x_locs):
        spawn_locs = []
        for x_loc in x_locs:
            y_loc = 0
            if x_loc < 14:
                y_loc = 13 - x_loc
            else:
                y_loc = x_loc - 14
            spawn_locs.append([x_loc, y_loc])

        game_state.attempt_spawn(unit_type, spawn_locs)

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        if game_state.turn_number == 0:
            self.starting_defenses(game_state)
        else:
            self.build_defences(game_state)

        #self.build_reactive_defense(game_state) # Need to figure out good way to spend structure points if we have left over from switching up for attacks and repairs. 

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base    ### Offense will completely depend on round number (and a bit of randomness)
        ### Should implement something to check if defense is complete (or nearly)
        if game_state.turn_number < 5:
            ### Quick damage strategies for accumulating structure points. 
            if game_state.get_resource(game_state.MP) > 8:
                game_state.attempt_spawn(SCOUT, num = 1000, locations = self.least_damage_spawn_location(game_state, [[13,0], [14,0], [7,6], [20,6], [9,4], [18,4], [5,8], [22,8]])) # Checking attacking corners as well as some random locations. 
                     # To make better: Edit least damage spawn so it also returns damage,
                     # Check damage before doing any spawns, don't want to throw away                         #  points.
        elif 5 <= game_state.turn_number < 15:
            ### TODO
            pass

        elif 15 <= game_state.turn_number < 25:
            ### TODO
            pass

        else:
            ### Should be good to implement general behavior here, just increasing unit stack. 
            pass








    def starting_defenses(self, game_state):
        '''
        Builds starting defenses. Prioritizes building defenses at corner. Try different strategies.
        1. 4 upgraded turrets covering all tiles
        2. More balanced defense. 
        '''
        turret_locations = [[3,12], [24,12], [9,10], [18,10]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)


    def build_defences(self, game_state): #
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        Implement logic so that if we have an unupgraded turret, we keep at least 1 structure point.

        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        while len(self.unupgraded_turrets) >= 1 and game_state.get_resource(game_state.SP) >= 6:
            game_state.attempt_upgrade(self.unupgraded_turrets.popleft())
        #if self.unupgraded_turrets and game_state.get_resource(game_state.SP) >=6:
            #print('can upgrade')
            #to_upgrade = self.unupgraded_turrets.popleft()
            #game_state.attempt_upgrade(to_upgrade) 
        # else:
        #     game_state.SP -=1
        # Builds units by importance. Triple for loop kinda ugly, but it rarely is ever actually executed. 
        #number_placed = 0
        save = (len(self.unupgraded_turrets) != 0)

        for i in self.defense_by_importance.keys():

            level = self.defense_by_importance[i]
    
            for tower_type in ["TURRET", "WALL", "SUPPORT", "UPGRADE"]:
                if tower_type == "TURRET":
                    number_placed = game_state.attempt_spawn(TURRET, level[tower_type])
                elif tower_type == "WALL":
                    game_state.attempt_spawn(WALL, level[tower_type], save = save)
                elif tower_type == "SUPPORT":
                    game_state.attempt_spawn(SUPPORT, level[tower_type], save = save)
                else:
                    game_state.attempt_upgrade(level["UPGRADE"])
                if tower_type == "TURRET" and number_placed:
                    for j in range(number_placed+1):
                        #print('appending')
                        self.unupgraded_turrets.append(level[tower_type][j])
                
        

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        # Initialize lists to pass into this to check each corner, middle, etc. 
        # Will modify to have it return number of units by type and upgrade
        total_units = {"TURRET": 0, "WALL": 0, "UPGRADED_TURRET": 0, "UPGRADED_WALL": 0}
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        if unit.unit_type == TURRET:
                            if unit.upgraded:
                                total_units["UPGRADED_TURRET"] +=1
                            else:
                                total_units["TURRET"] +=1
                        else:
                            if unit.upgraded:
                                total_units["UPGRADED_WALL"] +=1
                            else:
                                total_units["WALL"] +=1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
