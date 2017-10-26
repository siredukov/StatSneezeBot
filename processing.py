"""
   Some function for processing data 
"""


import time
from hashlib import md5
import pickle


def coord_to_md(coord_list):
    if coord_list[0][0] == 0:
        del coord_list[0]
        
        
    text = ''
    for coord in coord_list:
        street = 'None None'
        if coord[1] != 'None':
            street = gmaps.reverse_geocode((coord[2], coord[1]))[0]['formatted_address']
        text +="<b># {}</b> {} {} \n".format(coord[0], street, unix_to_local(coord[3]))
    return text

def exist(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True  

def check_mem(user_coord):
    return len(user_coord) > 100

def pickle_load(filename):
    with open(filename, 'rb') as f:
        obj = pickle.load(f)
    return obj

def pickle_dump(user_hash, location):
    filename = str(user_hash) + '.pickle' 
    if exist(filename):
        obj = pickle_load(filename)
        obj.extend(location[user_hash])
    else:
        obj = location[user_hash]
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)
               
def get_key(user_id):
    return md5(str(user_id).encode()).hexdigest()

def unix_to_local(t):
    return time.strftime("%D %H:%M", time.localtime(int(t)))