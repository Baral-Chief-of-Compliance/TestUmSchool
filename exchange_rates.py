import requests,os
from dotenv import load_dotenv


load_dotenv()

FIXER_KEY = os.getenv('FIXER_KEY')


def get_exchange_rates(currency):
    url = f"https://api.apilayer.com/fixer/convert?to=RUB&from={currency}&amount=1"

    response = requests.request("GET", url, headers={
        "apikey": FIXER_KEY
    }, data={})

    result = response.json()

    return str(result['info']['rate'])