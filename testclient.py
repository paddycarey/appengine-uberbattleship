# Battleship client

import json
import random
import requests
import sys
import time

#api = 'https://uberbattleship.appspot.com/'
api = 'http://127.0.0.1:8080/'

def new_game():
	ng = requests.post(api, data='{}').json
	return ng

def join_game(game_id):
	payload = {"action": "addplayer", "args": {}}
	jg = requests.post(api + game_id, data=json.dumps(payload)).json
	return jg

def start_game(game_id, player_id, player_secret_key):
	payload = {"action": "startgame", "args": {"player_id": player_id, "player_secret_key": player_secret_key}}
	sg = requests.post(api + game_id, data=json.dumps(payload)).json
	return sg

def game_started(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json
	return gs['game_state']['started']

def is_my_turn(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json
	if gs['game_state']['winner'] is not None:
		return True
	return gs['game_state']['next_player_id'] == player_id


def is_winner(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json
	if gs['game_state']['winner'] is not None:
		return True
	else:
		return False

def get_winner(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json
	return gs['game_state']['winner']

def get_target_id(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json
	targets = [x for x in gs['game_state']['live_player_ids'] if x != player_id]
	return random.choice(targets)

def fire_shot(game_id, player_id, player_secret_key, target_id, coords):
	payload = {'action': 'fire', 'args': {'player_id': player_id,'player_secret_key': player_secret_key, 'target_id': target_id, 'coords': coords}}
	sg = requests.post(api + game_id, data=json.dumps(payload)).json
	return sg

def get_game_state(game_id, player_id, player_secret_key):
	payload = {"player_id": player_id, "player_secret_key": player_secret_key}
	gs = requests.get(api + game_id, params=payload).json['game_state']
	return gs


if __name__ == '__main__':

	# Get the Game ID
	try:
		game_id = sys.argv[1]
	except IndexError:
		game_id = None

	try:
		start = sys.argv[2] == 'start'
	except IndexError:
		start = False

	# Start or join a game
	if game_id is not None:
		player = join_game(game_id)
		if start:
			game_state = start_game(game_id, player['id'], player['secret_key'])['game_state']
		else:
			game_state = get_game_state(game_id, player['id'], player['secret_key'])
	else:
		ng = new_game()
		game_state = ng['game_state']
		player = ng['player']

	# Check if the game has started
	while not game_started(game_state['game_id'], player['id'], player['secret_key']):
		print "Waiting for game to start: %s" % game_state['game_id']
		time.sleep(5)
	else:
		print "Game started: SPREAD IT ON!"

	while not is_winner(game_state['game_id'], player['id'], player['secret_key']):
		while not is_my_turn(game_state['game_id'], player['id'], player['secret_key']):
			print "Awaiting turn"
		else:
			target_id = get_target_id(game_state['game_id'], player['id'], player['secret_key'])
			coords = [random.randint(0, 9), random.randint(0, 9)]
			try:
				print get_game_state(game_state['game_id'], player['id'], player['secret_key'])['live_player_ids']
				if fire_shot(game_state['game_id'], player['id'], player['secret_key'], target_id, coords)['hit']:
					print "Firing shot!: (%s) %s" % (target_id, str(coords))
					print "HIT!"
				else:
					print "Firing shot!: (%s) %s" % (target_id, str(coords))
					print "MISS!"
			except KeyError:
				continue
	else:
		print "Winner: %s" % get_winner(game_state['game_id'], player['id'], player['secret_key'])
