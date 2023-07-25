import requests
import time
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

PAXFUL_CLIENT_ID = os.environ.get('PAXFUL_CLIENT_ID')
PAXFUL_CLIENT_SECRET = os.environ.get('PAXFUL_CLIENT_SECRET')
PAXFUL_CLIENT_ID_2 = os.environ.get('PAXFUL_CLIENT_ID_2')
PAXFUL_CLIENT_SECRET_2 = os.environ.get('PAXFUL_CLIENT_SECRET_2')

NOONES_CLIENT_ID = os.environ.get('NOONES_CLIENT_ID')
NOONES_CLIENT_SECRET = os.environ.get('NOONES_CLIENT_SECRET')
MONGO_DB = os.environ.get('MONGO_DB')

def getNoonesAccessToken() -> list:
    response = requests.post('https://auth.noones.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': NOONES_CLIENT_ID, 'client_secret': NOONES_CLIENT_SECRET})
    response2 = requests.post('https://accounts.paxful.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': PAXFUL_CLIENT_ID, 'client_secret': PAXFUL_CLIENT_SECRET})
    response3 = requests.post('https://accounts.paxful.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': PAXFUL_CLIENT_ID_2, 'client_secret': PAXFUL_CLIENT_SECRET_2})
    if response.status_code == 200 and response2.status_code == 200 and response3.status_code == 200:
        print(response.status_code, response2.status_code, response3.status_code)
        return [response.json(), response2.json(), response3.json()]
    else:
        raise Exception("({0}, {1}, {2}) Error obtaining access token".format(response.status_code, response2.status_code, response3.json()))

def insertNewNoonesToken(collection):
    token_json = getNoonesAccessToken()
    insert_result1 = collection.insert_one({'client_id' : NOONES_CLIENT_ID, 'token_json': token_json[0]})
    insert_result2 = collection.insert_one({'client_id' : PAXFUL_CLIENT_ID, 'token_json': token_json[1]})
    insert_result3 = collection.insert_one({'client_id' : PAXFUL_CLIENT_ID_2, 'token_json': token_json[2]})
    print("Inserted token, document IDs {0}, {1}, {2}".format(insert_result1.inserted_id, insert_result2.inserted_id, insert_result3.inserted_id))
    return [token_json[0]["access_token"], token_json[1]["access_token"], token_json[2]["access_token"]]
    
def retrieveNoonesToken(collection):
    return [collection.find_one({'client_id': NOONES_CLIENT_ID}), collection.find_one({'client_id': PAXFUL_CLIENT_ID}), collection.find_one({'client_id': PAXFUL_CLIENT_ID_2})] # ["token_json"]["access_token"],

def updateNoonesToken(collection, new_json1, new_json2, new_json3):
    collection.update_one({'client_id': NOONES_CLIENT_ID}, {'$set': {'token_json': new_json1}})
    collection.update_one({'client_id': PAXFUL_CLIENT_ID}, {'$set': {'token_json': new_json2}})
    collection.update_one({'client_id': PAXFUL_CLIENT_ID_2}, {'$set': {'token_json': new_json3}})
    return [new_json1["access_token"], new_json2["access_token"], new_json3["access_token"]]
    
def refreshNoonesToken(collection):
    return updateNoonesToken(collection, *getNoonesAccessToken())

def initialise():
    global token1, token2, token3, collection
    client = MongoClient(MONGO_DB, server_api=ServerApi('1'))
    db = client['Noones']
    collection = db['noonesJWT']
    try:
        token1, token2, token3 = retrieveNoonesToken(collection)
        token1 = token1["token_json"]["access_token"]
        token2 = token2["token_json"]["access_token"]
        token3 = token3["token_json"]["access_token"]
    except TypeError:
        print("New user detected, creating a new token...")
        token1, token2, token3 = insertNewNoonesToken(collection)
        
def lambda_handler(event, context):
    global token1, token2, token3
    response1 = requests.post("https://api.noones.com/noones/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', "Authorization": "Bearer {0}".format(token1)})
    response2 = requests.post("https://api.paxful.com/paxful/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', "Authorization": "Bearer {0}".format(token2)})
    response3 = requests.post("https://api.paxful.com/paxful/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', "Authorization": "Bearer {0}".format(token3)})
    if (response1.status_code == 200 and response2.status_code == 200 and response3.status_code == 200):
        #print(response.json())
        print("UPDATED...")
    elif (response1.status_code == 401 or response2.status_code == 401 or response3.status_code == 401):
        print("({0}, {1}, {2})Error validating access token".format(response1.json(), response2.json(), response3.json()))
        print("Token expired, refreshing token")
        token1, token2, token3 = refreshNoonesToken(collection)
    else:
        raise Exception("({0}, {1}, {2})Error validating access token".format(response1.status_code, response2.status_code, response3.json()))

initialise()
#while True:
#    run()
#    time.sleep(60)
