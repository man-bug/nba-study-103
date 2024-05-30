import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from nba_api.stats.static import players
from requests.exceptions import ReadTimeout
from tenacity import retry, stop_after_attempt, wait_fixed

# Function to get player ID by name
def get_player_id(player_name):
    nba_players = players.get_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

# Retry settings: retry up to 3 times with a 5 second wait between attempts
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def fetch_player_info(player_id):
    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, timeout=20)
    return player_info.get_data_frames()[0]

# Function to get player info
def get_player_info(player_id):
    try:
        player_info = fetch_player_info(player_id)
        return player_info
    except ReadTimeout:
        st.error(f"Request timed out while fetching data for player ID: {player_id}")
        return None

# Function to fetch player stats
def get_player_stats(player_id, season='2023-24'):
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    stats = career_stats.get_data_frames()[0]
    return stats[stats['SEASON_ID'] == season]

# Streamlit app
st.title("NBA Player Visualization and Prediction")

# User input for player name
player_name_input = st.text_input("Enter a player name")

# User input for toggle options
toggle_option = st.selectbox("Select visualization type", ["Points-Per-Game (PPG)", "Rebounds-Per-Game (RPG)", "Individual Scores", "Field Goals", "Age of Player", "All Star Scores"])

# Initialize variables to store player data
ppg_value = 0
rpg_value = 0
individual_score = 0
field_goal = 0
age = None
all_star_score = 0
player_name = None

if player_name_input:
    player_id = get_player_id(player_name_input.strip())
    if player_id:
        player_info = get_player_info(player_id)
        if player_info is not None:
            player_stats = get_player_stats(player_id)
            
            if not player_stats.empty:
                player_name = player_name_input
                ppg_value = player_stats['PTS'].values[0]
                rpg_value = player_stats['REB'].values[0]
                individual_score = player_stats['PTS'].values[0]
                field_goal = player_stats['FGM'].values[0]
                age = player_info['BIRTHDATE'].values[0]
                if player_info['IS_ALL_STAR'].values[0]:
                    all_star_score = player_stats['PTS'].values[0]
    else:
        st.warning(f"Player {player_name_input} not found.")

# Create graphs based on toggle option
if player_name:
    if toggle_option == "Points-Per-Game (PPG)":
        fig = go.Figure(data=[go.Bar(name='PPG', x=[player_name], y=[ppg_value])])
    elif toggle_option == "Rebounds-Per-Game (RPG)":
        fig = go.Figure(data=[go.Bar(name='RPG', x=[player_name], y=[rpg_value])])
    elif toggle_option == "Individual Scores":
        fig = go.Figure(data=[go.Bar(name='Individual Scores', x=[player_name], y=[individual_score])])
    elif toggle_option == "Field Goals":
        fig = go.Figure(data=[go.Bar(name='Field Goals', x=[player_name], y=[field_goal])])
    elif toggle_option == "Age of Player":
        fig = go.Figure(data=[go.Bar(name='Age', x=[player_name], y=[age])])
    elif toggle_option == "All Star Scores":
        fig = go.Figure(data=[go.Bar(name='All Star Scores', x=[player_name], y=[all_star_score])])

    # Add title and labels
    fig.update_layout(
        title=f'{toggle_option} for {player_name} in the 23-24 Season',
        xaxis_title='Player',
        yaxis_title=toggle_option,
        barmode='group'
    )

    # Display the chart
    st.plotly_chart(fig)
else:
    st.info("Please enter a valid player name.")
