# Add 'libs' dir to the python path
import os
import sys
this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(this_dir, 'libs'))

# Import required modules
import webapp2
import handlers

# Define our apps routes
ROUTES = [(r'/(.*)', handlers.GameHandler)]

# Main WSGI App
app = webapp2.WSGIApplication(ROUTES, debug=True)
