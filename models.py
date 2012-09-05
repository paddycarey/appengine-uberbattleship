from google.appengine.ext import db
from customproperties import DerivedProperty
from operator import itemgetter
import helpers
import json
import uuid


class Game(db.Model):

    # Use a text property to store a JSON representation
    # of the current game state

    started = db.BooleanProperty(default=False)
    _board_state = db.TextProperty(default='{}')

    def get_board_state(self):
        return json.loads(self._board_state)

    def set_board_state(self, value):
        self._board_state = json.dumps(value)

    board_state = property(get_board_state, set_board_state)

    # Store a UUID to use as a Game ID

    game_uuid = db.StringProperty()

    @DerivedProperty()
    def game_id(self):
        if not self.game_uuid:
            self.game_uuid = str(uuid.uuid4())
        return self.game_uuid

    # Store a list of the game's players

    _players = db.ListProperty(db.Text)

    @property
    def players(self):
        return [json.loads(player) for player in self._players]

    def add_player(self):
        player_id = str(uuid.uuid4())
        player_secret_key = str(uuid.uuid4())
        player_num = len(self.players)
        player = {'num': player_num, 'id': player_id, 'secret_key': player_secret_key, 'alive': True}
        self._players.append(db.Text(json.dumps(player)))
        return player

    last_player_id = db.StringProperty()

    @property
    def next_player_id(self):

        players = [player for player in self.players if player['alive']]
        players = sorted(players, key=itemgetter('num'))

        last_player_idx = 0
        next_player_idx = 0

        for idx, player in enumerate(players):
            if player['id'] == self.last_player_id:
                last_player_idx = idx
                next_player_idx = last_player_idx + 1
                break

        try:
            next_player_id = players[next_player_idx]['id']
        except IndexError:
            next_player_id = players[0]['id']
        return next_player_id

    @property
    def player_ids(self):
        return [player['id'] for player in self.players]

    def kill_player(self, player_id):
        players = self.players
        new_players = []
        for player in players:
            if player['id'] == player_id:
                player['alive'] = False
            new_players.append(db.Text(json.dumps(player)))
        self._players = new_players
        self.put()

    def player_authed(self, player_id, player_secret_key):
        for player in self.players:
            if player_id == player['id'] and player_secret_key == player['secret_key']:
                return True
        else:
            return False

    def player(self, player_id):
        for player in self.players:
            if player_id == player['id']:
                return player
        else:
            return {}

    # Game logic

    def fire_shot(self, player_id, player_secret_key, target_id, coord):
        if not self.player_authed(player_id, player_secret_key):
            raise Exception('Not authorised... TRY A-FUCKING-GAIN!')
        if not self.started:
            raise Exception('Game hasn\'t started yet, CALM DOWN!!!1!')
        if not player_id == self.next_player_id:
            raise Exception('You are not the next player, WAIT YOUR TURN!')
        self.last_player_id = player_id
        board_state = self.board_state
        if board_state[target_id][coord[0]][coord[1]] is not None and not board_state[target_id][coord[0]][coord[1]] == 'MISS!':
            board_state[target_id][coord[0]][coord[1]] = 'HIT!'
            self.board_state = board_state
            self.put()
            if not self.check_alive(target_id):
                self.kill_player(target_id)
            return True
        else:
            board_state[target_id][coord[0]][coord[1]] = 'MISS!'
            self.board_state = board_state
            self.put()
            return False

    def check_alive(self, target_id):

        board = self.board_state[target_id]
        for row in board:
            for column in row:
                if column is not None and column != 'HIT!':
                    return True
        else:
            return False

    def start_game(self):
        if not self.started and len(self.players) > 1:
            boards = self.board_state
            for player in self.players:
                ships = helpers.ships
                board = helpers.generate_board(10)
                board = helpers.randomise_board(board, ships)
                boards[player['id']] = board
            self.board_state = boards
            self.started = True
            self.put()
            return True
        else:
            return False

    # Check for a winner

    winner = db.StringProperty()

    def is_winner(self):

        players_alive = [player for player in self.players if player['alive']]
        if len(self.players) > 1 and len(players_alive) > 1:
            return False
        else:
            if not len(self.players) == 1:
                self.winner = players_alive[0]['id']
                self.started = False
                return True
            else:
                return False

    # Return current game state as dict

    @property
    def game_state(self):
        game_state = {}
        game_state['game_id'] = self.game_id
        game_state['started'] = self.started
        game_state['player_ids'] = self.player_ids
        game_state['live_player_ids'] = [player['id'] for player in self.players if player['alive']]
        game_state['board_state'] = self.board_state
        game_state['next_player_id'] = self.next_player_id
        game_state['winner'] = self.winner
        return game_state

    def get_game_state(self, player_id, player_secret_key):
        if self.player_authed(player_id, player_secret_key):
            game_state = self.game_state
            all_boards = game_state['board_state']
            try:
                board = all_boards[player_id]
            except KeyError:
                board = []
            game_state['board_state'] = board
            return game_state
        else:
            raise Exception('Not authorised... TRY A-FUCKING-GAIN!')

    def put(self, *args, **kwargs):
        if not self.players:
            self.add_player()
        self.is_winner()
        super(Game, self).put(*args, **kwargs)
