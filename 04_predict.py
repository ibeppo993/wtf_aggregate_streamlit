# https://facebook.github.io/prophet/docs/quick_start.html
import pandas as pd
import psycopg2 as pg
import sqlite3, json, time, os, psycopg2, time
from prophet import Prophet
from sqlalchemy import create_engine
import ast
import matplotlib.pyplot as plt

import toml
data_toml = toml.load("config.toml")

site_url = data_toml['site_url']
n_keywords = data_toml['n_keywords']
site = data_toml['site_url']
host = data_toml['host']
database = data_toml['database']
user = data_toml['user']
password = data_toml['password']
port= data_toml['port']
postgre_complete_url = data_toml['postgre_complete_url']
range_forecast = data_toml['range_forecast']
week_in_year = data_toml['week_in_year']
accurancy = data_toml['accurancy']


engine = create_engine(postgre_complete_url)
df = pd.read_sql_query(f"SELECT * FROM wtforecast WHERE site = '{site_url}' AND gt_accuracy <= {accurancy}",con=engine)
#print(df)

data_for_prophet = df[['keyword', 'gt_dates']].copy()
data_for_prophet = data_for_prophet.dropna()

#print(data_for_prophet)
#print(data_for_prophet.info())

for index, row in data_for_prophet.iterrows():
    #print(row['keyword'], row['gt_dates'])
    #print(row['keyword'])
    keyword = str(row['keyword'])
    #print(f'--------------------------------{keyword}')
    #print(type(row['gt_dates']))
    if row['gt_dates'] == None:
        pass
    else:
        #print(type(row['gt_dates']))

        df_dit = pd.DataFrame.from_dict(row['gt_dates'], orient='columns')
        #df_dit = pd.to_datetime(df_dit['gt_dates']).dt.strftime('%Y-%m-%d')
        df_dit['date'] = pd.to_datetime(df_dit['date'], unit='ms')
        print(df_dit)
        #print(df_dit.info())

        df_dit.columns = ['ds', 'y']
        m = Prophet(weekly_seasonality=True)
        m.fit(df_dit)
        future = m.make_future_dataframe(periods=range_forecast, freq='W')
        future.tail()
        forecast = m.predict(future)
        forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
        #pd.set_option("display.max_rows", None, "display.max_columns", None)
        #print(forecast)
        #with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #    print(forecast)
        #print(type(forecast))

        df_toprint = forecast[['ds', 'yhat']]
        df_toprint.columns = ['date', row['keyword']]
        #print(df_toprint)

        #calcolo Trebds futuri ultimo anno da 1 a 100
        #print(data)
        data_forecast_1_100 = df_toprint[-week_in_year:]
        print(data_forecast_1_100)
        a, b = 0, 100
        x, y = data_forecast_1_100[f'{keyword}'].min(), data_forecast_1_100[f'{keyword}'].max()
        data_forecast_1_100['SIZE'] = (data_forecast_1_100[f'{keyword}'] - x) / (y - x) * (b - a) + a
        data_forecast_1_100.drop([f'{keyword}'], axis=1, inplace=True)
        data_forecast_1_100.rename(columns={'SIZE':f'{keyword}'}, inplace=True)
        print(data_forecast_1_100)
        last_forecast = data_forecast_1_100[f'{keyword}'].tolist()
        #print(last_forecast)
        last_n = last_forecast[-range_forecast:]
        max_forecast = max(last_n)
        print(f"----------------------------{max_forecast}")
        #print(type(max_forecast))
        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port= port)
        cur = conn.cursor()
        cur.execute(f"UPDATE wtforecast SET last_forecast = {max_forecast} WHERE site = %s AND keyword = %s;", (site_url, keyword,))
        conn.commit()
        conn.close()


        dict_to_sql = df_toprint.to_json(orient = 'records')
        #print(dict_to_sql)

        #fig1 = m.plot(forecast)
        #plt.show()

        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port= port)
        cur = conn.cursor()
        cur.execute(f"UPDATE wtforecast SET forecast_dates = '{dict_to_sql}' WHERE site = %s AND keyword = %s;", (site_url, keyword,))
        conn.commit()
        conn.close()
        #time.sleep(5)

        #print(df_toprint)

'''

while True:
    timestr = time.strftime('%Y%m%d-%H')
    select_keyword()
    print(f'keyword ------- {keyword}')
    
    df_filtered = df.loc[df['Week'] == f'{keyword}']
    #print(df_filtered)
    df_filtered = df_filtered.T
    #print(df_filtered)
    df_filtered = df_filtered.reset_index()

    new_header = df_filtered.iloc[0]
    df_filtered = df_filtered[1:]
    df_filtered.columns = new_header

    df_filtered.columns = ['ds', 'y']
    #print(type(df_filtered))
    #print(df_filtered.info())
    #print(df_filtered)

    m = Prophet(weekly_seasonality=True)
    m.fit(df_filtered)

    future = m.make_future_dataframe(periods=8, freq='W')
    future.tail()
    forecast = m.predict(future)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    #pd.set_option("display.max_rows", None, "display.max_columns", None)
    #print(forecast)
    #with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #    print(forecast)
    #print(type(forecast))

    df_toprint = forecast[['ds', 'yhat']]
    #print(df_toprint)

    #fig1 = m.plot(forecast)
    #plt.show()

    
    if os.path.isfile(f'output_data/10_trend_forecast_{timestr}.csv'):
        #print('##########################################################file exist1')
        df_toprint.columns = ['week', f'{keyword}']
        #df_toprint.set_index('week')
        #print(df_toprint.info())

        #print('##########################################################file exist2')
        df_to_concat = pd.read_csv(f'output_data/10_trend_forecast_{timestr}.csv', sep='\t', decimal=",")#, index_col='week')
        #df_to_concat.set_index('week')
        df_to_concat['week'] = pd.to_datetime(df_to_concat['week'])
        #print(df_to_concat.info())
        #print(df_to_concat)

        #result = pd.concat([df_to_concat, df_toprint], axis=1, )
        result = pd.DataFrame.merge(df_toprint,df_to_concat,on='week')
        #print(result)
        
        result.to_csv(f'output_data/10_trend_forecast_{timestr}.csv', sep='\t', index=False, decimal=",")

    else:
        #print ("File not exist")
        df_toprint.columns = ['week', f'{keyword}']
        df_toprint.set_index('week')
        
        df_toprint.to_csv(f'output_data/10_trend_forecast_{timestr}.csv', sep='\t', index=False, decimal=",")

'''