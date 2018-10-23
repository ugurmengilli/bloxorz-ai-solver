"""
Author: Ugur Mengilli

Bloxorz Game implemented as an AI problem
"""
import bloxorzutils
from aima.search import Problem


class BloxorzGame(Problem):
    """
    Implements the game as AI Problem and defines the game rules, internal representations and
    interfaces for further usage of the class.
    """

    _BLOCK_VAL = 2
    _GOAL_VAL = -1

    @staticmethod
    def decoder_gen(empty='X', safe='O', block='S', goal='G',
                    col_sep=' ', row_sep='\n'):
        """
        Generate a custom/default decoder needed to translate str representation of a map into tiles.
        :param empty: The block cannot go into an empty tile, even partially.
        :param safe: The block can stand on safe tile at any time at any orientation.
        :param block: Denotes the tile(s) occupied by the block.
        :param goal: The block should stand on the goal tile vertically.
        :param col_sep: Separator between the str representation of the tiles in the same row (separates each col).
        :param row_sep: Separator between the str representation of the rows in a map.
        :return: Decoder to be used in initialization of game parameters
        """
        return {empty: 0,
                safe: 1,
                block: BloxorzGame._BLOCK_VAL,
                goal: BloxorzGame._GOAL_VAL,
                'col_sep': col_sep,
                'row_sep': row_sep
                }

    @staticmethod
    def validate_map(str_map, decoder=None):
        """
        Validate the str map given the decoder. If decoder is not given, default decoder returned
        by BloxorzGame.decoder_gen is used.
        :param str_map: map to be validated.
        :param decoder: decoder to be used in validation. Default decoder is used if not given.
        :return: True if valid, False otherwise.
        """
        # Set default decoder if not given
        decoder = decoder if decoder else BloxorzGame.decoder_gen()

        # CHECK IF RECTANGULAR:
        # Remove delimiters and newlines to have a list of rows represented as string
        filtered_map = str_map.replace(decoder['col_sep'], '') \
            .split(decoder['row_sep'])
        # For rectangular map, number of tile in each row should be equal.
        for i in range(1, len(filtered_map)):
            if len(filtered_map[0]) != len(filtered_map[i]):
                return False  # Even one inequality is enough to be invalid.

        # CHECK NUMBER OF BLOCK TILES:
        if not 0 < str_map.count(
                list(decoder.keys())[list(decoder.values()).index(
                    BloxorzGame._BLOCK_VAL)]) < 3:
            return False

        # CHECK INVALID CHARACTERS:
        for key in decoder:
            # Remove all valid characters to see if any invalid character exists in the map
            str_map = str_map.replace(
                key if 'col_sep' != key != 'row_sep' else decoder[key],
                '')
        return not bool(len(str_map))  # Non-zero length indicate there exist at least one invalid char

    def __init__(self, game_map=None, decoder=None):
        """
        Initialize the game with the given string-represented map. If decoder is not given,
        default one is used to convert the string representation of the map into tiles. If the
        map does not use the default encoding, corresponding decoder should be passed. Custom
        decoders can be generated using BloxorzGame.get_decoder. If map is not given, game is
        initialized with empty parameters. Then, init_board should be used to finish the
        initialization of Problem parameters.
        :param game_map: rectangular, str map corresponding to the encoding generated by BloxorzGame.get_decoder.
        :param decoder: generated by BloxorzGame.get_decoder.
        """
        self._map = None
        self._decoder = decoder if decoder else BloxorzGame.decoder_gen()
        self._state = None

        # Default initial and goal states to initialize the Problem class.
        problem_parameters = (None, None)
        if game_map:
            # Find Problem parameters and _map. Validity of the map will be checked in init_map.
            problem_parameters = self.init_map(game_map, self._decoder)

        Problem.__init__(self, *problem_parameters)
        self._state = [list(self.initial[0]), self.initial[1]]

    def actions(self, state):
        """
        Given any possible state, returns applicable action-argument list.
        :param state: Possible state in the map.
        :return: List of tuples in the form [(act1, arg11, arg12, ...), (act2, arg21, ...), ...]
        """
        # Game actions utilizes class variables, so set the required variables first.
        backup_state = [[self._state[0][0], self._state[0][1]], self._state[1]]
        self._state = state

        # Actions of the game and their possible directions +-x and +-y.
        actions = (self.pitch_block, self.roll_block)
        args = (1, 2, -2, -1)
        act_arg = [(action, arg) for action in actions for arg in args
                   if action(arg, apply_action=False)]

        self._state = backup_state  # Restore the state for convenience
        return act_arg

    def goal_test(self, state):
        """
        Redefine the goal test to handle customizations.
        :param state: to be tested.
        :return: True if goal is reached, False otherwise.
        """
        for goal in self.goal:
            if list(goal[0]) == state[0]:
                return goal[1] == state[1]
        return False

    def init_map(self, str_map, decoder=None):
        """
        Given a valid map where the validity can be checked using BloxorzGame.validate_map, determine the initial
        state and the goal(s if there are more than one). Raises ValueError if str_map is not valid.
        :param str_map: str map corresponding to the encoding generated by BloxorzGame.get_decoder.
        :param decoder: generated by BloxorzGame.get_decoder.
        :return: Initial state of the block, goal state
        """
        # In the worst case, _decoder is default via __init__.
        self._decoder = decoder if decoder else self._decoder

        if not self.validate_map(str_map, self._decoder):
            raise ValueError('Str map contains invalid value(s) undeclared in the decoder '
                             'or invalid initial state or it is not rectangular!')

        # Remove delimiters and newlines to have a list of rows represented as string
        filtered_map = str_map.replace(self._decoder['col_sep'], '') \
            .split(self._decoder['row_sep'])

        # Decode all characters in each row of the map, form a decoded list of rows where each
        # row is a list of adjacent tiles.
        self._map = [[self._decoder[char] for char in line] for line in filtered_map]

        initial = [None, None]
        goal = []
        for j in range(len(self._map)):
            # Check goal tile in j'th row.
            i = 0
            for k in range(self._map[j].count(BloxorzGame._GOAL_VAL)):
                # To find multiple goals in the same row, trim the search area from the previous goal.
                i = self._map[j].index(BloxorzGame._GOAL_VAL, i + 1)
                goal.append(((i, j), 3))

            # Check block tile(s)
            num_block_tiles = self._map[j].count(BloxorzGame._BLOCK_VAL)
            if num_block_tiles == 2:
                # The block is in x-direction
                initial = [(self._map[j].index(BloxorzGame._BLOCK_VAL), j), 1]
            elif not initial[0] and num_block_tiles == 1:
                i = self._map[j].index(BloxorzGame._BLOCK_VAL)
                # If initial[0] is None, this is the first time block-tile was encountered. For
                # the first occurrence, it is the position of the upper portion if aligned with
                # y-axis or of left portion if aligned with x-axis or the position of the block
                # if aligned with z-axis. Either way it is the position of the block.
                initial[0] = (i, j)
                # If there is a block tile below, it is aligned with y-axis, otherwise with z-axis.
                if self._map[i][j + 1] == BloxorzGame._BLOCK_VAL:
                    initial[1] = 2
                else:
                    initial[1] = 3

        # Convert to tuples since they won't change anymore.
        return tuple(initial), tuple(goal)

    def pitch_block(self, d, apply_action=True):
        """
        Pitch the block in the given direction. Pitch is only possible in the direction along
        the long edge if it is horizontal or in any direction when it is vertical. Both the
        position and orientation of the block changes as a result of this action. If pitching
        is not possible,  the action is simply not applied.
        :param d: intended direction of motion
        :param apply_action: Execute the action if True, otherwise check applicability.
        :return: True if motion is applied or can be applied; False otherwise
        """
        # The block can only pitch in the direction of its orientation when horizontal
        # or in any direction when vertical.
        if self._state[1] == abs(d) or self._state[1] == 3:
            # Deep copy for pseudo-pitch
            state = [[self._state[0][0], self._state[0][1]], self._state[1]]

            # Due to the definition of position of state, the block moves 2 tiles along positive
            # direction and 1 tile along negative direction when it is horizontal. However, for
            # the vertical case, it is vice-versa. Also pitching changes the orientation.
            if state[1] == 3:
                displacement = -2 if d < 0 else 1
                state[1] = abs(d)
            else:
                displacement = -1 if d < 0 else 2
                state[1] = 3

            state[0][abs(d) - 1] += displacement

            # Check if the block is in the safe tile for the pseudo-rolling. If the player wants
            # to move into an empty tile, it should be possible. However for the pseudo-pitching
            # case, the purpose is to determine whether it is possible to move or not.
            if not apply_action:
                return self.validate_state(state)

            # If not pseudo, apply the action:
            self._state = state
            return True
        return False

    def result(self, state, action):
        """
        Given any possible state, returns the result of action applied on the state.
        :param state: Possible state in the map.
        :param action: to be applied
        :return: Result of the applied action
        """
        # Game actions utilizes class variables, so set the required variables first.
        backup_state = [[self._state[0][0], self._state[0][1]], self._state[1]]
        self._state = state

        # Knowing the signature of the functions, apply the action.
        action[0](*action[1:])
        # The result is written on the class variable self._state.
        state = [[self._state[0][0], self._state[0][1]], self._state[1]]

        self._state = backup_state
        return state

    def roll_block(self, d, apply_action=True):
        """
        Roll the block in the given direction. Roll is only possible in the direction along the
        short edge since the block flips over its long edge. Position of the block is updated
        but the orientation does not change as a result of this action. If rolling is not
        possible, the action is simply not applied.
        :param d: intended direction of motion
        :param apply_action: Execute the action if True, otherwise check applicability.
        :return: True if motion is applied or can be applied; False otherwise
        """
        # The block cannot roll in the direction of its orientation when horizontal and in any
        # direction when vertical.
        if self._state[1] != abs(d) and self._state[1] != 3:
            # Deep copy for pseudo-roll
            state = [[self._state[0][0], self._state[0][1]], self._state[1]]
            state[0][abs(d) - 1] += int(d / abs(d))

            # Check if the block is in the safe tile for the pseudo-rolling. If the player wants
            # to move into an empty tile, it should be possible. However for the pseudo-rolling
            # case, the purpose is to determine whether it is possible to move or not.
            if not apply_action:
                return self.validate_state(state)

            # If not pseudo, apply the action:
            self._state = state
            return True
        return False

    def validate_state(self, state):
        """
        Validate the state for the current map. If the block is completely in safe tile(s),
        then the state is valid.
        :param state: to be validated
        :return: True if state is valid, False otherwise.
        """
        # Regardless of the block orientation, check the position given by the state definition.
        if not self._map[state[0][1]][state[0][0]]:  # Indexing convention of the map is reverse due to init_map!
            return False

        # For vertical orientation of the block, validation is completed.
        # Find the adjacent occupied tile from the direction give by the state. Having the position (x, y), we have
        #   (x+1, y) for x-oriented block
        #   (x, y+1) for y-oriented block
        if not state[1] == 3 and \
           not self._map[state[0][1] + 1 if state[1] == 2 else state[0][1]] \
                        [state[0][0] + 1 if state[1] == 1 else state[0][0]]:
            return False
        return True

    def value(self, state):
        """
        Not related to the implementations of the search algorithms of interest.
        :param state: -
        :return: 1
        """
        return 1
