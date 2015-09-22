import requests
import simplejson as json
import pandas as pd

stock_json_file = requests.get('https://www.quandl.com/api/v1/datasets/WIKI/AAPL.json?api_key=xDbkv2XztyErqMSjJ8He')
stock_dict = stock_json_file.json()
df = pd.DataFrame(stock_dict['data'])
df.columns=stock_dict['column_names']
df['Date'] = pd.to_datetime(df['Date'])
print(stock_dict['data'][0])