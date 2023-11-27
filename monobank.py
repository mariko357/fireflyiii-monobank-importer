import requests
from time import time, sleep

API_BASE = "https://api.monobank.ua"
CURRENCY_REQUEST_LOCATION = "/bank/currency"
CLIENT_INFO_LOCATION = "/personal/client-info"
WEBHOOK_LOCATION = "/personal/webhook"
STATEMENT_LOCATION = "/personal/statement"
API_STATEMENT_TIMEOUT = 61

class Monobank:
    token = ""

    currencies = []
    userInfo = dict
    userAccounts = []
    userJars = []

    def __init__(self, userToken):
        self.token = userToken
    
    def makeRequest(self, location):
        return requests.get(API_BASE + location, headers = {"X-Token": self.token})
        
    def getCurrencies(self):
        response =  self.makeRequest(CURRENCY_REQUEST_LOCATION)

        responseJson = response.json()

        self.currencies = []
        for i in responseJson:
            self.currencies.append(i)

        return self.currencies
    
    def setWebhookUrl(self, webhookUrl):
        response = requests.post(API_BASE + WEBHOOK_LOCATION, headers = {"X-Token": self.token}, json = {"webHookUrl": webhookUrl})
        return response

    def getClientInfo(self):
        response = self.makeRequest(CLIENT_INFO_LOCATION)

        responseJson = response.json()

        self.userInfo = {
            "clientId": responseJson["clientId"],
            "name": responseJson["name"],
            "webHookUrl": responseJson["webHookUrl"],
            "permissions": responseJson["permissions"],
        }

        for i in responseJson["accounts"]:
            self.userAccounts.append(i)
        
        if "jars" in responseJson:
            for i in responseJson["jars"]:
                self.userJars.append(i)

        return self.userAccounts
    
    def getStatement(self, accountId, timeFrom, timeTo = 0):

        transactions = []

        lastRequestTime = int(time())

        timeTo = int(time()) if timeTo == 0 else timeTo

        if timeTo - timeFrom > 30 * 24 * 60 * 60:
            response = self.makeRequest(STATEMENT_LOCATION + 
                        "/" + str(accountId) + "/" + str(timeFrom)
                        + ("/" + str(timeFrom + 30 * 24 * 60 * 60)))
            transactions = response.json()
            while(int(time()) - lastRequestTime < API_STATEMENT_TIMEOUT): sleep(1)
            if len(transactions) == 500:
                transactions += self.getStatement(accountId, int(transactions[499]["time"]), timeFrom + 30 * 24 * 60 * 60)
                while(int(time()) - lastRequestTime < API_STATEMENT_TIMEOUT): sleep(1)
            transactions += self.getStatement(accountId, timeFrom + 30 * 24 * 60 * 60, timeTo)
            
        else:
            response = self.makeRequest(STATEMENT_LOCATION + 
                                    "/" + str(accountId) + "/" + str(timeFrom)
                                    + ("/" + str(timeTo)))
            transactions = response.json()
            if len(transactions) == 500:
                while(int(time()) - lastRequestTime < API_STATEMENT_TIMEOUT): sleep(1)
                transactions += self.getStatement(accountId, int(transactions[499]["time"]), timeTo)
        
        return transactions