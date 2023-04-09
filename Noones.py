import requests
import time
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
MONGO_DB = os.environ.get('MONGO_DB')

def getNoonesAccessToken() -> dict:
    response = requests.post('https://auth.noones.com/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'client_credentials', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("({0})Error obtaining access token {1}".format(response.status_code, response.json()))

def insertNewNoonesToken(collection):
    token_json = getNoonesAccessToken()
    insert_result = collection.insert_one({'client_id' : CLIENT_ID, 'token_json': token_json})
    print("Inserted token, document ID:", insert_result.inserted_id)
    return token_json["access_token"]
    
def retrieveNoonesToken(collection):
    result = collection.find_one({'client_id': CLIENT_ID})
    return result

def updateNoonesToken(collection, new_json):
    collection.update_one({'client_id': CLIENT_ID}, {'$set': {'token_json': new_json}})
    print("Token updated")
    return new_json["access_token"]
    
def refreshNoonesToken(collection):
    return updateNoonesToken(collection, getNoonesAccessToken())

def initialise():
    global token, collection
    client = MongoClient(MONGO_DB, server_api=ServerApi('1'))
    db = client['Noones']
    collection = db['noonesJWT']
    try:
        token = retrieveNoonesToken(collection)["token_json"]["access_token"]
    except TypeError:
        print("New user detected, creating a new token...")
        token = insertNewNoonesToken(collection)
        #token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIyNDhlN2I2LTA0ODktNDNiOC1iODE3LTc2MjYwYzViMmIzNiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2ODA5ODY3ODYsImlhdCI6MTY4MDk4Njc4NiwiZXhwIjoxNjgxODUwNzg2LCJpc3MiOiJodHRwczovL2F1dGgubm9vbmVzLmNvbSIsImF1ZCI6Im5vb25lcyIsImp0aSI6InZsOVFndHE2RlFLdzNqZ09JNHRpZFU0dWRndlR5RmttIiwiY2xpZW50X2lkIjoiRHJCckIyTVZxQm5BczlaTmQzS3ZYaGxmWWlBQ0ozRkRyVnpWWndGRGUwbDNFS3FTIiwic3ViIjoiODEwYTQ2NDAtNjhmZC00YzhmLWI4ZjUtODFjOWEyMTlkMjI5Iiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBwaG9uZSBhZGRyZXNzIGNpdGl6ZW5zaGlwIHN0YXR1cyBzdGFmZiB3ZWJob29rOndlYmhvb2s6ZXZlbnQ6d2FsbGV0IHdlYmhvb2s6d2ViaG9vazpldmVudDp0cmFkZS1tZ20gd2ViaG9vazp3ZWJob29rOmV2ZW50OnRyYWRlLWNoYXQgd2ViaG9vazp3ZWJob29rOmV2ZW50OnByb2ZpbGUtbWdtLWFuZC1pbmZvIHdlYmhvb2s6d2ViaG9vazpldmVudDppbnZvaWNlIG5vb25lczp3YWxsZXQ6bmV3LWFkZHJlc3Mgbm9vbmVzOndhbGxldDpsaXN0LWFkZHJlc3NlcyBub29uZXM6d2FsbGV0OmNvbnZlcnQgbm9vbmVzOndhbGxldDpjb252ZXJzaW9uLXF1b3RlcyBub29uZXM6d2FsbGV0OmJhbGFuY2Ugbm9vbmVzOnVzZXI6dW50cnVzdCBub29uZXM6dXNlcjp1bmJsb2NrIG5vb25lczp1c2VyOnR5cGVzIG5vb25lczp1c2VyOnRydXN0IG5vb25lczp1c2VyOnRvdWNoIG5vb25lczp1c2VyOm1lIG5vb25lczp1c2VyOmluZm8gbm9vbmVzOnVzZXI6YmxvY2tlZC1saXN0IG5vb25lczp1c2VyOmJsb2NrIG5vb25lczp1c2VyOmFmZmlsaWF0ZSBub29uZXM6dHJhbnNhY3Rpb25zOmFsbCBub29uZXM6dHJhZGU6c3RhcnQgbm9vbmVzOnRyYWRlOnNoYXJlLWxpbmtlZC1iYW5rLWFjY291bnQgbm9vbmVzOnRyYWRlOnJlb3BlbiBub29uZXM6dHJhZGU6cmVsZWFzZSBub29uZXM6dHJhZGU6cGFpZCBub29uZXM6dHJhZGU6bG9jYXRpb25zIG5vb25lczp0cmFkZTpsaXN0IG5vb25lczp0cmFkZTpnZXQgbm9vbmVzOnRyYWRlOmZ1bmQgbm9vbmVzOnRyYWRlOmRpc3B1dGUtcmVhc29ucyBub29uZXM6dHJhZGU6ZGlzcHV0ZSBub29uZXM6dHJhZGU6Y29tcGxldGVkIG5vb25lczp0cmFkZS1jaGF0OnBvc3Qgbm9vbmVzOnRyYWRlLWNoYXQ6bGF0ZXN0IG5vb25lczp0cmFkZS1jaGF0OmltYWdlOnVwbG9hZCBub29uZXM6dHJhZGUtY2hhdDppbWFnZTphZGQgbm9vbmVzOnRyYWRlLWNoYXQ6aW1hZ2Ugbm9vbmVzOnRyYWRlLWNoYXQ6Z2V0IG5vb25lczp0cmFkZTpjYW5jZWwgbm9vbmVzOnRyYWRlOmFkZC1wcm9vZiBub29uZXM6cHJvZmlsZSBub29uZXM6cGF5bWVudC1tZXRob2Q6bGlzdCBub29uZXM6cGF5bWVudC1tZXRob2QtZ3JvdXA6bGlzdCBub29uZXM6cGF5bWVudC1tZXRob2Q6ZmVlIG5vb25lczpvZmZlcjp1cGRhdGUtcHJpY2Ugbm9vbmVzOm9mZmVyOnVwZGF0ZSBub29uZXM6b2ZmZXI6dHVybi1vbiBub29uZXM6b2ZmZXI6dHVybi1vZmYgbm9vbmVzOm9mZmVyLXRhZzpsaXN0IG5vb25lczpvZmZlci1zeXMtdGFnOnJvYm93YXkgbm9vbmVzOm9mZmVyOnByaWNlcyBub29uZXM6b2ZmZXI6cHJpY2Ugbm9vbmVzOm9mZmVyOmxpc3Qgbm9vbmVzOm9mZmVyOmdldCBub29uZXM6b2ZmZXI6ZGVsZXRlIG5vb25lczpvZmZlcjpkZWFjdGl2YXRlIG5vb25lczpvZmZlcjpjcmVhdGUgbm9vbmVzOm9mZmVyOmFsbCBub29uZXM6b2ZmZXI6YWN0aXZhdGUgbm9vbmVzOm5vdGlmaWNhdGlvbnM6dW5yZWFkLWNvdW50IG5vb25lczpub3RpZmljYXRpb25zOnVucmVhZCBub29uZXM6bm90aWZpY2F0aW9uczptYXJrLXJlYWQgbm9vbmVzOm5vdGlmaWNhdGlvbnM6bGlzdCBub29uZXM6bm90aWZpY2F0aW9uczpsYXN0IG5vb25lczpraW9zazp0cmFuc2FjdGlvbnMgbm9vbmVzOmZlZWRiYWNrOnJlcGx5IG5vb25lczpmZWVkYmFjazpsaXN0IG5vb25lczpmZWVkYmFjazpnaXZlIG5vb25lczplbWFpbCBub29uZXM6Y3VycmVuY3k6cmF0ZXMgbm9vbmVzOmN1cnJlbmN5Omxpc3Qgbm9vbmVzOmN1cnJlbmN5OmJ0YyBub29uZXM6Y3J5cHRvOmxpc3Qgbm9vbmVzOmJhbms6bGlzdCBub29uZXM6YmFuay1hY2NvdW50OnVwZGF0ZSBub29uZXM6YmFuay1hY2NvdW50Omxpc3Qgbm9xzZSwiYXV0aF9kZWxlZ2F0ZWQiOmZhbHNlfQ.VJurn87X7NsQKZDEt7o3SbNv2W5cS4wzZ49h6FFklnTOz1eJ86Cna_aT7mKlBoPsTMn_9k8-BBzbluKc2-8a7dzUbqEYObb1t7wHXAxzZSwiYXV0aF9kZWxlZ2F0ZWQiOmZhbHNlfQ.VJurn83AO4jQukYpsoR-kY11LmMzsT5NAF9buMFI49eJ7s1m7hMEa1yZtwlzM-BcFmyCywm20CeuyrBzgibHg7reHNI_wajGuvAVw7S5Ov7Cyz4QaYsQs3Ixu3oUC3d9oCHPpsxQuaQGAGWp5hMEa1yZtwlzM-BcFmyCywm20CeuyrBzgibHg7reHNI_GiXxVPzxfLp98rEofKxsYbxyRMqI5ZY5MPDY4mETzM6gnWcNROkuLXFd6QVeDd-LIja0sPowZEE6os9RcU95D3Yz5kzZza2DoAS5A"

def run():
    global token
    response = requests.post("https://api.noones.com/noones/v1/user/me", headers={'content-type': 'application/x-www-form-urlencoded', "Authorization": "Bearer {0}".format(token)})
    #print(response.json())
    if (response.status_code == 200):
        #print(response.json())
        print("UPDATED...")
    elif (response.status_code == 403):
        print("Token expired, refreshing token")
        token = refreshNoonesToken(collection)
    else:
        raise Exception("({0})Error validating access token {1}".format(response.status_code, response.json()))

initialise()

while True:
    run()
    time.sleep(60)