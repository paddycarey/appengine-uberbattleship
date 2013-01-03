import json
import logging
import models
import settings
import sys
import webapp2
from google.appengine.api import memcache
from raven import Client

# Init Sentry client for error reporting
client = Client(settings.SENTRY_DSN)


class BaseHandler(webapp2.RequestHandler):

    """Simple base handler to provide things like error handling, json encoding and cache management"""

    def cached_result(self, function, kwargs_dict, cache_time):

        """Retrieve data from cache, or run function with provided args if not already cached"""

        # Build a cache key from the function name and args
        cache_key = '%s_%s' % (str(function.__name__), str(kwargs_dict))
        # attempt to retrieve object from cache
        cached_object = memcache.get(cache_key)

        # Run function if object not in cache
        if cached_object is None:
            # Run function
            result_object = function(**kwargs_dict)
            # Throw 404 if not found
            if result_object:
                # Store result object in cache
                memcache.set(cache_key, result_object, cache_time)
            # Return the result object
            return result_object
        else:
            # Return the cached object
            return cached_object

    def json_response(self, json_response_dict):

        # Set the response headers
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        # Dump the response to string and output
        json_response_str = json.dumps(json_response_dict)
        self.response.write(json_response_str)

    def handle_exception(self, exception, debug):

        """Override the default exception handler to log exceptions to sentry (if configured) aswell as the appengine log"""

        # Log the exception
        logging.exception(exception)

        # Log the error to sentry
        client.capture('Exception',
            exc_info=sys.exc_info(),
            data={
                'sentry.interfaces.Http': {
                    'method': self.request.method,
                    'url': self.request.path_url,
                    'query_string': self.request.query_string,
                    'headers': dict(self.request.headers),
                    'env': dict((
                        ('REMOTE_ADDR', self.request.environ['REMOTE_ADDR']),
                        ('SERVER_NAME', self.request.environ['SERVER_NAME']),
                        ('SERVER_PORT', self.request.environ['SERVER_PORT']),
                    )),
                }
            },
        )

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)

        response_dict = {'error': unicode(exception)}

        # Write a simple JSON error msg in the response
        self.json_response(response_dict)


class GameHandler(BaseHandler):

    def get(self, game_id):

        if game_id:
            player_id = self.request.get('player_id')
            player_secret_key = self.request.get('player_secret_key')
            game = models.Game.all().filter('game_id = ', game_id).get()
            self.json_response({'game_state': game.get_game_state(player_id, player_secret_key)})
        else:
            games = models.Game.all()
            self.json_response([{'game_state': game.game_state} for game in games if game.is_winner()])

    def post(self, game_id):

        actions = {
            'fire': self.fire,
            'addplayer': self.addplayer,
            'startgame': self.startgame,
        }
        logging.info(game_id)
        if game_id:
            req = json.loads(self.request.body)
            game = models.Game.all().filter('game_id = ', game_id).get()
            try:
                logging.info(str(req))
                actions[req['action']](game, **req['args'])
            except AttributeError:
                self.abort(404)
        else:
            game = models.Game()
            game.put()
            self.json_response({'player': game.player(game.player_ids[0]), 'game_state': game.game_state})

    def fire(self, game, player_id, player_secret_key, target_id, coords):
        if game.player_authed(player_id, player_secret_key):
            resp = {}
            resp['hit'] = game.fire_shot(player_id, player_secret_key, target_id, coords)
            resp['game_state'] = game.get_game_state(player_id, player_secret_key)
            self.json_response(resp)
        else:
            self.abort(403)

    def addplayer(self, game):
        newplayer = game.add_player()
        game.put()
        self.json_response(newplayer)

    def startgame(self, game, player_id, player_secret_key):
        if game.player_authed(player_id, player_secret_key):
            game.start_game()
            self.json_response({'game_state': game.get_game_state(player_id, player_secret_key)})
        else:
            self.abort(403)
