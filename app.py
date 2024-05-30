import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, leaguestandings, commonplayerinfo
from nba_api.stats.static import players, teams

# Function to get player ID by name
def get_player_id(player_name):
    nba_players = players.get_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

# Function to get player info
def get_player_info(player_id):
    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    return player_info.get_data_frames()[0]

# Function to get team members
def get_team_members(team_id):
    team_players = players.get_players()
    return [player for player in team_players if player['team_id'] == team_id]

# Function to get all-star players
def get_all_star_players():
    all_star_players = players.get_players()
    return [player for player in all_star_players if player['is_all_star']]

# Function to fetch player stats
def get_player_stats(player_id, season='2023-24'):
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    stats = career_stats.get_data_frames()[0]
    return stats[stats['SEASON_ID'] == season]

# Streamlit app
st.title("NBA Player Visualization and Prediction")

# User input for player names
player_names_input = st.text_input("Enter three player names separated by commas").split(',')

# User input for toggle options
toggle_option = st.selectbox("Select visualization type", ["Points-Per-Game (PPG)", "Rebounds-Per-Game (RPG)", "Individual Scores", "Field Goals", "Age of Players", "All Star Scores"])

# Initialize lists to store player data
ppg_values = []
rpg_values = []
individual_scores = []
field_goals = []
ages = []
all_star_scores = []
player_names = []

for player_name in player_names_input:
    player_name = player_name.strip()
    player_id = get_player_id(player_name)
    if player_id:
        player_info = get_player_info(player_id)
        player_stats = get_player_stats(player_id)
        
        if not player_stats.empty:
            player_names.append(player_name)
            ppg_values.append(player_stats['PTS'].values[0])
            rpg_values.append(player_stats['REB'].values[0])
            individual_scores.append(player_stats['PTS'].values[0])
            field_goals.append(player_stats['FGM'].values[0])
            ages.append(player_info['BIRTHDATE'].values[0])
            if player_info['is_all_star']:
                all_star_scores.append(player_stats['PTS'].values[0])
    else:
        st.warning(f"Player {player_name} not found.")

# Create graphs based on toggle option
if player_names:
    if toggle_option == "Points-Per-Game (PPG)":
        fig = go.Figure(data=[go.Bar(name='PPG', x=player_names, y=ppg_values)])
    elif toggle_option == "Rebounds-Per-Game (RPG)":
        fig = go.Figure(data=[go.Bar(name='RPG', x=player_names, y=rpg_values)])
    elif toggle_option == "Individual Scores":
        fig = go.Figure(data=[go.Bar(name='Individual Scores', x=player_names, y=individual_scores)])
    elif toggle_option == "Field Goals":
        fig = go.Figure(data=[go.Bar(name='Field Goals', x=player_names, y=field_goals)])
    elif toggle_option == "Age of Players":
        fig = go.Figure(data=[go.Bar(name='Ages', x=player_names, y=ages)])
    elif toggle_option == "All Star Scores":
        fig = go.Figure(data=[go.Bar(name='All Star Scores', x=player_names, y=all_star_scores)])

    # Add title and labels
    fig.update_layout(
        title=f'Player {toggle_option} Comparison 23-24 Season',
        xaxis_title='Players',
        yaxis_title=toggle_option,
        barmode='group'
    )

    # Display the chart
    st.plotly_chart(fig)
else:
    st.info("Please enter at least one valid player name.")

