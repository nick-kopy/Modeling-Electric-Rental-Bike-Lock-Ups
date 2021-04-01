# This file contains all the necessary functions for model.ipynb to run
# It mostly collects, cleans, and presents data

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic

import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

def grab_data(url):
    '''Grabs data from URL and cleans it up for use in EDA.

    Output still needs a touch up before modeling however.
    '''
    # start with data we want
    df = pd.read_csv(url, usecols=['ended_at', 'started_at', 'start_station_id', 'rideable_type',
                                   'end_station_id', 'end_lat', 'end_lng', 'member_casual'])

    # drop rows w/o lat/long coordinates
    df = df[df['end_lat'].notna()]

    # drop non-electric bikes
    df = df[df['rideable_type'] == 'electric_bike']
    df.reset_index(drop=True)
    df = df.drop(columns='rideable_type')

    # grab date (for matching up with other data)
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    df['date'] = pd.to_datetime(df['ended_at'].dt.date)

    # add a few time related features
    # daylight savings makes a few negative trip times, a quick approximate fix is okay
    df['hour'] = df['ended_at'].dt.hour

    df['started_at'] = pd.to_datetime(df['started_at'])
    df['trip_time'] = abs((df['ended_at'] - df['started_at']).dt.total_seconds())

    df = df.drop(columns=['ended_at', 'started_at'])

    # binary encoding for a few categorical features
    df['start_station_id'] = df['start_station_id'].apply(lambda x: 0 if pd.isna(x) else 1)
    df['member_casual'] = df['member_casual'].apply(lambda x: 0 if x=='casual' else 1)

    return df

def grab_geo(city):
    '''Returns dataframe with lat/long of each docking station in a given city.
    '''

    # Grab full data from desired city
    # Stations do change over time so it's better to look at the full time span
    if city == 'SF':
        geo1 = pd.read_csv('data/SF/202010-baywheels-tripdata.csv', usecols=['end_station_id', 'end_lat', 'end_lng'])
        geo2 = pd.read_csv('data/SF/202011-baywheels-tripdata.csv', usecols=['end_station_id', 'end_lat', 'end_lng'])
    elif city == 'CH':
        geo1 = pd.read_csv('data/CH/202010-divvy-tripdata.csv', usecols=['end_station_id', 'end_lat', 'end_lng'])
        geo2 = pd.read_csv('data/CH/202011-divvy-tripdata.csv', usecols=['end_station_id', 'end_lat', 'end_lng'])
    else:
        return None

    # Reduce to one row per station and associated lat/long
    geo = pd.concat([geo1, geo2], ignore_index=True).groupby(by='end_station_id').agg(np.mean)

    # Rows without a station name also end up as a row, don't need it
    geo = geo[geo['end_lat'].notna()]

    return geo

def station_dist(row, input_geo):
    '''Wrapper function that returns the distance between an input coordinate set
    and a row coordinate set.

    Applied to the station coordinate dataframe, can be used to make a new column
    of distances from a specific point in space.
    '''

    # geopy uses lat/long specifically in a tuple to calculate distance
    stat_geo = tuple([val for idx, val in row.items()])

    return geodesic(stat_geo, input_geo).km

def nearest_station(row, station_geo):
    '''Returns the distance to the nearest docking station.

    Should be applied to a dataframe and the output will be two new columns.

    Arguments:
        row: row of a pandas dataframe, typically automatically pass when using df.apply(func)
        station_geo: df, output of grab_geo() function

    Returns:
        tuple: the distance to the nearest docking station in meters (float),
        and that station's name (str or int)
    '''

    # simple progress tracker because this takes a long time
    if row.name%2000 == 0:
        print(round(row.name/254000, 3))

    # this function expects lat/long in a specific column position
    # if df is changed beforehand, indexing this variable will mess up
    row_vals = [val for idx, val in row.items()]

    # if statement to catch rows where bikes are already at a station
    if not pd.isna(row_vals[1]):
        return 0, row_vals[1]

    # get row lat/long
    row_geo = tuple(row_vals[2:4])

    # get distance to each station
    s_geo = station_geo.copy()
    s_geo['dist'] = s_geo.apply(station_dist, args=[row_geo], axis=1)

    # grab the minimum distance and station name
    min_id = s_geo['dist'].idxmin()
    min_dist = s_geo.at[min_id, 'dist']*1000

    # can modify to only return distance if desired
    return min_dist, min_id

def grab_weather(city):
    '''Returns dataframe of date, temperature, and windspeed.

    Other weather measurements are present but not used.
    Precipitation in particular should have been useful, but is
    measured at 0 every single day for both cities.

    San Jose is approximated to have the same weather as San Francisco.
    '''

    # Grab full data from desired city
    if city == 'CH':
        url = 'data/CH/99733899999.csv'
    elif city == 'SF':
        url = 'data/SF/99401699999.csv'
    else:
        return None

    # only grab the columns we want
    dfw = pd.read_csv(url, usecols=['DATE', 'TEMP', 'WDSP'])

    # Make our date the datetime datatype for merging later
    dfw['DATE'] = pd.to_datetime(dfw['DATE'])

    return dfw

def grab_traffic(city):
    '''Returns dataframe with traffic measurement.

    Data for Chicago and San Francisco are different and not directly comparable.
    They do both however measure the volume of people using transportation (traffic),
    and are scaled during the modeling process so it shouldn't be an issue.

    San Jose is approximated to have the same traffic as San Francisco.
    '''

    # Grab Chicago's traffic data
    if city == 'CH':
        dft = pd.read_csv('data/CH/CTA_-_Ridership_-_Daily_Boarding_Totals.csv',
                         usecols=['service_date', 'total_rides'])

        # Make our date the datetime datatype for merging later
        dft['service_date'] = pd.to_datetime(dft['service_date'])

        return dft

    # Grab San Francisco's traffic data which needs a touch more cleaning
    elif city == 'SF':
        dft = pd.read_csv('data/SF/TaxiTable.csv')

        dft['Day of Date'] = pd.to_datetime(dft['Day of Date'])
        dft['Number of Records'] = dft['Number of Records'].replace(',', '', regex=True).astype('int32')
        dft = dft.rename(columns={'Number of Records':'taxi_trips'})

        return dft

    else:
        return None

def get_city(row):
    '''Returns the name of a city for a given row.
    '''
    # if df is changed beforehand indexing this variable will mess up
    row_vals = [val for idx, val in row.items()]
    stat = row_vals[12]

    # looks at station id to figure out which city a row is from
    if type(stat) == float:
        return 'CH'
    elif stat.find('SF') > -1:
        return 'SF'
    elif stat.find('SJ') > -1:
        return 'SJ'
    elif stat.find('San Jose Depot') > -1:
        return 'SJ'
    else:
        return 'unknown'

def rmse(true, predicted):
    '''Quick root mean squared error function
    '''
    mean_squared = mean_squared_error(true, predicted)
    return np.sqrt(mean_squared)

def cross_val(X_train, y_train, k):
    '''Simple CV loop that returns average rmse across k folds.

    Useful in getting a more accurate model training error that's less dependent
    on the train-test-split.
    '''
    rmse_arr = []
    kf = KFold(n_splits=k)

    # Each loop takes a different fold, calculates the error, and saves it in a list
    for train_index, test_index in kf.split(X_train):

        # Make within fold test train splits
        Kx_train, Kx_test = X_train[train_index], X_train[test_index]
        Ky_train, Ky_test = y_train.iloc[train_index], y_train.iloc[test_index]

        # Train the model and make a prediction
        mod = sm.OLS(Ky_train, Kx_train, hasconst=True).fit()
        train_predicted = mod.predict(Kx_test)

        # Calculate the error
        cur_rmse = rmse(Ky_test, train_predicted)

        # Add it to the error list
        rmse_arr.append(cur_rmse)

    # The average of the error list is a good estimate of the training error
    return np.average(rmse_arr)