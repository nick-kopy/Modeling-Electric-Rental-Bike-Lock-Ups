## Project Overview
A predictive model based analysis of electric rental bikes and how far away from any given docking station people are locking them up.

This study found that select measurements (traffic, time of day, trip time, rideshare membership, city, and whether or not a bike started at a station) all have a small but measurable impact on how far an electric bike is parked from the nearest station. There are also some places where riders disproportionately park near but not *direct at* the docking station and these places are worth investigating.

>Check out the five minute [slide]() version of this repo!

## The story
Electric bikes are an amazing inovation that bring access and much more range to riders. They're a welcomem addition to rental programs already known for their [benefits](https://www.outsideonline.com/2136406/do-bike-share-systems-actually-work) on metropolitan areas.

For a regular bike rental, a bike is considered returned once it is back in a slot at a station. Electric bikes (for many reasons) have changed the game, and they can be locked anywhere in town there's a bike rack. Obviously it’s better if people leave them at stations for charging and security, so there is a cost. And companies know this: they have started included insentives like small discounts for returning a rental all the way to the station.

But the truth is electric bikes are still relatively new, and rentals even more so. The market is [developing](https://www.lyft.com/bikes/bay-wheels/service-log) and we still have so much to learn. What can we discover from the data on where bikes are dismounted?

## Data Prep and Cleaning

#### Data sources
This data comes from public sources:

The San Francisco Bay Wheels bike share [data](https://s3.amazonaws.com/baywheels-data/index.html)
- 13 columns, 300k rows (2 months)
The Chicago Divvy bike share [data](https://divvy-tripdata.s3.amazonaws.com/index.html)
- 13 columns, 648k rows (2 months)
National Oceanic and Atmospheric Administration's Global Surface Summary of Day [data](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc%3AC00516/html#)
- 28 columns, 365 rows (one per calendar day)
San Francisco Municipal Transportation Agency's Taxi Trips Durig Covid [data](https://www.sfmta.com/reports/taxi-trips-during-covid-19)
- 1 column, 383 rows (one per day since COVID began), proxy for amount of traffic on the road
Chicago Transit Authority's Daily Boarding Totals
- 5 columns, 7000 rows

Some files may need to be unzipped, which is not shown in this notebook. NOAA's data comes with a separate file for each weather station. The code for each specific station can be found with their search tools online.


#### Preparation and cleaning
We'll combine all of our data together and engineer a few extra features so we can both model our data but also dig in and explore it. Particularly import is our target feature: a bike's distance from the nearest station when it's parked. Most of our analyses and our model will center around this metric.

>For a more complete look at the code and statistics used, check out the model file.


## Exploratory Data Analysis
Let's look at the data in different ways and see if we can glean any insights, especially from our target feature.

Again note that we are ONLY looking at rentals of electric bikes.

First some descriptive statistics:
- 69% of electric bike rides ended at a docking station
- The mean distance to a station for undocked rides was 412 meters.
- San Francisco had a higher proportion (40%) of undocked rides than Chicago (24%)
Among undocked bikes
- In San Francisco 38% were within 200 meters of a docking station (about a 1 minute walk)
- In Chicago 35% of rides ending within 200 meters of a station