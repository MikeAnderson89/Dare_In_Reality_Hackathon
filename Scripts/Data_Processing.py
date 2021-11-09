import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def DataProcessing(csv_url):
    df = pd.read_csv(csv_url)
    df.columns = [x.title().strip() for x in df.columns]
    df = df.dropna(subset=['S1'])

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

    return df
