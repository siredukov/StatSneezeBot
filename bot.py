"""
    -*- coding: utf-8 -*-
    Simple Telegram Bot with 
    - pyTelegramBotAPI 
    - flask (fro webhook connection)
    - botan (Yandex App Metrics)

"""



import telebot
from telebot import types
import flask
import logging
import botan

from processing import *
import config




WEBHOOK_HOST = 'IP of your server '
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = 'CERT.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = 'KEY.pem' # Path to the ssl private key

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.BOT_TOKEN)


logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(config.BOT_TOKEN)
app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''

# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


location = {}   #data store dictionary

# get information about all commands
@bot.message_handler(commands=["help"])
def helpme(message):
    bot.send_message(message.chat.id, config.HELP_TEXT, parse_mode='HTML')   # Help text is contained in config.py
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/help')
   
    
# initialize user 
@bot.message_handler(commands=["start"])
def start(message):
    if exist("pickles/{}.pickle".format(get_key(message.chat.id))):   # use piclkes file instead database
        bot.send_message(message.chat.id, "You have already started")
    else:
        location[get_key(message.chat.id)] = [[0]]  # initialize new user
        bot.send_message(message.chat.id, "Hi. I'm a bot that collect sneezes statistics")
        helpme(message)  # send command description
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True) # button class
    button_geo = types.KeyboardButton(text="SNEEZED!! !", request_location=True) # button
    keyboard.add(button_geo) # create button
    bot.send_message(message.chat.id, "Tap when sneezed", reply_markup=keyboard) # add button
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/start')
 
# sneeze with location
@bot.message_handler(content_types=['location'])
def locat(message):
    user_key = get_key(message.chat.id)  # get_key return hash string from user id
    if user_key not in location.keys():  # load last 5 location
        location[user_key] = pickle_load(user_key)[-5:] # it is need if program will failed
    location[user_key].append([location[user_key][-1][0] + 1, message.location.longitude, \
                                                message.location.latitude, message.date])  # add sneeze count
    bot.send_message(message.chat.id, "Bless you! It's your {} sneezes".format(str(location[user_key][-1][0])))        
    pickle_dump(user_key, location[get_key(message.chat.id)][-1])  # after recording rewrite to pickles
    location[user_key] = pickle_load(user_key)[-5:] 
    if location[user_key][-1][0] % 10 == 0 :
        bot.send_sticker(message.chat.id, config.PLANTAIN_STICK) #send podorojnik sticker
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/location')


# sneeze without location 
@bot.message_handler(commands=['sneeze'])
def sneeze(message): 
    user_key = get_key(message.chat.id)
    if (get_key(message.chat.id) not in location.keys()):
        location[user_key] = pickle_load(user_key)[-5:]
    location[user_key].append([location[user_key][-1][0] + 1, 'None', 'None', message.date])
                                     # add sneeze count
    bot.send_message(message.chat.id, "Bless you! It's your {} sneezes".format(str(location[user_key][-1][0])))
    pickle_dump(user_key, location[get_key(message.chat.id)][-1])
    location[user_key] = pickle_load(user_key)[-5:] 
    if location[user_key][-1][0] % 10 == 0 :
        bot.send_sticker(message.chat.id, config.PLANTAIN_STICK) #send podorojnik sticker
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/sneeze')

# get last 5 sneezes location
@bot.message_handler(commands=["getgeo"])
def getgeo(message):
    bot.send_message(message.chat.id, coord_to_md(pickle_load(get_key(message.chat.id))[-5:]), parse_mode='HTML')
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/getgeo')

# get all sneezes location
@bot.message_handler(commands=["getall"])
def getall(message):
    bot.send_message(message.chat.id, coord_to_md(pickle_load(get_key(message.chat.id))), parse_mode='HTML')
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/getall')

# get maps with your sneezes
@bot.message_handler(commands=["getmap"])
def getmap(message):
    bot.send_message(message.chat.id, map_render(get_key(message.chat.id)))
    botan.track(config.BOTAN_KEY, message.chat.id, message, '/getmap')
    
# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

#Start flask server
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
debug=True)