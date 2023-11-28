# [Fireflyiii](https://www.firefly-iii.org/) transaction importer for [monobank](https://www.monobank.ua/)

## Usage:
1. Install python modules. `pip install -r requirements`

2. Configure env variables. This can be done manually, or by running `export $(cat .env | xargs)`.

`.env:`
```
FIREFLYIII_INSTANCE="http://firefly.yourdomain.com:1234/" - location of your Fireflyiii instance
FIREFLYIII_TOKEN="your-fireflyiii-token" - personal token for Fireflyiii
MONOBANK_TOKEN="your-monobank-token" - personal token for monobank
TIMEZONE="Europe/Kyiv" - timezone
```

To get Fireflyiii token, follow [these steps](https://docs.firefly-iii.org/firefly-iii/api/#personal-access-token). Get monobank personal API token [here](https://api.monobank.ua/).

3. Configure import settings.

`config.yaml:`
```
MonobankAccounts:
  -
    - accountName: "black" - arbitrary name (str)
    - monoID: "yourId" - monobank account id (str)
    - fireflyAccountID: -1 - fireflyiii acount id (int)
    - tags: [] - tags to be added to the transaction, empty if none ([str, str])
    - budgetID: -1 - budget id to be added to the transaction, -1 if none (int)
    - categoryID: -1 - category id to be added to the transaction, -1 if none (int)
  -
    - accountName: "white"
    - monoID: "yourId"
    - fireflyAccountID: -1
    - tags: []
    - budgetID: -1
    - categoryID: -1
```

To get monobank account id, run `curl -H 'X-Token: your-monobank-api-token' https://api.monobank.ua/personal/client-info`. Your available accounts [will be](https://api.monobank.ua/docs/#tag/Kliyentski-personalni-dani/paths/~1personal~1client-info/get) in `accounts` array.

To get id of account / budget / category in Fireflyiii, go to its edit page and look for the number in the address bar. (e.g. `http://fireflyinstance.xyz/accounts/edit/9` - id of this account is 9).

4. Run `python main.py`

## [Docker container](https://github.com/mariko357/fireflyiii-monobank-importer-docker)