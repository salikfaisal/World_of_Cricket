from espncricinfo.match import Match
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# reads dataset of ODI matches
odi_matches_df = pd.read_csv("ODI_Matches_Data.csv")
previous_matches = odi_matches_df["Match ID"].tolist()
num_of_prev_matches = len(previous_matches)

# list of years since the ODI Format was introduced to International Cricket in 1971
years = list(range(1971, 2024))

# list of match ids for all ODI Matches
new_match_ids = []

start_time = time.time()
# scrapes data from each year of T20I matches and adds the Match IDs for the year to a list
for year in years:
    url = 'https://www.espncricinfo.com/records/year/team-match-results/' + str(year) + '-' + str(year) + \
          '/one-day-internationals-2'
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')
    matches_table = soup.find(class_='ds-w-full ds-table ds-table-xs ds-table-auto ds-w-full ds-overflow-scroll '
                                     'ds-scrollbar-hide')
    rows = matches_table.find_all('tr')
    # iterates through rows on the table for match_id info
    for row in rows:
        odi_num = row.find_all(class_="ds-min-w-max ds-text-right")[-1].text
        match_id_link = row.find('a', title=odi_num)
        if match_id_link:
            match_id = int(match_id_link['href'].split('-')[-2].split('/')[0])
            # finds new matches
            if match_id not in previous_matches:
                new_match_ids.append(match_id)
    print(year, "Match IDs Extracted.")
    print()
end_time = time.time()
print("ESPN CricInfo Match IDs Extracted in", round((end_time - start_time) / 60, 2), "Minutes")

print(new_match_ids)
# analyzes each match and extracts key data
match_nums = []
series = []
dates = []
grounds = []
cities = []
countries = []
winners = []
bf = []
bf_runs = []
bf_wickets = []
bf_overs = []
bf_adjusted_run_rate = []
bs = []
bs_runs = []
bs_wickets = []
bs_overs = []
bs_adjusted_run_rate = []
num_of_new_matches = len(new_match_ids)
missing_cities = []

print("Extracting ODI Match Data")
start_time = time.time()
new_match_ids_cutoff = len(new_match_ids)
for match_num, match_id in enumerate(new_match_ids):
    print("Match ID:", match_id)
    # this gets information base on the match ID
    match = Match(str(match_id))
    # this has the match information in json format
    json_info = match.json
    # extracts a dictionary of match information from the json info
    match_info = json_info["match"]
    # extracts key match information
    date = match_info["end_date_raw"]
    host_country = match_info["country_name"]
    host_city = match_info["town_name"]
    ground_name = match_info["ground_name"]
    if ',' in ground_name:
        ground_name = ground_name.split(',')[0]
    # finds the type of match (for example: 'asia-cup')
    match_type = json_info["series"][0]["slug"]
    # gets a dictionary of {team_id: team_name}
    team_id_dict = {match_info["team1_id"]: match_info["team1_name"], match_info["team2_id"]: match_info["team2_name"]}
    team_1 = list(team_id_dict.values())[0]
    team_2 = list(team_id_dict.values())[1]
    # examines the match result and adds the match winner (if there is one) to the list
    match_result = match.result
    if match_result[0:9] == 'No result':
        winners.append('No Result')
    elif match_result[0:10] == 'Match tied':
        winners.append('Tie')
    elif match_result == 'Match abandoned without a ball bowled':
        winners.append('No Result')
    elif match.status == 'current' or match.status == 'dormant':
        new_match_ids_cutoff = match_num
        break
    else:
        winner_team_id = match_info["winner_team_id"]
        winners.append(team_id_dict[winner_team_id])
    # appends the extracted information to their respective lists
    match_nums.append(match_num + 1 + num_of_prev_matches)
    series.append(match_type)
    dates.append(date)
    grounds.append(ground_name)
    cities.append(host_city)
    countries.append(host_country)
    # gets the batting order of the teams
    batting_first_id = match_info["batting_first_team_id"]
    if batting_first_id != '0':
        batting_first = team_id_dict[batting_first_id]
    else:
        batting_first = team_1
    if team_1 == batting_first:
        batting_second = team_2
    else:
        batting_second = team_1
    bf.append(batting_first)
    bs.append(batting_second)
    # gets the innings information
    innings = json_info["innings"]
    if len(innings) > 0:
        for inning_number, inning in enumerate(innings):
            if inning_number == 0:
                bf_runs.append(int(inning['runs']))
                bf_wickets.append(int(inning['wickets']))
                overs_completed = int(inning['balls']) // 6
                balls_in_last_over = int(inning['balls']) % 6
                overs = str(overs_completed)
                if balls_in_last_over != 0:
                    overs += '.' + str(balls_in_last_over)
                bf_overs.append(overs)
                if bf_wickets[-1] != 10:
                    balls_for_rr = overs_completed * 6 + balls_in_last_over
                else:
                    balls_for_rr = int(inning['ball_limit'])
                if balls_for_rr == 0:
                    bf_adjusted_run_rate.append('NA')
                else:
                    bf_adjusted_run_rate.append(bf_runs[-1] / balls_for_rr * 6)
            else:
                bs_runs.append(int(inning['runs']))
                bs_wickets.append(int(inning['wickets']))
                overs_completed = int(inning['balls']) // 6
                balls_in_last_over = int(inning['balls']) % 6
                overs = str(overs_completed)
                if balls_in_last_over != 0:
                    overs += '.' + str(balls_in_last_over)
                bs_overs.append(overs)
                if bs_wickets[-1] != 10:
                    balls_for_rr = int(inning['balls'])
                else:
                    balls_for_rr = int(inning['ball_limit'])
                if balls_for_rr == 0:
                    bs_adjusted_run_rate.append('NA')
                else:
                    bs_adjusted_run_rate.append(bs_runs[-1] / balls_for_rr * 6)
    else:
        # this is for matches where a match was abandoned before a ball was bowled
        bf_runs.append(0)
        bf_wickets.append(0)
        bf_overs.append(0)
        bf_adjusted_run_rate.append('NA')
        bs_runs.append(0)
        bs_wickets.append(0)
        bs_overs.append(0)
        bs_adjusted_run_rate.append('NA')
    pct_complete = (match_num + 1) * 100 / num_of_new_matches
    current_time = time.time()
    time_so_far = current_time - start_time
    projected_total_time = time_so_far / (pct_complete / 100)
    print(str(pct_complete) + '% complete')
    print(round((projected_total_time - time_so_far) / 60, 2), "Minutes left")
end_time = time.time()
print("New Match Info Extracted in", round((end_time - start_time) / 60, 2), "Minutes")


# cuts off match ids that are not ready to be examined
new_match_ids = new_match_ids[0:new_match_ids_cutoff]
# Creates a data frame to store all of the data recorded from the matches
new_data = {'ODI #': match_nums, 'Match ID': new_match_ids, 'Series Type': series, 'Winner': winners, 'Date': dates,
            'Batting First': bf, 'Team 1 Runs': bf_runs, 'Team 1 Wickets': bf_wickets, 'Team 1 Overs': bf_overs,
            'Team 1 Adjusted Run Rate': bf_adjusted_run_rate, 'Batting Second': bs, 'Team 2 Runs': bs_runs,
            'Team 2 Wickets': bs_wickets, 'Team 2 Overs': bs_overs, 'Team 2 Adjusted Run Rate': bs_adjusted_run_rate,
            'Ground': grounds, 'City': cities, 'Country': countries}
new_odi_matches_df = pd.DataFrame(new_data)

# adds new data to previous data frame and saves data frame to a CSV file
df = pd.concat([odi_matches_df, new_odi_matches_df], axis=0)
df.to_csv("ODI_Matches_Data.csv", index=False, header=True)
