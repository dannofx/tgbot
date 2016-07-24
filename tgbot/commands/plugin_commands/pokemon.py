from tgbot.commands.command import Command
from dateutil import parser
from datetime import timedelta
from datetime import datetime
from threading import Thread
from google.protobuf.internal import encoder
from google.protobuf.message import DecodeError
from s2sphere import *
from geopy.geocoders import GoogleV3
from gpsoauth import perform_master_login, perform_oauth
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.adapters import ConnectionError
from requests.models import InvalidURL
from DictObject import DictObject
from tgbot.commands.plugin_commands.pokemongo import pokemon_pb2

import re
import random
import pickle
import os
import sys
import struct
import json
import requests
import getpass
import time
import threading 

args = None
pokemons = {}
pokesearch_config_file = 'poke_search_config.json'
proximity_limit = 50

# Command options
subscribe_opt = 'Subscribe to pokeupdates'
unsubscribe_opt = 'Unsubscribe to pokeupdates'
update_location_opt = 'Update location'
update_proximity_opt = 'Set proximity'
exclude_pokemons_opt = 'Exclude pokemons from search'
include_pokemons_opt = 'Include pokemons in search'
include_all_opt = 'Include all'
exclude_all_opt = 'Exclude all'
list_pokemons_opt = 'List all pokemons'
done_opt = 'Done'

#Action id's
update_location_action = 1
update_proximity_action = 2
include_action = 3
exclude_action = 4
force_reset_location = False

def get_current_directory():
    return os.path.realpath( 
                os.path.join(os.getcwd(), os.path.dirname(__file__)))

def get_pokemon_directory():
    return os.path.join(get_current_directory(), 'pokemongo')

class PokemonCommand(Command):            
    receivers = []

    
    def __init__(self, logger, message_sender):
        global pokemon_thread
        super().__init__(logger, message_sender)
        receivers_path = self.receivers_file_path()
        if os.path.isfile(receivers_path):
            rfile = open(receivers_path, 'rb')
            self.receivers = pickle.load(rfile)
            rfile.close()

        self.pokemon_list = self.load_pokemon_list()

        self.pokemon_thread_stop = None
        self.pokemon_thread = None
        self.start_thread()

    def start_thread(self):
        self.pokemon_thread_stop = threading.Event()
        self.pokemon_thread = Thread(target=self.run_pokemon_search, args=(1, self.pokemon_thread_stop), daemon=True)
        self.pokemon_thread.start()   
    
    def stop_thread(self):
        self.pokemon_thread_stop.set() 

    def run_pokemon_search(self, arg1, stop_event):
        global args
        args = get_pokemon_config()
        time.sleep(6)
        while (not stop_event.is_set()):
            look_for_pokemons(self, stop_event)
            time.sleep(30)

    def process(self, chat_id, user_id, username, arguments):

        self.register_for_reply(chat_id, user_id)
        options = [[subscribe_opt], \
                    [unsubscribe_opt]
                    ]
        if self.is_user_privileged(username):
            complementary = [[update_location_opt],\
                            [update_proximity_opt],\
                            [include_pokemons_opt],\
                            [exclude_pokemons_opt],\
                            ]
            options.extend(complementary)
        options.append([list_pokemons_opt])
        self.message_sender.send_options(chat_id, options)

        # if (len(arguments) > 0):
        #     if arguments[0] == 'add':
        #         if chat_id in self.receivers:
        #             return "User already added"
        #         else:
        #             self.receivers.append(chat_id)
        #             self.save_receivers()
        #             return "User added"
        #     elif arguments[0] == 'remove':
        #         if chat_id in self.receivers:
        #             self.receivers.remove(chat_id)
        #             self.save_receivers()
        #             return "User removed"
        #         else:
        #             return "User has not been added yet."
        #     elif arguments[0] == 'test':
        #         self.message_sender.request_location(chat_id, "Provide a location to update the search.")
        #         self.register_for_reply(chat_id, user_id)
        #         return


    def process_expected_reply(self, chat_id, user_id, username, reply, action_id):
        if  isinstance(reply, str):
            if reply == subscribe_opt:
                if chat_id in self.receivers:
                    return "Conversation already subscribed."
                else:
                    self.receivers.append(chat_id)
                    self.save_receivers()
                    return "Conversation subscribed"
            elif reply == unsubscribe_opt:
                if chat_id in self.receivers:
                    self.receivers.remove(chat_id)
                    self.save_receivers()
                    return "Conversation unsubscribed"
                else:
                    return "Conversation has not been unsubscribed yet."
            elif reply == update_location_opt:
                if chat_id == user_id:
                    # private conversation
                    self.message_sender.request_location(chat_id, "Provide a location to update the search.")
                    self.register_for_reply(chat_id, user_id, update_location_action)
                else:
                    #no available in public room
                    return "The location can be updated just in a private conversation."
                return
            elif reply == update_proximity_opt:
                options = []
                for i in range(1,(proximity_limit+1)):
                    options.append([str(i)])
                text =  "Set the proximity to be used for the search (bigger number = bigger distance, longer waiting time)"
                self.message_sender.send_options(chat_id, options, text)
                self.register_for_reply(chat_id, user_id, update_proximity_action)
                return
            elif reply == include_pokemons_opt:
                return self.show_include_menu(chat_id, user_id)
            elif reply == exclude_pokemons_opt:
                return self.show_exclude_menu(chat_id, user_id)
            elif reply == include_all_opt:
                return
            elif reply == exclude_all_opt:
                return
            elif reply == list_pokemons_opt:
                return '\n'.join(self.pokemon_list)
            elif reply == done_opt:
                pass
        
        if action_id == update_location_action:
            return self.update_location(reply)
        elif action_id == update_proximity_action:
            return self.update_proximity(reply)

    def update_location(self, location):
        global force_reset_location
        if hasattr(location, 'longitude') and \
            hasattr(location, 'latitude'):
            args.location = str(location.latitude) + ',' + str(location.longitude)
            save_pokemon_config()
            force_reset_location = True
            self.stop_thread()
            self.start_thread()
            return "Location updated!"

    def load_pokemon_list(self):
        file_path = os.path.join(get_pokemon_directory(), 'pokemonlist.txt')
        return [line.strip() for line in open(file_path, 'r')]

    def update_proximity(self, proximity):
        global args
        if  not isinstance(proximity, str):
            return
        update_value = 0
        try:
            update_value = int(proximity)
        except ValueError:
            return 'That\'s not a number!'

        if update_value < 0 or update_value > proximity_limit:
            return 'Not in range!'

        args.step_limit = update_value
        save_pokemon_config()
        self.stop_thread()
        self.start_thread()
        return "Proximity updated!"

    def show_include_menu(self, chat_id, user_id):
        options = [[include_all_opt],[done_opt]]
        if args.only:#only is a list with numbers or false
            not_added = [[pokemon] for i, pokemon in enumerate(self.pokemon_list) if  (i+1) not in args.only]
            options.extend(not_added)
        else:
            options.extend(self.pokemon_list)
        self.message_sender.send_options(chat_id, options)
        self.register_for_reply(chat_id, user_id, include_action)


    def show_exclude_menu(self, chat_id, user_id):
        options = [[exclude_all_opt],[done_opt]]
        if args.only:#only is a list with numbers or false
            added = [[pokemon] for i, pokemon in enumerate(self.pokemon_list) if  (i+1) in args.only]
            options.extend(added)
        else:
            options.extend(self.pokemon_list)
        self.message_sender.send_options(chat_id, options)
        self.register_for_reply(chat_id, user_id, exclude_action)

    
    def save_receivers(self):
        receivers_path = self.receivers_file_path()
        rfile = open(receivers_path, 'wb')
        new_d = pickle.dump(self.receivers, rfile)
        rfile.close()

    def notify_about_pokemon(self, pokemon):

        id_text = "{0:0>3}".format(pokemon["id"])
        remaining_time = datetime.utcfromtimestamp(pokemon["disappear_time"] - time.time())
        text = ("========\nPokemon found!\n"
                "Name: " + pokemon["name"] + "\n"
                "Id: " + id_text + "\n"
                "Disappear time: " + time.ctime(int(pokemon["disappear_time"])) + "\n"
                "Time left: " + remaining_time.strftime('%M:%S')+ "\n"
                "Image: http://assets.pokemon.com/assets/cms2/img/pokedex/detail/" + id_text+ ".png\n"
                "Location: "
                )
        for receiver in self.receivers:
            self.message_sender.send_message(receiver, str(text), False)
            self.message_sender.send_location(receiver,pokemon["lat"],pokemon["lng"])

    def get_local_time(self):
        date_str =  str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        return "My time is {}".format(date_str)

        return "{}The message [{}] has been successfully scheduled on {}"\

    def get_human_string_date(self,datetime):
        return str(datetime.strftime('%Y-%m-%d %H:%M:%S'))

    def receivers_file_path(self):
        file_path = os.path.join(get_pokemon_directory(), 'pokereceivers.dat')
        self.logger.info("FILE PATH "+file_path)
        return file_path

    def help(self):
        return "Pokemon notifier" 
    def name(self):
        return "pokemon"
    
    def description(self):
        return "Pokemon notifier"

    def stop(self):
        self.stop_thread()


# -- Pokemon search methods

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'
LOGIN_URL = \
    'https://sso.pokemon.com/sso/login?service=https://sso.pokemon.com/sso/oauth2.0/callbackAuthorize'
LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'
APP = 'com.nianticlabs.pokemongo'

credentials_path = os.path.join(get_pokemon_directory(), 'credentials.json')
with open(credentials_path) as file:
    credentials = json.load(file)
    PTC_CLIENT_SECRET = credentials.get('ptc_client_secret', None)
    ANDROID_ID = credentials.get('android_id', None)
    SERVICE = credentials.get('service', None)
    CLIENT_SIG = credentials.get('client_sig', None)
    GOOGLEMAPS_KEY = credentials.get('gmaps_key', None)

    SESSION = requests.session()
    SESSION.headers.update({'User-Agent': 'Niantic App'})
    SESSION.verify = False

    global_password = None
    global_token = None
    access_token = None
    DEBUG = True
    VERBOSE_DEBUG = False  # if you want to write raw request/response to the console
    COORDS_LATITUDE = 0
    COORDS_LONGITUDE = 0
    COORDS_ALTITUDE = 0
    FLOAT_LAT = 0
    FLOAT_LONG = 0
    NEXT_LAT = 0
    NEXT_LONG = 0
    default_step = 0.001
    api_endpoint = None
    gyms = {}
    pokestops = {}
    numbertoteam = {  # At least I'm pretty sure that's it. I could be wrong and then I'd be displaying the wrong owner team of gyms.
        0: 'Gym',
        1: 'Mystic',
        2: 'Valor',
        3: 'Instinct',
    }
    origin_lat, origin_lon = None, None
    is_ampm_clock = False

def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer

def parse_unicode(bytestring):
    #decoded_string = bytestring.decode(sys.getfilesystemencoding())
    return bytestring


def debug(message):
    if DEBUG:
        print('[-] {}'.format(message))


def time_left(ms):
    s = ms / 1000
    (m, s) = divmod(s, 60)
    (h, m) = divmod(m, 60)
    return (h, m, s)


def encode(cellid):
    output = []
    encoder._VarintEncoder()(output.append, cellid)
    return b''.join(output)


def getNeighbors():
    origin = CellId.from_lat_lng(LatLng.from_degrees(FLOAT_LAT, FLOAT_LONG)).parent(15)
    walk = [origin.id()]

    # 10 before and 10 after

    next = origin.next()
    prev = origin.prev()
    for i in range(10):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return walk


def f2i(float):
    return struct.unpack('<Q', struct.pack('<d', float))[0]


def f2h(float):
    return hex(struct.unpack('<Q', struct.pack('<d', float))[0])


def h2f(hex):
    return struct.unpack('<d', struct.pack('<Q', int(hex, 16)))[0]


def retrying_set_location(location_name):
    """
    Continue trying to get co-ords from Google Location until we have them
    :param location_name: string to pass to Location API
    :return: None
    """

    while True:
        try:
            set_location(location_name)
            return
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            debug(
                'retrying_set_location: geocoder exception ({}), retrying'.format(
                    str(e)))
        time.sleep(1.25)


def set_location(location_name):
    geolocator = GoogleV3()
    prog = re.compile('^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$')
    global origin_lat
    global origin_lon
    if prog.match(location_name):
        local_lat, local_lng = [float(x) for x in location_name.split(",")]
        alt = 0
        origin_lat, origin_lon = local_lat, local_lng
    else:
        loc = geolocator.geocode(location_name)
        origin_lat, origin_lon = local_lat, local_lng = loc.latitude, loc.longitude
        alt = loc.altitude
        print('[!] Your given location: {}'.format(loc.address.encode('utf-8')))

    print(('[!] lat/long/alt: {} {} {}'.format(local_lat, local_lng, alt)))
    set_location_coords(local_lat, local_lng, alt)


def set_location_coords(lat, longitude, alt):
    global COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE
    global FLOAT_LAT, FLOAT_LONG
    FLOAT_LAT = lat
    FLOAT_LONG = longitude
    COORDS_LATITUDE = f2i(lat)  # 0x4042bd7c00000000 # f2i(lat)
    COORDS_LONGITUDE = f2i(longitude)  # 0xc05e8aae40000000 #f2i(long)
    COORDS_ALTITUDE = f2i(alt)


def get_location_coords():
    return (COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE)


def retrying_api_req(service, api_endpoint, access_token, *args, **kwargs):
    while True:
        try:
            response = api_req(service, api_endpoint, access_token, *args,
                               **kwargs)
            if response:
                return response
            debug('retrying_api_req: api_req returned None, retrying')
        except (InvalidURL, ConnectionError, DecodeError) as e:
            debug('retrying_api_req: request error ({}), retrying'.format(
                str(e)))
        time.sleep(1)


def api_req(service, api_endpoint, access_token, *args, **kwargs):
    p_req = pokemon_pb2.RequestEnvelop()
    p_req.rpc_id = 1469378659230941192

    p_req.unknown1 = 2

    (p_req.latitude, p_req.longitude, p_req.altitude) = \
        get_location_coords()

    p_req.unknown12 = 989

    if 'useauth' not in kwargs or not kwargs['useauth']:
        p_req.auth.provider = service
        p_req.auth.token.contents = access_token
        p_req.auth.token.unknown13 = 14
    else:
        p_req.unknown11.unknown71 = kwargs['useauth'].unknown71
        p_req.unknown11.unknown72 = kwargs['useauth'].unknown72
        p_req.unknown11.unknown73 = kwargs['useauth'].unknown73

    for arg in args:
        p_req.MergeFrom(arg)

    protobuf = p_req.SerializeToString()

    r = SESSION.post(api_endpoint, data=protobuf, verify=False)

    p_ret = pokemon_pb2.ResponseEnvelop()
    p_ret.ParseFromString(r.content)

    if VERBOSE_DEBUG:
        print('REQUEST:')
        print(p_req)
        print('Response:')
        print(p_ret)
        print('''

''')
    time.sleep(0.51)
    return p_ret


def get_api_endpoint(service, access_token, api=API_URL):
    profile_response = None
    while not profile_response:
        profile_response = retrying_get_profile(service, access_token, api,
                                                None)
        if not hasattr(profile_response, 'api_url'):
            debug(
                'retrying_get_profile: get_profile returned no api_url, retrying')
            profile_response = None
            continue
        if not len(profile_response.api_url):
            debug(
                'get_api_endpoint: retrying_get_profile returned no-len api_url, retrying')
            profile_response = None

    return 'https://%s/rpc' % profile_response.api_url

def retrying_get_profile(service, access_token, api, useauth, *reqq):
    profile_response = None
    while not profile_response:
        profile_response = get_profile(service, access_token, api, useauth,
                                       *reqq)
        if not hasattr(profile_response, 'payload'):
            debug(
                'retrying_get_profile: get_profile returned no payload, retrying')
            profile_response = None
            continue
        if not profile_response.payload:
            debug(
                'retrying_get_profile: get_profile returned no-len payload, retrying')
            profile_response = None

    return profile_response

def get_profile(service, access_token, api, useauth, *reqq):
    req = pokemon_pb2.RequestEnvelop()
    req1 = req.requests.add()
    req1.type = 2
    if len(reqq) >= 1:
        req1.MergeFrom(reqq[0])

    req2 = req.requests.add()
    req2.type = 126
    if len(reqq) >= 2:
        req2.MergeFrom(reqq[1])

    req3 = req.requests.add()
    req3.type = 4
    if len(reqq) >= 3:
        req3.MergeFrom(reqq[2])

    req4 = req.requests.add()
    req4.type = 129
    if len(reqq) >= 4:
        req4.MergeFrom(reqq[3])

    req5 = req.requests.add()
    req5.type = 5
    if len(reqq) >= 5:
        req5.MergeFrom(reqq[4])
    return retrying_api_req(service, api, access_token, req, useauth=useauth)

def login_google(username, password):
    print('[!] Google login for: {}'.format(username))
    r1 = perform_master_login(username, password, ANDROID_ID)
    r2 = perform_oauth(username,
                       r1.get('Token', ''),
                       ANDROID_ID,
                       SERVICE,
                       APP,
                       CLIENT_SIG, )
    return r2.get('Auth')

def login_ptc(username, password):
    print('[!] PTC login for: {}'.format(username))
    head = {'User-Agent': 'Niantic App'}
    r = SESSION.get(LOGIN_URL, headers=head)
    if r is None:
        return render_template('nope.html', fullmap=fullmap)

    try:
        jdata = json.loads(r.content)
    except ValueError as e:
        debug('login_ptc: could not decode JSON from {}'.format(r.content))
        return None

    # Maximum password length is 15 (sign in page enforces this limit, API does not)

    if len(password) > 15:
        print('[!] Trimming password to 15 characters')
        password = password[:15]

    data = {
        'lt': jdata['lt'],
        'execution': jdata['execution'],
        '_eventId': 'submit',
        'username': username,
        'password': password,
    }
    r1 = SESSION.post(LOGIN_URL, data=data, headers=head)

    ticket = None
    try:
        ticket = re.sub('.*ticket=', '', r1.history[0].headers['Location'])
    except Exception as e:
        if DEBUG:
            print(r1.json()['errors'][0])
        return None

    data1 = {
        'client_id': 'mobile-app_pokemon-go',
        'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
        'client_secret': PTC_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'code': ticket,
    }
    r2 = SESSION.post(LOGIN_OAUTH, data=data1)
    access_token = re.sub('&expires.*', '', r2.content)
    access_token = re.sub('.*access_token=', '', access_token)

    return access_token


def get_heartbeat(service,
                  api_endpoint,
                  access_token,
                  response, ):
    m4 = pokemon_pb2.RequestEnvelop.Requests()
    m = pokemon_pb2.RequestEnvelop.MessageSingleInt()
    m.f1 = int(time.time() * 1000)
    m4.message = m.SerializeToString()
    m5 = pokemon_pb2.RequestEnvelop.Requests()
    m = pokemon_pb2.RequestEnvelop.MessageSingleString()
    m.bytes = b'05daf51635c82611d1aac95c0b051d3ec088a930'
    m5.message = m.SerializeToString()
    walk = sorted(getNeighbors())
    m1 = pokemon_pb2.RequestEnvelop.Requests()
    m1.type = 106
    m = pokemon_pb2.RequestEnvelop.MessageQuad()
    m.f1 = b''.join(map(encode, walk))
    m.f2 = b'\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'
    m.lat = COORDS_LATITUDE
    m.long = COORDS_LONGITUDE
    m1.message = m.SerializeToString()
    response = get_profile(service,
                           access_token,
                           api_endpoint,
                           response.unknown7,
                           m1,
                           pokemon_pb2.RequestEnvelop.Requests(),
                           m4,
                           pokemon_pb2.RequestEnvelop.Requests(),
                           m5, )

    try:
        payload = response.payload[0]
    except (AttributeError, IndexError):
        return

    heartbeat = pokemon_pb2.ResponseEnvelop.HeartbeatPayload()
    heartbeat.ParseFromString(payload)
    return heartbeat

def get_token(service, username, password):
    """
    Get token if it's not None
    :return:
    :rtype:
    """

    global global_token
    if global_token is None:
        if service == 'ptc':
            global_token = login_ptc(username, password)
        else:
            global_token = login_google(username, password)
        return global_token
    else:
        return global_token

def get_pokemon_config():

    args_dict = None
    config_path = os.path.join(get_pokemon_directory(), pokesearch_config_file)
    with open(config_path) as file:
        args_dict = json.load(file)
    # args_dict = {
    #                 'auth_service': 'google',
    #                 'username': 'xxxx@xxxxx',
    #                 'password': 'm0015d041f363',
    #                 'location': '20.6704923,-103.3713086',
    #                 'step-limit': 10,
    #                 'ignore': False,
    #                 'only': '13',
    #                 'display-pokestop': False,
    #                 'display-gym': False,
    #                 'locale': 'en',
    #                 'onlylure': False,
    #                 'ampm_clock': False,
    #                 'debug': False
    #             }
    return DictObject.objectify(args_dict)

def save_pokemon_config():
    global args
    config_path = os.path.join(get_pokemon_directory(), pokesearch_config_file)
    with open(config_path, 'w') as outfile:
        json.dump(args, outfile)

@memoize
def login(args):
    global global_password
    if not global_password:
      if args.password:
        global_password = args.password
      else:
        global_password = getpass.getpass()

    access_token = get_token(args.auth_service, args.username, global_password)
    if access_token is None:
        raise Exception('[-] Wrong username/password')

    print('[+] RPC Session Token: {} ...'.format(access_token[:25]))

    api_endpoint = get_api_endpoint(args.auth_service, access_token)
    if api_endpoint is None:
        raise Exception('[-] RPC server offline')

    print('[+] Received API endpoint: {}'.format(api_endpoint))

    profile_response = retrying_get_profile(args.auth_service, access_token,
                                            api_endpoint, None)
    if profile_response is None or not profile_response.payload:
        raise Exception('Could not get profile')

    print('[+] Login successful')

    payload = profile_response.payload[0]
    profile = pokemon_pb2.ResponseEnvelop.ProfilePayload()
    profile.ParseFromString(payload)
    print('[+] Username: {}'.format(profile.profile.username))

    creation_time = \
        datetime.fromtimestamp(int(profile.profile.creation_time)
                               / 1000)
    print('[+] You started playing Pokemon Go on: {}'.format(
        creation_time.strftime('%Y-%m-%d %H:%M:%S')))

    for curr in profile.profile.currency:
        print('[+] {}: {}'.format(curr.type, curr.amount))

    return api_endpoint, access_token, profile_response

def look_for_pokemons(telegram_command, stop_event):
    global force_reset_location
    if args.auth_service not in ['ptc', 'google']:
        print('[!] Invalid Auth service specified')
        return

    print(('[+] Locale is ' + args.locale))
    pokemonsJSON = json.load(
        open(get_pokemon_directory() + '/locales/pokemon.' + args.locale + '.json'))
    if args.debug:
        global DEBUG
        DEBUG = True
        print('[!] DEBUG mode on')

    # only get location for first run
    if not (FLOAT_LAT and FLOAT_LONG) or force_reset_location:
        if force_reset_location:
            force_reset_location = False
        print('[+] Getting initial location')
        retrying_set_location(args.location)
    else:
        print('EXISTING LOCATION')

    if args.ampm_clock:
        global is_ampm_clock
        is_ampm_clock = True

    api_endpoint, access_token, profile_response = login(args)

    clear_stale_pokemons()

    steplimit = int(args.step_limit)

    ignore = []
    only = []
    if args.ignore:
        ignore = [i.lower().strip() for i in args.ignore.split(',')]
    elif args.only:
        only = args.only #[i.lower().strip() for i in args.only.split(',')]

    pos = 1
    x = 0
    y = 0
    dx = 0
    dy = -1
    steplimit2 = steplimit**2
    for step in range(steplimit2):

        if stop_event.is_set():
            return
        #starting at 0 index
        debug('looping: step {} of {}'.format((step+1), steplimit**2))
        #debug('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(steplimit2, x, y, pos, dx, dy))
        # Scan location math
        if -steplimit2 / 2 < x <= steplimit2 / 2 and -steplimit2 / 2 < y <= steplimit2 / 2:
            set_location_coords(x * 0.0025 + origin_lat, y * 0.0025 + origin_lon, 0)
        if x == y or x < 0 and x == -y or x > 0 and x == 1 - y:
            (dx, dy) = (-dy, dx)

        (x, y) = (x + dx, y + dy)

        process_step(args, api_endpoint, access_token, profile_response,
                     pokemonsJSON, ignore, only, telegram_command)

        print(('Completed: ' + str(
            ((step+1) + pos * .25 - .25) / (steplimit2) * 100) + '%'))

    global NEXT_LAT, NEXT_LONG
    if (NEXT_LAT and NEXT_LONG and
            (NEXT_LAT != FLOAT_LAT or NEXT_LONG != FLOAT_LONG)):
        print(('Update to next location %f, %f' % (NEXT_LAT, NEXT_LONG)))
        set_location_coords(NEXT_LAT, NEXT_LONG, 0)
        NEXT_LAT = 0
        NEXT_LONG = 0
    else:
        set_location_coords(origin_lat, origin_lon, 0)

def process_step(args, api_endpoint, access_token, profile_response,
                 pokemonsJSON, ignore, only, telegram_command):
    print(('[+] Searching for Pokemon at location {} {}'.format(FLOAT_LAT, FLOAT_LONG)))
    origin = LatLng.from_degrees(FLOAT_LAT, FLOAT_LONG)
    step_lat = FLOAT_LAT
    step_long = FLOAT_LONG
    parent = CellId.from_lat_lng(LatLng.from_degrees(FLOAT_LAT,
                                                     FLOAT_LONG)).parent(15)
    h = get_heartbeat(args.auth_service, api_endpoint, access_token,
                      profile_response)
    hs = [h]
    seen = set([])

    for child in parent.children():
        latlng = LatLng.from_point(Cell(child).get_center())
        set_location_coords(latlng.lat().degrees, latlng.lng().degrees, 0)
        hs.append(
            get_heartbeat(args.auth_service, api_endpoint, access_token,
                          profile_response))
    set_location_coords(step_lat, step_long, 0)
    visible = []

    for hh in hs:
        try:
            for cell in hh.cells:
                for wild in cell.WildPokemon:
                    hash = wild.SpawnPointId + ':' \
                        + str(wild.pokemon.PokemonId)
                    if hash not in seen:
                        visible.append(wild)
                        seen.add(hash)
                if cell.Fort:
                    for Fort in cell.Fort:
                        if Fort.Enabled == True:
                            if Fort.GymPoints and args.display_gym:
                                gyms[Fort.FortId] = [Fort.Team, Fort.Latitude,
                                                     Fort.Longitude, Fort.GymPoints]

                            elif Fort.FortType \
                                and args.display_pokestop:
                                expire_time = 0
                                if Fort.LureInfo.LureExpiresTimestampMs:
                                    expire_time = datetime\
                                        .fromtimestamp(Fort.LureInfo.LureExpiresTimestampMs / 1000.0)\
                                        .strftime("%H:%M:%S")
                                if (expire_time != 0 or not args.onlylure):
                                    pokestops[Fort.FortId] = [Fort.Latitude,
                                                              Fort.Longitude, expire_time]
        except AttributeError:
            break

    for poke in visible:
        pokeid = str(poke.pokemon.PokemonId)
        pokename = pokemonsJSON[pokeid]
        print ('POKEMON DETECTED')
        if args.ignore:
            if pokename.lower() in ignore or pokeid in ignore:
                print ('POKEMON DISCARDED 1')
                continue
        elif args.only:
            if int(pokeid) not in only:
                print ('POKEMON DISCARDED 2')
                continue
        disappear_timestamp = time.time() + poke.TimeTillHiddenMs \
            / 1000

        if poke.SpawnPointId in pokemons:
            oldtime = pokemons[poke.SpawnPointId]["disappear_time"]
            timedifference = abs(disappear_timestamp - oldtime)
            if timedifference < 3.0:
                print ('POKEMON DISCARDED BY TIME')
                return #already notified pokemon without change

        pokemon_dict = {
            "lat": poke.Latitude,
            "lng": poke.Longitude,
            "disappear_time": disappear_timestamp,
            "id": poke.pokemon.PokemonId,
            "name": pokename
        }
        pokemons[poke.SpawnPointId] = pokemon_dict
        telegram_command.notify_about_pokemon(pokemon_dict)
        print("[+] Adding pokemon %s at %f, %f dtime: %s id: %s timetill: %d" % (
                pokename, poke.Latitude, poke.Longitude, time.ctime(int(disappear_timestamp)), poke.pokemon.PokemonId, poke.TimeTillHiddenMs))

def clear_stale_pokemons():
    current_time = time.time()

    try:
        for pokemon_key in pokemons.keys():
            pokemon = pokemons[pokemon_key]
            if current_time > pokemon['disappear_time']:
                print ("[+] removing stale pokemon %s at %f, %f from list" % (
                    pokemon['name'].encode('utf-8'), pokemon['lat'], pokemon['lng']))
                del pokemons[pokemon_key]
    except RuntimeError as error:
        print('ERROR: ' + str(error))

