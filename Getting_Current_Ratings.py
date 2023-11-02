import numpy as np
import pandas as pd
from Match_Extraction import df
import time
import statistics
import matplotlib.pyplot as plt

# gets the net run rate for a projected 50 overs score
df["Adj RR Margin"] = abs(df["Team 1 Projected 50 Overs Score"] - df["Team 2 Projected 50 Overs Score"]) / 50
# gets rid of matches with no result
df = df[df["Winner"] != 'No Result']
# finds the percentile for the 'BF Adj NRR' column
df['RR Margin Percentile'] = df["Adj RR Margin"].rank(pct=True)

# these are a list of teams to ignore
teams_to_ignore = ['ICC World XI', 'Asia XI', 'Africa XI']

# this is used to calculate the elo ratings for each ODI side over time
elo_dict = {'England': 1734, 'Australia': 1818, 'New Zealand': 1684, 'Pakistan': 1719, 'West Indies': 1748,
            'India': 1765, 'East Africa': 1165, 'Sri Lanka': 1599, 'Canada': 1422, 'Zimbabwe': 1751, 'Bangladesh': 1633,
            'South Africa': 1710, 'United Arab Emirates': 1323, 'Netherlands': 1490, 'Kenya': 1614, 'Scotland': 1466,
            'Namibia': 1349, 'Hong Kong': 1302, 'United States of America': 1352, 'Bermuda': 1409, 'Ireland': 1641,
            'Afghanistan': 1657, 'Papua New Guinea': 1226, 'Nepal': 1451, 'Oman': 1562, 'Jersey': 1415}




# in the form of {ground, city, country: [ground, city, country, 1st innings adj rr, 2nd innings adjusted rr,
#                                         total matches, bf_win, bf_lose]}
ground_stats_dict = {}
home_advantage_elo_boost = 220
start_time = time.time()
for idx, match_facts in df.iterrows():
    winner = match_facts["Winner"]
    bf = match_facts["Batting First"]
    bs = match_facts["Batting Second"]
    # doesn't change the ratings if there is no result
    if winner == 'No Result':
        continue
    # doesn't change the ratings if matches involve World or Continental XIs
    elif bf in teams_to_ignore:
        continue
    elif bs in teams_to_ignore:
        continue
    bf_pre_match_elo = elo_dict[bf]
    bs_pre_match_elo = elo_dict[bs]
    # assigns home advantage (if there is any)
    host_country = match_facts["Country"]
    ground_name = match_facts["Ground"]
    city = match_facts["City"]
    ground = ground_name + ", " + city + ", " + host_country
    if bf == host_country:
        bf_pre_match_elo += home_advantage_elo_boost
    elif bs == host_country:
        bs_pre_match_elo += home_advantage_elo_boost
    # adds the elo boost to the team batting first
    match_type = match_facts["Series Type"]
    k_factor = 20
    # changes the impact of the ratings depending on the kind of match
    # world cup matches have the most importance
    if match_type == "world-cup":
        k_factor *= 2
    # Asia Cup and ICC Champions Trophy Matches also have more weight than regular ODI matches
    elif match_type == 'asia-cup' or match_type == 'bang':
        k_factor *= 1.5
    # calculates the odds of the team batting first winning the match
    bf_win_expectancy = 1 / (10 ** ((bs_pre_match_elo - bf_pre_match_elo) / 400) + 1)
    # finds the adjusted run rate and finds the value to be used in elo points exchanges
    # 1.64 is the standard deviation of NRR for all ODI matches
    bf_adjusted_run_rate = match_facts["Team 1 Projected 50 Overs Score"] / 50
    bs_adjusted_run_rate = match_facts["Team 2 Projected 50 Overs Score"] / 50
    bf_nrr = bf_adjusted_run_rate - bs_adjusted_run_rate
    percentile = match_facts['RR Margin Percentile']
    if percentile > 0.9999999999998945:
        percentile = 0.9999999999998945
    elif percentile < 0.0000000000001055:
        percentile = 0.0000000000001055
    z_score = statistics.NormalDist().inv_cdf(percentile)
    nrr_factor = 1.3 * z_score
    nrr_margin_increase = (0.75 + (nrr_factor - 3) / 8)
    # calculates the change in rating for each time
    if winner == bf:
        bf_change_in_rating = (1 - bf_win_expectancy) * k_factor * nrr_margin_increase
    elif winner == 'Tie':
        bf_change_in_rating = (0.5 - bf_win_expectancy) * k_factor
    else:
        bf_change_in_rating = (0 - bf_win_expectancy) * k_factor * nrr_margin_increase
    # updates the elo ratings after the match
    elo_dict[bf] += bf_change_in_rating
    elo_dict[bs] -= bf_change_in_rating
    if bf == host_country:
        home_advantage_elo_boost += 0.075 * bf_change_in_rating
    elif bs == host_country:
        home_advantage_elo_boost -= 0.075 * bf_change_in_rating
    # updates the ground information
    if ground not in ground_stats_dict:
        ground_stats_dict.update({ground: [ground_name, city, host_country, 0, 0, 0, 0, 0, 0]})
    ground_stats_dict[ground][3] += 0.075 * bf_change_in_rating
    ground_total_matches = ground_stats_dict[ground][6]
    if ground_total_matches == 0:
        ground_stats_dict[ground][4] = bf_adjusted_run_rate
        ground_stats_dict[ground][5] = bs_adjusted_run_rate
    else:
        match_weight = (1 / ((ground_total_matches + 1) / 1.5))
        ground_stats_dict[ground][4] = bf_adjusted_run_rate * match_weight + ground_stats_dict[ground][4] * (1 - match_weight)
        ground_stats_dict[ground][5] = bs_adjusted_run_rate * match_weight + ground_stats_dict[ground][5] * (1 - match_weight)
    ground_stats_dict[ground][6] += 1
    if winner == bf:
        ground_stats_dict[ground][7] += 1
    else:
        ground_stats_dict[ground][8] += 1

# creates a data frame on ground statistics
ground_stats_df = pd.DataFrame(columns=["Ground Name", "City", "Country", "Batting First Elo Boost",
                                        "Adj 1st Innings Score", "Adj 2nd Innings Score", "Matches Completed",
                                        "Batting First Wins", "Batting Second Wins"],
                               data=ground_stats_dict.values())
ground_stats_df["Adj 1st Innings Score"] = ground_stats_df["Adj 1st Innings Score"] * 50
ground_stats_df["Adj 2nd Innings Score"] = ground_stats_df["Adj 2nd Innings Score"] * 50
ground_stats_df.sort_values(by='Matches Completed', ascending=False, inplace=True)
ground_stats_df["Batting First Win %"] = ground_stats_df["Batting First Wins"] / ground_stats_df["Matches Completed"]
ground_stats_df["Batting Second Win %"] = ground_stats_df["Batting Second Wins"] / ground_stats_df["Matches Completed"]
ground_stats_df.to_csv("ODI Grounds.csv", index=False, header=True)
end_time = time.time()
print("Elo Ratings Determined from Matches in", round((end_time - start_time) / 60, 2), "Minutes")

# this is an elo dictionary that updates over time as new teams enter the ODI format
time_sensitive_elo_dict = {}
# in the form of {team: batting first elo adjustment}
bat_first_elo_dict = {}
# in the form of {ground: [adj run rate, total matches]}
grounds_tilt_dict = {}
# in the form of {team: [batting heavy score, total matches]}
teams_tilt_dict = {}
# these are used to update the tilt and rating over time for a line graph
elo_line_graph_dict = {"Date": []}
bat_first_elo_line_graph = {"Date": []}
teams_tilt_line_graph = {"Date": []}
teams_of_interest = ['West Indies', 'India', 'Australia', 'Pakistan', 'Sri Lanka', 'New Zealand', 'South Africa', 'England']
for team in teams_of_interest:
    elo_line_graph_dict.update({team: []})
    bat_first_elo_line_graph.update({team: []})
    teams_tilt_line_graph.update({team: []})
home_advantage_elo_boost = 220
start_time = time.time()
for idx, match_facts in df.iterrows():
    winner = match_facts["Winner"]
    bf = match_facts["Batting First"]
    bs = match_facts["Batting Second"]
    # doesn't change the ratings if there is no result
    if winner == 'No Result':
        continue
    # doesn't change the ratings if matches involve World or Continental XIs
    elif bf in teams_to_ignore:
        continue
    elif bs in teams_to_ignore:
        continue
    date = match_facts['Date']
    bf_pre_match_elo = elo_dict[bf]
    bs_pre_match_elo = elo_dict[bs]
    # assigns home advantage (if there is any)
    host_country = match_facts["Country"]
    ground_name = match_facts["Ground"]
    city = match_facts["City"]
    ground = ground_name + "," + city + "," + host_country
    if bf == host_country:
        bf_pre_match_elo += home_advantage_elo_boost
    elif bs == host_country:
        bs_pre_match_elo += home_advantage_elo_boost
    # adds the elo boost to the team batting first based on the ground and the team
    bf_elo_boost = ground_stats_df[(ground_stats_df["Country"] == host_country) & (ground_stats_df["City"] == city) &
                                   (ground_stats_df["Ground Name"] == ground_name)].iloc[0]["Batting First Elo Boost"]
    if bf not in bat_first_elo_dict:
        bat_first_elo_dict.update({bf: 0})
    if bs not in bat_first_elo_dict:
        bat_first_elo_dict.update({bs: 0})
    bf_elo_boost += bat_first_elo_dict[bf] + bat_first_elo_dict[bs]
    bf_pre_match_elo += bf_elo_boost
    match_type = match_facts["Series Type"]
    k_factor = 20
    # changes the impact of the ratings depending on the kind of match
    # world cup matches have the most importance
    if match_type == "world-cup":
        k_factor *= 2
    # Asia Cup and ICC Champions Trophy Matches also have more weight than regular ODI matches
    elif match_type == 'asia-cup' or match_type == 'bang':
        k_factor *= 1.5
    # calculates the odds of the team batting first winning the match
    bf_win_expectancy = 1 / (10 ** ((bs_pre_match_elo - bf_pre_match_elo) / 400) + 1)
    # finds the adjusted run rate and finds the value to be used in elo points exchanges
    # 1.64 is the standard deviation of NRR for all ODI matches
    bf_adjusted_run_rate = match_facts["Team 1 Projected 50 Overs Score"] / 50
    bs_adjusted_run_rate = match_facts["Team 2 Projected 50 Overs Score"] / 50
    bf_nrr = bf_adjusted_run_rate - bs_adjusted_run_rate
    percentile = match_facts['RR Margin Percentile']
    if percentile > 0.9999999999998945:
        percentile = 0.9999999999998945
    elif percentile < 0.0000000000001055:
        percentile = 0.0000000000001055
    z_score = statistics.NormalDist().inv_cdf(percentile)
    nrr_factor = 1.3 * z_score
    nrr_margin_increase = (0.75 + (nrr_factor - 3) / 8)
    # calculates the change in rating for each time
    if winner == bf:
        bf_change_in_rating = (1 - bf_win_expectancy) * k_factor * nrr_margin_increase
    elif winner == 'Tie':
        bf_change_in_rating = (0.5 - bf_win_expectancy) * k_factor
    else:
        bf_change_in_rating = (0 - bf_win_expectancy) * k_factor * nrr_margin_increase
    # updates the elo ratings after the match
    elo_dict[bf] += bf_change_in_rating
    elo_dict[bs] -= bf_change_in_rating
    time_sensitive_elo_dict.update({bf: elo_dict[bf]})
    time_sensitive_elo_dict.update({bs: elo_dict[bs]})
    # updates for home field advantage updates
    if bf == host_country:
        home_advantage_elo_boost += 0.075 * bf_change_in_rating
    elif bs == host_country:
        home_advantage_elo_boost -= 0.075 * bf_change_in_rating
    # updates for bat first elo ratings
    bat_first_elo_dict[bf] += 0.075 * bf_change_in_rating
    bat_first_elo_dict[bs] += 0.075 * bf_change_in_rating
    # updates the ground tilt (high run vs low run pitch)
    avg_rr = (bf_adjusted_run_rate + bs_adjusted_run_rate) / 2
    if ground not in grounds_tilt_dict:
        grounds_tilt_dict.update({ground: [avg_rr, 1]})
    else:
        match_weight = 1 / ((grounds_tilt_dict[ground][1] + 1) / 1.25)
        grounds_tilt_dict[ground][0] = match_weight * avg_rr + (1 - match_weight) * grounds_tilt_dict[ground][0]
    # updates the tilt (bowling or batting strength) of both teams
    ground_adj_rr = grounds_tilt_dict[ground][0]
    match_runs_percentile = statistics.NormalDist(mu=ground_adj_rr, sigma=0.9386).cdf(avg_rr)
    if bf not in teams_tilt_dict:
        teams_tilt_dict.update({bf: [match_runs_percentile, 1]})
    else:
        match_weight = 1 / ((teams_tilt_dict[bf][1] + 1) / 1.25)
        teams_tilt_dict[bf][0] = match_weight * match_runs_percentile + teams_tilt_dict[bf][0] * (1 - match_weight)
    if bs not in teams_tilt_dict:
        teams_tilt_dict.update({bs: [match_runs_percentile, 1]})
    else:
        match_weight = 1 / ((teams_tilt_dict[bf][1] + 1) / 1.25)
        teams_tilt_dict[bs][0] = match_weight * match_runs_percentile + teams_tilt_dict[bs][0] * (1 - match_weight)
    # records the ratings to use in a line graph
    elo_line_graph_dict["Date"].append(date)
    bat_first_elo_line_graph["Date"].append(date)
    teams_tilt_line_graph["Date"].append(date)
    for team in teams_of_interest:
        if team not in time_sensitive_elo_dict:
            elo_line_graph_dict[team].append(np.NaN)
            bat_first_elo_line_graph[team].append(np.NaN)
            teams_tilt_line_graph[team].append(np.NaN)
        else:
            elo_line_graph_dict[team].append(elo_dict[team])
            bat_first_elo_line_graph[team].append(bat_first_elo_dict[team])
            teams_tilt_line_graph[team].append(teams_tilt_dict[team][0])
    if idx % 100 == 0:
        print(match_facts['Date'])
        print()
        time_sensitive_elo_dict = dict(sorted(time_sensitive_elo_dict.items(), key=lambda item: item[1], reverse=True))
        elo_ratings_df = pd.DataFrame(list(time_sensitive_elo_dict.items()), columns=["Team", "Rating"])
        rank = 0
        ranked_bf_elo_dict = {}
        ranked_batting_tilt_dict = {}
        for team, rating in time_sensitive_elo_dict.items():
            rank += 1
            ranked_bf_elo_dict.update({team: bat_first_elo_dict[team]})
            ranked_batting_tilt_dict.update({team: teams_tilt_dict[team][0]})
            print(rank, team, rating, bat_first_elo_dict[team], teams_tilt_dict[team][0])
        print()
print("Current Ratings:")
print(match_facts['Date'])
print()
time_sensitive_elo_dict = dict(sorted(time_sensitive_elo_dict.items(), key=lambda item: item[1], reverse=True))
elo_ratings_df = pd.DataFrame(list(time_sensitive_elo_dict.items()), columns=["Team", "Rating"])
rank = 0
ranked_bf_elo_dict = {}
ranked_batting_tilt_dict = {}
for team, rating in time_sensitive_elo_dict.items():
    rank += 1
    ranked_bf_elo_dict.update({team: bat_first_elo_dict[team]})
    ranked_batting_tilt_dict.update({team: teams_tilt_dict[team][0]})
    print(rank, team, rating, bat_first_elo_dict[team], teams_tilt_dict[team][0])
print()

elo_ratings_df['Bat First Elo Adj'] = list(ranked_bf_elo_dict.values())
# elo_ratings_df['Batting Dependency Score'] = list(ranked_batting_tilt_dict.values())
elo_ratings_df['Rank'] = list(range(1, 27))
elo_ratings_df.set_index("Rank", inplace=True)
elo_ratings_df.to_csv("ODI_Elo_Ratings.csv", index=True, header=True)
end_time = time.time()
print("Ground-Adjusted Elo Ratings Determined from Matches in", round((end_time - start_time) / 60, 2), "Minutes")

elo_line_graph_df = pd.DataFrame(elo_line_graph_dict)
bat_first_line_graph_df = pd.DataFrame(bat_first_elo_line_graph)
team_tilt_line_graph_df = pd.DataFrame(teams_tilt_line_graph)