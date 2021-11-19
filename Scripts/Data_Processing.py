import pandas as pd
import numpy as np
from datetime import datetime, timedelta



def DataProcessing(csv_url):
    df = pd.read_csv(csv_url)
    df.columns = [x.title().strip() for x in df.columns]
    df = df.dropna(subset=['S1'])

    drop_cols = ['S1_Large', 'S2_Large', 'S3_Large']

    df['Event'].value_counts()

    for index, row in df.iterrows():
        number = str(row['Number'])
        location_number = row['Location'][-1:]
        if row['Event'] == 'Free Practice 1':
            event = 'FP1'
        elif row['Event'] == 'Free Practice 2':
            event = 'FP2'
        elif row['Event'] == 'Free Practice 3':
            event = 'FP3'
        elif row['Event'] == 'Qualifying Group 1':
            event = 'QG1'
        elif row['Event'] == 'Qualifying Group 2':
            event = 'QG2'
        elif row['Event'] == 'Qualifying Group 3':
            event = 'QG3'
        elif row['Event'] == 'Qualifying Group 4':
            event = 'QG4'
        df.at[index, 'Trial_ID'] = event + '-' + location_number + '-' + number

    for x in df['Trial_ID'].unique():
        temp = df.loc[df['Trial_ID'] == x]

        lap_number_previous = 1
        trial_identifier = 1

        for index, row in temp.iterrows():
            if row['Lap_Number'] >= lap_number_previous:
                df.at[index, 'Trial_Number'] = trial_identifier
                lap_number_previous += 1
            elif row['Lap_Number'] < lap_number_previous:
                trial_identifier += 1
                df.at[index, 'Trial_Number'] = trial_identifier
                lap_number_previous = 1

    df['Trial_ID_2'] = df['Trial_ID'] + '-' + df['Trial_Number'].astype(int).astype(str)

    def TimeConversion(x):
        x = str(x)
        if x != 'nan':
            try:
                y = datetime.strptime(x, '%M:%S.%f').time()
            except ValueError:
                try:
                    y = datetime.strptime(x, '%S.%f').time()
                except ValueError:
                    try:
                        y = datetime.strptime(x, '%S').time()
                    except ValueError:
                        y = datetime.strptime('0', '%S').time()
        if x == 'nan':
            y = datetime.strptime('0', '%S').time()
        z = timedelta(minutes=y.minute, seconds=y.second, microseconds=y.microsecond)
        return z

    time_cols = [
        'S1',
        'S2',
        'S3',
        'Elapsed',
        'Hour',
        'S1_Large',
        'S2_Large',
        'S3_Large',
        'Pit_Time',
    ]

    daytime_cols = ['Hour']

    for x in time_cols:
        df[x] = df[x].apply(TimeConversion)

    for x in df['Trial_ID_2']:
        temp = df.loc[df['Trial_ID_2'] == x]
        laps = len(temp)
        pit_time = timedelta(0)
        for index, row in temp.iterrows():
            if ~pd.isna(row['Pit_Time']):
                pit_amount = row['Pit_Time']
                pit_time += pit_amount

        df.loc[df['Trial_ID_2'] == x, 'Pit_Time'] = pit_time / laps

    df = df.drop(columns=[
    'S1_Large',
    'S2_Large',
    'S3_Large',
    'Trial_Number',
    'Trial_ID',
    'Number',
    'Driver_Number',
    'Crossing_Finish_Line_In_Pit'
    ])

    def ConvertToSeconds(x):
        y = x.total_seconds()
        return y

    df['S1'] = df['S1'].apply(ConvertToSeconds)
    df['S2'] = df['S2'].apply(ConvertToSeconds)
    df['S3'] = df['S3'].apply(ConvertToSeconds)
    df['Pit_Time'] = df['Pit_Time'].apply(ConvertToSeconds)
    df['Elapsed'] = df['Elapsed'].apply(ConvertToSeconds)

    df['Time_Minutes'] = [(x.total_seconds() / 60) for x in df['Hour']]

    wdf_train = pd.read_csv('../Data/train_weather.csv')
    wdf_test = pd.read_csv('../Data/test_weather.csv')
    wdf_test = wdf_test.rename(columns={'EVENTS': 'EVENT'})
    wdf_test['RAIN'] = wdf_test['RAIN'].astype(str)

    wdf = pd.concat([wdf_train, wdf_test])

    #split into location due to different number formats
    train_weather_l1 = wdf[wdf['LOCATION'].isin(['Location 1','Location 2','Location 3','Location 4'])]
    train_weather_l1['AIR_TEMP'] = train_weather_l1['AIR_TEMP'] .str.replace(',','.')
    train_weather_l1['AIR_TEMP'] = pd.to_numeric(train_weather_l1['AIR_TEMP'])
    train_weather_l1['TRACK_TEMP'] = train_weather_l1['TRACK_TEMP'] .str.replace(',','.')
    train_weather_l1['TRACK_TEMP'] = pd.to_numeric(train_weather_l1['TRACK_TEMP'])
    train_weather_l1['HUMIDITY'] = train_weather_l1['HUMIDITY'] .str.replace(',','.')
    train_weather_l1['HUMIDITY'] = pd.to_numeric(train_weather_l1['HUMIDITY'])
    train_weather_l1['PRESSURE'] = train_weather_l1['PRESSURE'] .str.replace(',','.')
    train_weather_l1['PRESSURE'] = pd.to_numeric(train_weather_l1['PRESSURE'])
    train_weather_l1['WIND_SPEED'] = train_weather_l1['WIND_SPEED'] .str.replace(',','.')
    train_weather_l1['WIND_SPEED'] = pd.to_numeric(train_weather_l1['WIND_SPEED'])
    train_weather_l1['RAIN'] = train_weather_l1['RAIN'].str.replace(',', '.')
    train_weather_l1['RAIN'] = pd.to_numeric(train_weather_l1['RAIN'])



    train_weather_l2 = wdf[wdf['LOCATION'].isin(['Location 5','Location 6','Location 7', 'Location 8'])]
    train_weather_l2['AIR_TEMP'] = train_weather_l2['AIR_TEMP'] .str.replace(',','')
    train_weather_l2['AIR_TEMP'] = pd.to_numeric(train_weather_l2['AIR_TEMP'], errors='coerce')
    conditions = [
        (train_weather_l2['AIR_TEMP'] > 100)  & (train_weather_l2['AIR_TEMP'] < 1000),
        (train_weather_l2['AIR_TEMP'] > 1000) & (train_weather_l2['AIR_TEMP'] < 10000),
        (train_weather_l2['AIR_TEMP'] > 10000) & (train_weather_l2['AIR_TEMP'] < 100000),
        (train_weather_l2['AIR_TEMP'] > 100000)]
    choices = [train_weather_l2['AIR_TEMP']/10,train_weather_l2['AIR_TEMP']/100,
               train_weather_l2['AIR_TEMP']/1000,train_weather_l2['AIR_TEMP']/10000]
    train_weather_l2['AIR_TEMP'] = np.select(conditions, choices, default=20)

    train_weather_l2['TRACK_TEMP'] = train_weather_l2['TRACK_TEMP'] .str.replace(',','.')
    train_weather_l2['TRACK_TEMP'] = pd.to_numeric(train_weather_l2['TRACK_TEMP'], errors='coerce')

    train_weather_l2['HUMIDITY'] = train_weather_l2['HUMIDITY'] .str.replace(',','.')
    train_weather_l2['HUMIDITY'] = pd.to_numeric(train_weather_l2['HUMIDITY'], errors='coerce')



    train_weather_l2['PRESSURE'] = train_weather_l2['PRESSURE'] .str.replace(',','')
    train_weather_l2['PRESSURE'] = pd.to_numeric(train_weather_l2['PRESSURE'], errors='coerce')
    conditions = [
        (train_weather_l2['PRESSURE'] > 10000) & (train_weather_l2['PRESSURE'] < 20000),
        (train_weather_l2['PRESSURE'] > 20000) & (train_weather_l2['PRESSURE'] < 200000),
        (train_weather_l2['PRESSURE'] > 200000)]

    choices = [train_weather_l2['PRESSURE']/10,
               train_weather_l2['PRESSURE']/100,
               train_weather_l2['PRESSURE']/1000]
    train_weather_l2['PRESSURE'] = np.select(conditions, choices, default=1000)


    train_weather_l2['WIND_SPEED'] = train_weather_l2['WIND_SPEED'] .str.replace(',','')
    train_weather_l2['WIND_SPEED'] = pd.to_numeric(train_weather_l2['WIND_SPEED'], errors='coerce')
    conditions = [
        (train_weather_l2['WIND_SPEED'] > 10) & (train_weather_l2['WIND_SPEED'] < 100),
        (train_weather_l2['WIND_SPEED'] > 100) & (train_weather_l2['WIND_SPEED'] < 1000),
        (train_weather_l2['WIND_SPEED'] > 1000) & (train_weather_l2['WIND_SPEED'] < 10000),
        (train_weather_l2['WIND_SPEED'] > 10000) & (train_weather_l2['WIND_SPEED'] < 100000),
        (train_weather_l2['WIND_SPEED'] > 100000)]

    choices = [train_weather_l2['WIND_SPEED']/10,
               train_weather_l2['WIND_SPEED']/100,
               train_weather_l2['WIND_SPEED']/1000,
               train_weather_l2['WIND_SPEED']/10000,
               train_weather_l2['WIND_SPEED']/100000,
               ]
    train_weather_l2['WIND_SPEED'] = np.select(conditions, choices, default=1)
    train_weather_l2['RAIN'] = train_weather_l2['RAIN'].str.replace(',', '.')
    train_weather_l2['RAIN'] = pd.to_numeric(train_weather_l2['RAIN'])

    wdf = pd.concat([train_weather_l1,train_weather_l2])

    wdf['TIME_UTC_STR'] = pd.to_datetime(wdf['TIME_UTC_STR'], dayfirst=True)
    wdf['TIME_UTC_MINUTE'] = [x.minute for x in wdf['TIME_UTC_STR']]

    num_cols = ['AIR_TEMP', 'TRACK_TEMP', 'HUMIDITY', 'PRESSURE', 'WIND_SPEED', 'RAIN']

    for index, row in df.iterrows():
        location = row['Location']
        event = row['Event']
        time = row['Time_Minutes']

        try:
            weather = wdf.loc[(wdf['LOCATION'] == location) & (wdf['EVENT'] == event) & (wdf['TIME_UTC_MINUTE'] <= time) & (time < (wdf['TIME_UTC_MINUTE'] + 1))]
            weather = weather.iloc[0]
            df.at[index, 'Air_Temp'] = weather['AIR_TEMP']
            df.at[index, 'Track_Temp'] = weather['TRACK_TEMP']
            df.at[index, 'Humidity'] = weather['HUMIDITY']
            df.at[index, 'Pressure'] = weather['PRESSURE']
            df.at[index, 'Wind_Speed'] = weather['WIND_SPEED']
            df.at[index, 'Wind_Direction'] = weather['WIND_DIRECTION']
            df.at[index, 'Rain'] = weather['RAIN']
        except IndexError:
            weather = wdf.loc[(wdf['LOCATION'] == location) & (wdf['EVENT'] == event)]
            if not weather.empty:
                df.at[index, 'Air_Temp'] = weather['AIR_TEMP'].mean()
                df.at[index, 'Track_Temp'] = weather['TRACK_TEMP'].mean()
                df.at[index, 'Humidity'] = weather['HUMIDITY'].mean()
                df.at[index, 'Pressure'] = weather['PRESSURE'].mean()
                df.at[index, 'Wind_Speed'] = weather['WIND_SPEED'].mean()
                df.at[index, 'Wind_Direction'] = weather['WIND_DIRECTION'].mean()
                df.at[index, 'Rain'] = weather['RAIN'].mode()[0]
            else:
                weather = wdf.loc[wdf['LOCATION'] == location]
                df.at[index, 'Air_Temp'] = weather['AIR_TEMP'].mean()
                df.at[index, 'Track_Temp'] = weather['TRACK_TEMP'].mean()
                df.at[index, 'Humidity'] = weather['HUMIDITY'].mean()
                df.at[index, 'Pressure'] = weather['PRESSURE'].mean()
                df.at[index, 'Wind_Speed'] = weather['WIND_SPEED'].mean()
                df.at[index, 'Wind_Direction'] = weather['WIND_DIRECTION'].mean()
                df.at[index, 'Rain'] = weather['RAIN'].mode()[0]


    df['Power'] = df['Power'].fillna(df['Power'].mode()[0])
    df['Kph'] = df['Kph'].fillna(df['Kph'].mean())
    df = df.drop(columns=['Group', 'Hour', 'Trial_ID_2', 'Time_Minutes'])

    return df
