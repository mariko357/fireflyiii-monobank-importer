from monobank import Monobank
from fireflyiii import FireflyAPI
import shelve
from time import time, sleep
from datetime import datetime
import zoneinfo
import os
import yaml

LAST_TRANSACTION_TIMEOUT = 60

FIREFLYIII_INSTANCE = os.environ["FIREFLYIII_INSTANCE"]
FIREFLYIII_TOKEN = os.environ["FIREFLYIII_TOKEN"]
MONOBANK_TOKEN = os.environ["MONOBANK_TOKEN"]
TIMEZONE = os.environ["TIMEZONE"]

CURRENCIES = {
    971: "AFN",
    8: "ALL",
    12: "DZD",
    840: "USD",
    978: "EUR",
    973: "AOA",
    951: "XCD",
    952: "XOF",
    32: "ARS",
    51: "AMD",
    533: "AWG",
    36: "AUD",
    944: "AZN",
    44: "BSD",
    48: "BHD",
    50: "BDT",
    52: "BBD",
    933: "BYN",
    84: "BZD",
    72: "BWP",
    60: "BMD",
    64: "BTN",
    356: "INR",
    68: "BOB",
    984: "BOV",
    977: "BAM",
    986: "BRL",
    96: "BND",
    975: "BGN",
    108: "BIF",
    132: "CVE",
    116: "KHR",
    950: "XAF",
    124: "CAD",
    136: "KYD",
    320: "GTQ",
    324: "GNF",
    328: "GYD",
    332: "HTG",
    340: "HNL",
    344: "HKD",
    348: "HUF",
    352: "ISK",
    360: "IDR",
    364: "IRR",
    368: "IQD",
    376: "ILS",
    380: "ITL",
    388: "JMD",
    392: "JPY",
    400: "JOD",
    398: "KZT",
    404: "KES",
    408: "KPW",
    410: "KRW",
    414: "KWD",
    417: "KGS",
    418: "LAK",
    428: "LAT",
    422: "LBP",
    426: "LSL",
    710: "ZAR",
    430: "LRD",
    434: "LYD",
    756: "CHF",
    608: "MAD",
    932: "MKD",
    450: "MWK",
    458: "MYR",
    462: "MVR",
    470: "MRU",
    480: "MUR",
    934: "MZN",
    104: "MMK",
    516: "NAD",
    524: "NPR",
    528: "ANG",
    554: "NZD",
    558: "NIO",
    566: "NGN",
    578: "NOK",
    512: "OMR",
    586: "PKR",
    604: "PEN",
    608: "PHP",
    634: "QAR",
    946: "RON",
    643: "RUB",
    646: "RWF",
    882: "WST",
    930: "STN",
    941: "RSD",
    690: "SCR",
    694: "SLL",
    994: "XSU",
    706: "SOS",
    144: "LKR",
    760: "SYP",
    901: "TWD",
    972: "TJS",
    834: "TZS",
    764: "THB",
    840: "USD",
    776: "TOP",
    780: "TTD",
    788: "TND",
    949: "TRY",
    934: "TMT",
    800: "UGX",
    980: "UAH",
    784: "AED",
    826: "GBP",
    997: "USN",
    860: "UZS",
    548: "VUV",
    704: "VND",
    953: "XPF",
    504: "MAD",
    886: "YER",
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

    database.close()