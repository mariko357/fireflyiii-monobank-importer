import requests

INFO_LOCATION = "api/v1/about/"
NEW_TRANSACTION = "api/v1/transactions"

class FireflyAPI:
    token = ""
    baseURL = ""

    def __init__(self, baseUrl, token):
        self.token = token
        self.baseURL = baseUrl

    def getRequest(self, path):
        return requests.get(self.baseURL + path, headers={"accept": "application/vnd.api+json",
                                                          "Authorization": "Bearer " + self.token,
                                                          "Content-Type": "application/json"})
    
    def postRequest(self, path, data):
        response = requests.post(self.baseURL + path, headers={"accept": "application/vnd.api+json",
                                                          "Authorization": "Bearer " + self.token,
                                                          "Content-Type": "application/json"},
                                                        json = data)
        return response

    def testConnection(self):
        if not len(self.token):
            return False
        if self.getRequest(INFO_LOCATION).status_code != 200:
            return False
        return True
    
    def addTransaction(self, transactions, config = {"error_if_duplicate_hash": False,
                                        "apply_rules": False,
                                        "fire_webhooks": False,
                                        "group_title": ""}, 
                                        ):
        
        if len(transactions) == 0:
            return
        
        data = {**config}
        data["transactions"] = transactions

        response = self.postRequest(NEW_TRANSACTION, data)
        
        return response