import pandas as pd
import random
import time
import statistics
import math
from scipy import stats

# imports data from all ODIs
df = pd.read_csv("ODI_Matches_Data.csv")
# gets the net run rate for a projected 50 overs score
df["Adj RR Margin"] = abs(df["Team 1 Projected 50 Overs Score"] - df["Team 2 Projected 50 Overs Score"]) / 50
# gets rid of matches with no result
df = df[df["Winner"] != 'No Result']
# finds the percentile for the 'BF Adj NRR' column
df['RR Margin Percentile'] = df["Adj RR Margin"].rank(pct=True)

# Convert the "Date" column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

icc_tournament_data = pd.read_csv("ICC_Tournament_Results.csv")

icc_wc_final_match_nums = [33, 73, 223, 477, 752, 1083, 1484, 1993, 2581, 3148, 3646, 4192]
icc_champions_trophy_final_match_nums = [1364, 1639, 1889, 2182, 2443, 2907, 3377, 3894]

# these are a list of teams to ignore
teams_to_ignore = ['ICC World XI', 'Asia XI', 'Africa XI']

# this is used to calculate the starting elo ratings for each ODI side
grand_elo_dict = {'England': 1500, 'Australia': 1500, 'New Zealand': 1500, 'Pakistan': 1500, 'West Indies': 1500,
                  'India': 1500, 'East Africa': 1500, 'Sri Lanka': 1500, 'Canada': 1500, 'Zimbabwe': 1500,
                  'Bangladesh': 1500, 'South Africa': 1500, 'United Arab Emirates': 1500, 'Netherlands': 1500,
                  'Kenya': 1500, 'Scotland': 1500, 'Namibia': 1500, 'Hong Kong': 1500, 'United States of America': 1500,
                  'Bermuda': 1500, 'Ireland': 1500, 'Afghanistan': 1500, 'Papua New Guinea': 1500, 'Nepal': 1500,
                  'Oman': 1500, 'Jersey': 1500}
starting_home_advantage = 0
starting_k_factor = 20

lowest_pts_tot = 100000
lowest_rank_fluc = 100000000
start_time = time.time()
for simulation in range(10000):
    starting_hfa_elo = starting_home_advantage + random.randrange(-10, 11)
    if starting_hfa_elo > 500:
        starting_hfa_elo = 500
    elif starting_hfa_elo < 0:
        starting_hfa_elo = 0
    initial_k_factor = starting_k_factor
    if initial_k_factor < 5:
        initial_k_factor = 5
    elif initial_k_factor > 25:
        initial_k_factor = 25
    home_advantage_elo = starting_hfa_elo
    home_advantage_fluctuations = 0
    elo_dict = {}
    sim_elo_dict = {}
    elo_fluctuations = {}
    rank_fluctuations = {}
    time_sensitive_elo_dict = {}
    # in the form of {team: [total fluctuation, matches played]}
    for team, rating in grand_elo_dict.items():
        tentative_rating = rating + random.randrange(-10, 11)
        if tentative_rating < 500:
            tentative_rating = 500
        elif tentative_rating > 2500:
            tentative_rating = 2500
        sim_elo_dict.update({team: tentative_rating})
        elo_dict.update({team: sim_elo_dict[team]})
        elo_fluctuations.update({team: [0, 0]})
        rank_fluctuations.update({team: 0})
    for idx, match_facts in df.iterrows():
        match_num = match_facts["ODI #"]
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
        if bf == host_country:
            bf_pre_match_elo += home_advantage_elo
        elif bs == host_country:
            bs_pre_match_elo += home_advantage_elo
        match_type = match_facts["Series Type"]
        # changes the impact of the ratings depending on the kind of match
        # world cup matches have the most importance
        k_factor = initial_k_factor
        if match_type == "world-cup":
            k_factor *= 3
        # Asia Cup and ICC Champions Trophy Matches also have more weight than regular ODI matches
        elif match_type == 'asia-cup' or match_type == 'bang':
            k_factor *= 2
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
        elo_fluctuations[bf][0] += abs(bf_change_in_rating)
        elo_fluctuations[bs][0] += abs(bf_change_in_rating)
        elo_fluctuations[bf][1] += 1
        elo_fluctuations[bs][1] += 1
        time_sensitive_elo_dict.update({bf: elo_dict[bf]})
        time_sensitive_elo_dict.update({bs: elo_dict[bs]})
        if bf == host_country:
            home_advantage_elo += 0.075 * bf_change_in_rating
            home_advantage_fluctuations += abs(0.075 * bf_change_in_rating)
        elif bs == host_country:
            home_advantage_elo -= 0.075 * bf_change_in_rating
            home_advantage_fluctuations += abs(0.075 * bf_change_in_rating)
        if match_num in icc_wc_final_match_nums:
            year = match_facts["Date"].year
            tournament_info = icc_tournament_data[icc_tournament_data["Year"] == year].iloc[0]
            time_sensitive_elo_dict = dict(
                sorted(time_sensitive_elo_dict.items(), key=lambda item: item[1], reverse=True))
            rank = 0
            for team in time_sensitive_elo_dict:
                rank += 1
                tournament_rank = tournament_info[team]
                if pd.isna(tournament_rank):
                    tournament_rank = 26
                rank_fluctuations[team] += math.pow((rank - tournament_rank), 2)
        elif match_num in icc_champions_trophy_final_match_nums:
            year = match_facts["Date"].year
            tournament_info = icc_tournament_data[icc_tournament_data["Year"] == year].iloc[0]
            time_sensitive_elo_dict = dict(
                sorted(time_sensitive_elo_dict.items(), key=lambda item: item[1], reverse=True))
            rank = 0
            for team in time_sensitive_elo_dict:
                rank += 1
                tournament_rank = tournament_info[team]
                if pd.isna(tournament_rank):
                    tournament_rank = 26
                rank_fluctuations[team] += math.pow((rank - tournament_rank), 2) * 2 / 3

    total_rank_fluc = 0
    for team, fluc in rank_fluctuations.items():
        total_rank_fluc += fluc
    total_pts_fluc = 0
    for team, data in elo_fluctuations.items():
        pts_fluc = data[0] / data[1]
        total_pts_fluc += pts_fluc
    if total_rank_fluc < lowest_rank_fluc and total_pts_fluc < lowest_pts_tot:
        lowest_pts_tot = total_pts_fluc
        lowest_rank_fluc = total_rank_fluc
        print("New Lowest: ", lowest_rank_fluc)
        print()
        print("Simulation Number:", simulation)
        grand_elo_dict = sim_elo_dict
        starting_home_advantage = starting_hfa_elo
        starting_k_factor = initial_k_factor
        print("Starting Home Advantage Elo:", starting_hfa_elo)
        print("K-Factor:", initial_k_factor)
        print("Total Rank Differences:", total_rank_fluc)
        print("Total Points Fluctuation:", total_pts_fluc)
        print("Starting Elos:")
        print(grand_elo_dict)
        print("Current Elos:")
        print(elo_dict)
        print()
    if (simulation + 1) % 10 == 0:
        current_time = time.time()
        pct_complete = (simulation + 1) / 10000
        time_so_far = current_time - start_time
        est_total_time = time_so_far / pct_complete
        print(pct_complete * 100, "% complete")
        print(round((est_total_time - time_so_far) / 60, 2), "Minutes left")
        print()

end_time = time.time()
print(round((end_time - start_time) / 60, 2), "Minutes spent for it to complete")
