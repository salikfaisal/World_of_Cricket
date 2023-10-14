# World_of_Cricket

This repository utilizes the [Elo System](https://en.wikipedia.org/wiki/Elo_rating_system) to analyze [National Cricket Teams](https://github.com/salikfaisal/World_of_Cricket/blob/main/ODI_Elo_Ratings.csv) and [Grounds](https://github.com/salikfaisal/World_of_Cricket/blob/main/ODI%20Grounds.csv), as well as forecasting the [2023 ICC Cricket World Cup](https://github.com/salikfaisal/World_of_Cricket/blob/main/2023_World_Cup_Expected_Results.csv).

## Producing Elo Ratings

These steps outline the process for calculating [Elo Ratings](https://github.com/salikfaisal/World_of_Cricket/blob/main/ODI_Elo_Ratings.csv) for each National Cricket Team and adjustments to their ratings based on whether they batted first in a given match.

1. [Determine Starting Elo Ratings](https://github.com/salikfaisal/World_of_Cricket/blob/main/Getting_Starting_Ratings.py): This involves running thousands of simulations to find the best starting Elo ratings for each team. Two key measures are used for determining the best starting ratings:
   A) Minimizing changes in ratings over time
   B) Minimizing the difference between Elo Rankings at a given time and final standings at major ICC tournaments.

2. Determine Advantages for Teams Based on Whether They Bat First: This is achieved by analyzing every completed ODI match on each cricket ground and quantifying the advantage or disadvantage for the side batting first in matches at the cricket ground.

3. [Determine Final Adjusted Ratings](https://github.com/salikfaisal/World_of_Cricket/blob/main/Getting_Current_Ratings.py): This final step involves iterating over each historical match and updating rankings based on expected win percentage and margin of victory. The expected win percentage is determined by the difference in Elo Ratings between the teams, adjusted for ground batting order effects and team batting order adjustments to Elo ratings.

## Projecting the ICC World Cup

The ICC World Cup projections are determined using the [Monte Carlo Method](https://en.wikipedia.org/wiki/Monte_Carlo_method). Each match is simulated based on the teams' Elo ratings and adjustments, which consider the team batting first, the data related to participating teams, and the cricket ground's data.

## Analysis:

[2023 ICC World Cup Projections](https://github.com/salikfaisal/World_of_Cricket/blob/main/2023_World_Cup_Expected_Results.csv)
<br>
[ODI Elo Ratings](https://github.com/salikfaisal/World_of_Cricket/blob/main/ODI_Elo_Ratings.csv)
<br>
[Cricket Ground Data](https://github.com/salikfaisal/World_of_Cricket/blob/main/ODI%20Grounds.csv)
