from monobank import Monobank
from fireflyiii import FireflyAPI
import shelve
from time import time, sleep
from datetime import datetime
import requests
import zoneinfo
import os
import yaml

LAST_TRANSACTION_TIMEOUT = 60

FIREFLYIII_INSTANCE = os.environ["FIREFLYIII_INSTANCE"]
FIREFLYIII_TOKEN = os.environ["FIREFLYIII_TOKEN"]
MONOBANK_TOKEN = os.environ["MONOBANK_TOKEN"]
TIMEZONE = os.environ["TIMEZONE"]

CURRENCIES = {
784: "AED",
971: "AFN",
8: "ALL",
51: "AMD",
532: "ANG",
973: "AOA",
32: "ARS",
36: "AUD",
533: "AWG",
944: "AZN",
977: "BAM",
52: "BBD",
50: "BDT",
975: "BGN",
48: "BHD",
108: "BIF",
60: "BMD",
96: "BND",
68: "BOB",
984: "BOV",
986: "BRL",
44: "BSD",
64: "BTN",
72: "BWP",
933: "BYN",
84: "BZD",
124: "CAD",
976: "CDF",
947: "CHE",
756: "CHF",
948: "CHW",
990: "CLF",
152: "CLP",
156: "CNY",
170: "COP",
970: "COU",
188: "CRC",
931: "CUC",
192: "CUP",
132: "CVE",
203: "CZK",
262: "DJF",
208: "DKK",
214: "DOP",
12: "DZD",
818: "EGP",
232: "ERN",
230: "ETB",
978: "EUR",
242: "FJD",
238: "FKP",
826: "GBP",
981: "GEL",
936: "GHS",
292: "GIP",
270: "GMD",
324: "GNF",
320: "GTQ",
328: "GYD",
344: "HKD",
340: "HNL",
332: "HTG",
348: "HUF",
360: "IDR",
376: "ILS",
356: "INR",
368: "IQD",
364: "IRR",
352: "ISK",
388: "JMD",
400: "JOD",
392: "JPY",
404: "KES",
417: "KGS",
116: "KHR",
174: "KMF",
408: "KPW",
410: "KRW",
414: "KWD",
136: "KYD",
398: "KZT",
418: "LAK",
422: "LBP",
144: "LKR",
430: "LRD",
426: "LSL",
434: "LYD",
504: "MAD",
498: "MDL",
969: "MGA",
807: "MKD",
104: "MMK",
496: "MNT",
446: "MOP",
929: "MRU",
480: "MUR",
462: "MVR",
454: "MWK",
484: "MXN",
979: "MXV",
458: "MYR",
943: "MZN",
516: "NAD",
566: "NGN",
558: "NIO",
578: "NOK",
524: "NPR",
554: "NZD",
512: "OMR",
590: "PAB",
604: "PEN",
598: "PGK",
608: "PHP",
586: "PKR",
985: "PLN",
600: "PYG",
634: "QAR",
946: "RON",
941: "RSD",
643: "RUB",
646: "RWF",
682: "SAR",
90: "SBD",
690: "SCR",
938: "SDG",
752: "SEK",
702: "SGD",
654: "SHP",
925: "SLE",
706: "SOS",
968: "SRD",
728: "SSP",
930: "STN",
222: "SVC",
760: "SYP",
748: "SZL",
764: "THB",
972: "TJS",
934: "TMT",
788: "TND",
776: "TOP",
949: "TRY",
780: "TTD",
901: "TWD",
834: "TZS",
980: "UAH",
800: "UGX",
840: "USD",
997: "USN",
940: "UYI",
858: "UYU",
927: "UYW",
860: "UZS",
926: "VED",
928: "VES",
704: "VND",
548: "VUV",
882: "WST",
950: "XAF",
961: "XAG",
959: "XAU",
955: "XBA",
956: "XBB",
957: "XBC",
958: "XBD",
951: "XCD",
960: "XDR",
952: "XOF",
964: "XPD",
953: "XPF",
962: "XPT",
994: "XSU",
963: "XTS",
965: "XUA",
999: "XXX",
886: "YER",
710: "ZAR",
967: "ZMW",
932: "ZWL",
}

def monoToFireflyiiiTransaction(transaction, account, categories = {"budget_id": "",
                                                                    "category_id": "",
                                                                    "tags": ""}):
    
    transactionAmount = str(abs(int(transaction["amount"]) / 100))
    transactionForeignAmount = str(abs(int(transaction["operationAmount"]) / 100))
    
    transactionType = "withdrawal" if transaction["amount"] < 0 else "deposit"

    transactionTime = transaction["time"]
    timezone = zoneinfo.ZoneInfo(key=TIMEZONE)
    ctime = datetime.fromtimestamp(transactionTime, timezone).strftime("%Y-%m-%dT%H:%M:%S%z")
    ftime = ctime[:-2] + ":" + ctime[-2:]

    convRate = "%.2f" % (transaction["amount"] / transaction["operationAmount"])

    foreignCurrency = CURRENCIES[transaction["currencyCode"]]

    transactionNote = str()
    if convRate != 1:
        transactionNote += "Conversion rate: " + str(convRate) + " UAH/" + foreignCurrency + "; "
    if "cashbackAmount" in transaction.keys():
        if transaction["cashbackAmount"] != 0:
            transactionNote += "Cashback amount: " + str(transaction["cashbackAmount"]/100) + " UAH" + "; "
    if "comment" in transaction.keys():
        transactionNote += "Transfer comment:" + transaction["comment"] + "; "

    fireflyTransaction = {**categories}
    fireflyTransaction["type"] = transactionType
    fireflyTransaction["date"] = ftime
    fireflyTransaction["amount"] = transactionAmount
    fireflyTransaction["description"] = transaction["description"]
    fireflyTransaction["foreign_amount"] = transactionForeignAmount
    fireflyTransaction["foreign_currency_code"] = foreignCurrency
    fireflyTransaction["notes"] = transactionNote
    

    if transactionType == "withdrawal":
        fireflyTransaction["source_id"] = str(account)
    else:
        fireflyTransaction["destination_id"] = str(account)
    
    return fireflyTransaction

def testInternentConnection(url = "https://google.com"):
    try:
        res = requests.get(url)
        if res.status_code != 200:
            return False
    except:
        return False
    return True

if __name__ == "__main__":

    print("Invoking the script;")

    api = FireflyAPI(FIREFLYIII_INSTANCE, FIREFLYIII_TOKEN)
    monobank = Monobank(MONOBANK_TOKEN)
    database = shelve.open("database.db")
    
    yamlConfig = {}
    with open("config.yaml", "r") as configFile:
        try:
            yamlConfig = yaml.safe_load(configFile)
        except yaml.YAMLError as exc:
            print(exc)

    accountsConfig = []
    for index, i in enumerate(yamlConfig["MonobankAccounts"]):
        accountsConfig.append({})
        for j in i:
            accountsConfig[index] = {**accountsConfig[index], **j}

    if not "lastTransactionTime" in database:
        database["lastTransactionTime"] = int(time()) - 3600
        database["lastAccountStatement"] = {}
        for i in accountsConfig:
            database["lastAccountStatement"] = {**database["lastAccountStatement"], **{i["accountName"]: int(time()) - 3600}}
        print("First run, saving the time and Aborting.")

    else:
        if testInternentConnection():
            if (int(time()) - database["lastTransactionTime"] > LAST_TRANSACTION_TIMEOUT):
                if api.testConnection():
                    
                    converted = []
                    for index, account in enumerate(accountsConfig):
                        
                        lastAccountStatement = database["lastAccountStatement"][account["accountName"]]
                        now = int(time())
                        database["lastAccountStatement"] = {**database["lastAccountStatement"], account["accountName"]: now}

                        transactions = monobank.getStatement(account["monoID"], lastAccountStatement, now)
                        database["lastTransactionTime"] = int(time())

                        details = {}
                        if account["tags"] != []:
                            details["tags"] = account["tags"]
                        if account["budgetID"] != -1:
                            details["budget_id"] = account["budgetID"]
                        if account["categoryID"] != -1:
                            details["category_id"] = account["categoryID"]

                        for i in transactions:
                            converted.append(monoToFireflyiiiTransaction(i, account["fireflyAccountID"], details))

                        while database["lastTransactionTime"] + LAST_TRANSACTION_TIMEOUT > int(time()) and index + 1 != len(accountsConfig): sleep(1)

                    print("Transactions to be imported: ", converted)
                    for i in converted:
                        api.addTransaction([i])

                else:
                    print("Could not connect to a Firefly API; Aborting.")
        
            else:
                print("Last transaction was less than a specified timeout; Aborting.")
        else:
            print("No internet connection; Aborting.")

    database.close()