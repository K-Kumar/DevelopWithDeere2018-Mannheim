# Copyright (c) 2018 Deere & Company
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import sys
sys.path.insert(0, './python_modules')
from requests_oauthlib.oauth1_session import OAuth1Session
import requests
import datetime
import os
import pprint
import json
import logging
import random

#############################################################################
# Demo Constants

ORG_OVERRIDE = "" # Specify a specific org here, otherwise the default is to use the first org in your org list

DEFAULT_LATITUDE = "49.4728807"          # Used if Google Maps cannot resolve the address above
DEFAULT_LONGITUDE = "8.476208999999999"  # Used if Google Maps cannot resolve the address above

#############################################################################
# API Constants

GOOGLE_MAPS_KEY = 'UPDATE YOUR GOOGLE MAPS KEY HERE'

# Root URI
BASE_URI = 'https://sandboxapi.deere.com/platform/'

# OAuth Constants
CLIENT_KEY = 'UPDATE YOUR CLIENT APP CREDENTIALS HERE'
CLIENT_SECRET = 'UPDATE YOUR CLIENT APP CREDENTIALS HERE'
OAUTH_TOKEN = 'UPDATE YOUR CLIENT APP CREDENTIALS HERE'
OAUTH_TOKEN_SECRET = 'UPDATE YOUR CLIENT APP CREDENTIALS HERE'

#############################################################################
# Contribution Definition Constants

NOTIFICATION_CONTRIBUTION_DEFINITION = 'UPDATE YOUR CLIENT APP CONTRIBUTION CREDENTIALS HERE!'
MAP_LAYER_CONTRIBUTION_DEFINITION = 'UPDATE YOUR CLIENT APP CONTRIBUTION CREDENTIALS HERE!'
ASSET_CONTRIBUTION_DEFINITION = 'UPDATE YOUR CLIENT APP CONTRIBUTION CREDENTIALS HERE!'

#############################################################################

