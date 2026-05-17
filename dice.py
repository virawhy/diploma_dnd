import webapp2
import logging
import json
import requests
import os

root = '/dice/'
RANDOM_ORG_API_KEY = os.environ.get('RANDOM_ORG_API_KEY')

class DiceHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json-rpc'
        data = json.loads(self.request.body)
        if data['method'] == 'random':
            if not RANDOM_ORG_API_KEY:
                self.response.set_status(503)
                self.response.write(json.dumps({'error': 'Random.org API key is not configured'}))
                return

            req = {
                "jsonrpc": "2.0",
                "method": "generateDecimalFractions",
                "params": {
                    'apiKey': RANDOM_ORG_API_KEY,
                    'n': data['n'],
                    'decimalPlaces': 2,
                },
                "id": 1
            }
            result = requests.post(
                url='https://api.random.org/json-rpc/1/invoke',
                json=req,
                headers={'Content-Type': 'application/json-rpc'},
            )
            self.response.write(result.content)
            return

        self.response.write('{}')

app = webapp2.WSGIApplication([
        (root + 'f', DiceHandler),
    ], debug = True)

