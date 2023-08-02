import requests
import time
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

environmentVariables = {
    "PAXFUL": {
        "PAXFUL_CLIENT_ID": "PAXFUL_CLIENT_SECRET",
    },
    "NOONES": {
        "NOONES_CLIENT_ID": "NOONES_CLIENT_SECRET",
        "NOONES_CLIENT_ID_2": "NOONES_CLIENT_SECRET_2"
    }
}
MONGO_DB = os.environ.get('MONGO_DB')

def getNoonesAccessToken() -> list:
    accessVariables = {"PAXFUL": {}, "NOONES": {}}
    if environmentVariables["PAXFUL"]:
        for client_id, client_secret in  environmentVariables["PAXFUL"].items():
            response = requests.post('https://accounts.paxful.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': os.environ.get(client_id), 'client_secret': os.environ.get(client_secret)})
            if response.status_code == 200:
                accessVariables["PAXFUL"][client_id] = response.json()
            else:
                print("({0}) Error obtaining access token for {1}".format(response.status_code, client_id))
                #raise Exception("({0}) Error obtaining access token".format(response.status_code))
    if environmentVariables["NOONES"]:
        for client_id, client_secret in  environmentVariables["NOONES"].items():
            response = requests.post('https://auth.noones.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': os.environ.get(client_id), 'client_secret': os.environ.get(client_secret)})
            if response.status_code == 200:
                accessVariables["NOONES"][client_id] = response.json()
            else:
                print("({0}) Error obtaining access token for {1}".format(response.status_code, client_id))
                #raise Exception("({0}) Error obtaining access token".format(response.status_code))
    return accessVariables

def insertNewNoonesToken(collection):
    accessVariables = {"PAXFUL": {}, "NOONES": {}}
    Ttoken_json = getNoonesAccessToken()
    if Ttoken_json["PAXFUL"]:
        for client_id, token_json in  Ttoken_json["PAXFUL"].items():
            insert_result1 = collection.insert_one({'client_id' : os.environ.get(client_id), 'token_json': token_json})
            print("Inserted token, document ID {0} for PAXFUL ID {1}".format(insert_result1.inserted_id, client_id))
            accessVariables["PAXFUL"][client_id] = token_json["access_token"]
    if Ttoken_json["NOONES"]:
        for client_id, token_json in  Ttoken_json["NOONES"].items():
            insert_result1 = collection.insert_one({'client_id' : os.environ.get(client_id), 'token_json': token_json})
            print("Inserted token, document ID {0} for NOONES ID {1}".format(insert_result1.inserted_id), client_id)
            accessVariables["NOONES"][client_id] = token_json["access_token"]
    return accessVariables
    
def retrieveNoonesToken(collection):
    accessVariables = {"PAXFUL": {}, "NOONES": {}}
    if environmentVariables["PAXFUL"]:
        for client_id, client_secret in  environmentVariables["PAXFUL"].items():
            accessVariables["PAXFUL"][client_id] = collection.find_one({'client_id': os.environ.get(client_id)})
    if environmentVariables["NOONES"]:
        for client_id, client_secret in  environmentVariables["NOONES"].items():
            accessVariables["NOONES"][client_id] = collection.find_one({'client_id': os.environ.get(client_id)})
    return accessVariables

def updateNoonesToken(collection, accessV):
    accessVariables = {"PAXFUL": {}, "NOONES": {}}
    if accessV["PAXFUL"]:
        for client_id, new_json in  accessV["PAXFUL"].items():
            collection.update_one({'client_id': os.environ.get(client_id)}, {'$set': {'token_json': new_json}})
            accessVariables["PAXFUL"][client_id] = accessV["PAXFUL"][client_id]["access_token"]
    if accessV["NOONES"]:
        for client_id, new_json in  accessV["NOONES"].items():
            collection.update_one({'client_id': os.environ.get(client_id)}, {'$set': {'token_json': new_json}})
            accessVariables["NOONES"][client_id] = accessV["NOONES"][client_id]["access_token"]
    return accessVariables
    
def refreshNoonesToken(collection):
    return updateNoonesToken(collection, getNoonesAccessToken())

def initialise():
    global tokens, collection
    client = MongoClient(MONGO_DB, server_api=ServerApi('1'))
    db = client['Noones']
    collection = db['noonesJWT']
    try:
        tokens = retrieveNoonesToken(collection)
    except TypeError:
        print("New user(s) detected, creating a new token...")
        tokens = insertNewNoonesToken(collection)
        
def lambda_handler(event, context):
    global tokens
    if tokens["NOONES"]:
        for client_id, token in tokens["NOONES"].items():
            response1 = requests.post("https://api.noones.com/noones/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', "Authorization": "Bearer {0}".format(token)})
            if (response1.status_code == 200):
                #print(response1.json())
                print("UPDATED (NOONES)... for {0}".format(client_id))
            elif (response1.status_code == 401):
                print("({0})Error validating access token(NOONES) for id {1}".format(response1.json(), client_id))
                print("Token expired, refreshing token")
                tokens = refreshNoonesToken(collection)
            else:
                raise Exception("({0})Error validating access token(NOONES) for id {1}".format(response1.status_code, client_id))
    if tokens["PAXFUL"]:
        for client_id, token in tokens["PAXFUL"].items():
            response1 = requests.post("https://api.paxful.com/paxful/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', "Authorization": "Bearer {0}".format(token)})
            if (response1.status_code == 200):
                #print(response1.json())
                print("UPDATED (PAXFUL)... for {0}".format(client_id))
            elif (response1.status_code == 401):
                print("({0})Error validating access token(PAXFUL) for id {1}".format(response1.json(), client_id))
                print("Token expired, refreshing token")
                tokens = refreshNoonesToken(collection)
            else:
                raise Exception("({0})Error validating access token(PAXFUL) for id {1}".format(response1.status_code, client_id))
    

initialise()
