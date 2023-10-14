import pandas as pd
import time
import copy
from Getting_Current_Ratings import time_sensitive_elo_dict, home_advantage_elo_boost, df, bat_first_elo_dict
import random
import statistics

# Convert the "Date" column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# filters the data frame for 2023 World Cup matches
wc_2023_matches = df[(df['Date'].dt.year == 2023) & (df['Series Type'] == 'world-cup')]

# imports the venue data for World Cup Matches
wc_2023_venue_df = pd.read_csv("World_Cup_2023_GS_Grounds.csv")

# imports ground data
ground_data = pd.read_csv("ODI Grounds.csv")
ground_data = ground_data[ground_data["Country"] == "India"]
ground_bf_dict = {}
for idx, row in ground_data.iterrows():
    ground_bf_dict.update({row["Ground Name"]: row["Batting First Elo Boost"]})

# India gets a boost from being the hosts of the tournament
time_sensitive_elo_dict['India'] += home_advantage_elo_boost

wc_teams = ['India', 'Australia', 'New Zealand', 'England', 'South Africa', 'Pakistan', 'Sri Lanka', 'Bangladesh',
            'Afghanistan', 'Netherlands']

# this simulates a match based on elo ratings and returns the team_1 nrr
def match_simulation(team_1, team_2, team_1_elo, team_2_elo, ground_bf_elo_boost):
    # uses the elo formula to get the two-outcome win probability
    batting_first = random.randrange(0, 2)
    if batting_first == 0:
        team_1_elo += bat_first_elo_dict[team_1] - bat_first_elo_dict[team_2] + ground_bf_elo_boost
    else:
        team_2_elo += bat_first_elo_dict[team_2] - bat_first_elo_dict[team_1] + ground_bf_elo_boost
    team_1_wl = 1 / (10 ** ((team_2_elo - team_1_elo) / 400) + 1)
    team_1_margin_mean = statistics.NormalDist(0, 0.534).inv_cdf(team_1_wl)
    team_1_nrr = statistics.NormalDist(team_1_margin_mean, 0.534).inv_cdf(random.random())
    # we use 285 as the team 1's score. We can use any value but 285 is around the average for an ODI innings in the
    # modern age
    if batting_first == 0:
        team_1_runs = 285
        team_1_overs = 50
        if team_1_nrr > 0:
            team_2_overs = 50
            team_2_runs = team_1_runs - (team_1_nrr * team_1_overs)
        else:
            team_2_runs = 286
            team_2_overs = team_2_runs / ((team_1_runs / team_1_overs) - team_1_nrr)
    else:
        team_2_runs = 285
        team_2_overs = 50
        if team_1_nrr > 0:
            team_1_runs = 286
            team_1_overs = team_1_runs / ((team_2_runs / team_2_overs) + team_1_nrr)
        else:
            team_1_overs = 50
            team_1_runs = team_2_runs + (team_1_nrr * team_1_overs)

    return [team_1_runs, team_1_overs, team_2_runs, team_2_overs]

# this function helps sort the league table dictionary
def sort_table_dict(item):
    # These variables assist in locating "column" numbers
    nrr = 4
    points = 5
    club, stats = item
    return (stats[points], stats[nrr])

# dictionary in the form of {Team: [Total Runs, Total Overs Batted, Total Runs Conceded, Total Overs Bowled,
#                                   Net Run Rate, Points]}
wc_table = {}
for team in wc_teams:
    wc_table.update({team: [0, 0, 0, 0, 0, 0]})

# list of fixtures completed
fixtures_completed = []
for match_num, match_facts in wc_2023_matches.iterrows():
    winner = match_facts["Winner"]
    bf = match_facts["Batting First"]
    bs = match_facts["Batting Second"]
    # doesn't change the ratings if there is no result
    if winner == bf:
        wc_table[bf][5] += 2
    elif winner == bs:
        wc_table[bs][5] += 2
    elif winner == 'No Result':
        wc_table[bf][5] += 1
        wc_table[bs][5] += 1
    # gets the score information
    bf_adj_rr = match_facts["Team 1 Adjusted Run Rate"]
    bs_adj_rr = match_facts["Team 2 Adjusted Run Rate"]
    bf_runs = match_facts["Team 1 Runs"]
    bs_runs = match_facts["Team 2 Runs"]
    bf_adj_overs = bf_runs / bf_adj_rr
    bs_adj_overs = bs_runs / bs_adj_rr
    # adds the score info to the table
    wc_table[bf][0] += bf_runs
    wc_table[bs][0] += bs_runs
    wc_table[bf][1] += bf_adj_overs
    wc_table[bs][1] += bs_adj_overs
    wc_table[bf][2] += bs_runs
    wc_table[bs][2] += bf_runs
    wc_table[bf][3] += bs_adj_overs
    wc_table[bs][3] += bf_adj_overs
    # adds the match to list of fixtures completed
    fixtures_completed.append([bf, bs])

knockouts_started = False
# if the knockout rounds have started, we record the data in a seperate data frame
if len(wc_2023_matches) > 45:
    knockouts_started = True
    knockout_matches = wc_2023_matches.iloc[45:]
    wc_2023_matches = wc_2023_matches.iloc[0:45]


# dictionary in the form of {Team: [Avg_Pos, Avg_NRR, Avg_Points, 1st, 2nd, 3rd, 4th, Make SF, Make F, Win F]}
wc_sims_table = {}
for team in wc_teams:
    wc_sims_table.update({team: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})

start_time = time.time()
for sim in range(10000):
    sim_wc_table = copy.deepcopy(wc_table)
    for team_num1, team_1 in enumerate(wc_teams):
        for team_num2, team_2 in enumerate(wc_teams):
            if team_num1 <= team_num2:
                # we don't want matches between the same 2 teams or both home and away matches
                continue
            elif [team_1, team_2] in fixtures_completed or [team_2, team_1] in fixtures_completed:
                # skips over completed matches
                continue
            else:
                # simulates the match if it hasn't been completed
                team_1_elo = time_sensitive_elo_dict[team_1]
                team_2_elo = time_sensitive_elo_dict[team_2]
                # finds the venue information
                ground = wc_2023_venue_df[
                    ((wc_2023_venue_df["First Team"] == team_1) | (wc_2023_venue_df["Second Team"] == team_1)) &
                    ((wc_2023_venue_df["First Team"] == team_2) | (wc_2023_venue_df["Second Team"] == team_2))
                    ].iloc[0]["Ground"]
                bf_ground_elo_boost = ground_bf_dict[ground]
                sim_match = match_simulation(team_1, team_2, team_1_elo, team_2_elo, bf_ground_elo_boost)
                # adds the match statistics after a match has been simulated
                for team_1_idx, score_piece in enumerate(sim_match):
                    sim_wc_table[team_1][team_1_idx] += score_piece
                    if team_1_idx < 2:
                        sim_wc_table[team_2][team_1_idx + 2] += score_piece
                    else:
                        sim_wc_table[team_2][team_1_idx - 2] += score_piece
                if sim_match[0] > sim_match[2]:
                    sim_wc_table[team_1][5] += 2
                else:
                    sim_wc_table[team_2][5] += 2
    # calculates Net Run Rate
    for team, standings_info in sim_wc_table.items():
        standings_info[4] = (standings_info[0] / standings_info[1]) - (standings_info[2] / standings_info[3])
    # sorts the table into final group stage positions
    final_sim_wc_table = dict(sorted(sim_wc_table.items(), key=sort_table_dict, reverse=True))
    # adds group stage info to simulation summary data
    rank = 0
    semifinalists = []
    for team, standings_info in final_sim_wc_table.items():
        rank += 1
        wc_sims_table[team][0] += rank
        wc_sims_table[team][1] += standings_info[4]
        wc_sims_table[team][2] += standings_info[5]
        if rank <= 4:
            wc_sims_table[team][2 + rank] += 1
            wc_sims_table[team][7] += 1
            semifinalists.append(team)
    sfs = [[semifinalists[0], semifinalists[3]], [semifinalists[1], semifinalists[2]]]
    # semifinal stage
    finalists = []
    if knockouts_started:
        sf_1_winner = knockout_matches.iloc[0]["Winner"]
        sf_2_winner = knockout_matches.iloc[1]["Winner"]
    else:
        # determining venues for both semifinals
        if "Pakistan" in sfs[0]:
            venues = ["Eden Gardens", "Wankhede Stadium"]
        elif ("Pakistan" not in semifinalists) and ("India" in sfs[1]):
            venues = ["Eden Gardens", "Wankhede Stadium"]
        else:
            venues = ["Wankhede Stadium", "Eden Gardens"]
        # simulates the semifinals if they have not been completed yet
        for sf_num, sf in enumerate(sfs):
            team_1 = sf[0]
            team_2 = sf[1]
            team_1_elo = time_sensitive_elo_dict[team_1]
            team_2_elo = time_sensitive_elo_dict[team_2]
            ground = venues[sf_num]
            bf_ground_elo_boost = ground_bf_dict[ground]
            sim_match = match_simulation(team_1, team_2, team_1_elo, team_2_elo, bf_ground_elo_boost)
            if sim_match[0] > sim_match[2]:
                finalists.append(team_1)
                wc_sims_table[team_1][8] += 1
            else:
                finalists.append(team_2)
                wc_sims_table[team_2][8] += 1
    # world cup final stage
    team_1 = finalists[0]
    team_2 = finalists[1]
    team_1_elo = time_sensitive_elo_dict[team_1]
    team_2_elo = time_sensitive_elo_dict[team_2]
    ground_bf_elo_boost = ground_bf_dict["Narendra Modi Stadium"]
    sim_match = match_simulation(team_1, team_2, team_1_elo, team_2_elo, ground_bf_elo_boost)
    if sim_match[0] > sim_match[2]:
        wc_sims_table[team_1][9] += 1
    else:
        wc_sims_table[team_2][9] += 1
    # time updates
    if (sim + 1) % 10 == 0:
        print("Simulations", (sim + 1) / 100, "% complete")
        current_time = time.time()
        expected_total_time = (current_time - start_time) / ((sim + 1) / 10000)
        time_left_minutes = round((expected_total_time - (current_time - start_time)) / 60, 2)
        print(time_left_minutes, "Minutes left")
end_time = time.time()
print()
print("World Cup Simulated in", round((end_time - start_time) / 60, 2), "Minutes")

pd.set_option("display.max_columns", None)  # Display all columns
pd.set_option("display.expand_frame_repr", False)  # Prevent line-wrapping
pd.set_option("display.width", None)  # Auto-adjust the column width

# puts the information into a Data Frame
world_cup_sim_summary_df = pd.DataFrame(columns=["Avg Pos", "Avg NRR", "Avg Pts", "1st", "2nd", "3rd", "4th",
                                                 "Make SF", "Make Final", "Win World Cup"],
                                        data=list(wc_sims_table.values()))
world_cup_sim_summary_df = world_cup_sim_summary_df / 10000
world_cup_sim_summary_df.insert(0, "Team", list(wc_sims_table.keys()))
# Sorts by Average Position
world_cup_sim_summary_df.sort_values(by='Avg Pos', inplace=True)
# creates a new index for how the Teams will be viewed in Data Frames
world_cup_sim_summary_df['Pos'] = list(range(1, 11))
world_cup_sim_summary_df.set_index("Pos", inplace=True)
world_cup_sim_summary_df.to_csv("2023_World_Cup_Expected_Results.csv", index=True, header=True)

# Round and format the percentage columns
percentage_cols = ["1st", "2nd", "3rd", "4th", "Make SF", "Make Final", "Win World Cup"]
world_cup_sim_summary_df[percentage_cols] = (world_cup_sim_summary_df[percentage_cols]).applymap(
    lambda x: f'{x:.0%}')
world_cup_sim_summary_df[["Avg Pos", "Avg Pts"]] = round(world_cup_sim_summary_df[["Avg Pos", "Avg Pts"]], 1)
world_cup_sim_summary_df["Avg NRR"] = round(world_cup_sim_summary_df["Avg NRR"], 2)

print(world_cup_sim_summary_df)
