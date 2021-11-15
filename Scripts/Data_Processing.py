import pandas as pd
import numpy as np
from datetime import datetime, timedelta

pd.set_option('display.max_columns', None)


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

    wdf['TIME_UTC_STR'] = pd.to_datetime(wdf['TIME_UTC_STR'], dayfirst=True)
    wdf['TIME_UTC_MINUTE'] = [x.minute for x in wdf['TIME_UTC_STR']]

    num_cols = ['AIR_TEMP', 'TRACK_TEMP', 'HUMIDITY', 'PRESSURE', 'WIND_SPEED', 'RAIN']
    wdf['RAIN'] = [x.replace(',', '.') for x in wdf['RAIN']]

    for col in num_cols:
        wdf[col] = wdf[col].str.replace(',', '').replace('.', '').astype(float)

    wdf.dtypes

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
    df['Lap_Time'] = df['Lap_Time'].astype(float)

    return df
