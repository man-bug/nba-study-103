import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from nba_api.stats.static import players
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to get player ID by name
def get_player_id(player_name):
    nba_players = players.get_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

# Function to get player info
def get_player_info(player_id):
    try:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        return player_info.get_data_frames()[0]
    except Exception as e:
        logger.error(f"Error fetching player info: {e}")
        return None

# Function to fetch player stats
def get_player_stats(player_id, season='2023-24'):
    try:
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats = career_stats.get_data_frames()[0]
        return stats[stats['SEASON_ID'] == season]
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        return None

# Streamlit app
def main():
    st.title("NBA Player Field Goal Percentage")

    player_name_input = st.text_input("Enter a player name:")

    # Initialize variables to store player data
    field_goal_pct = None
    player_name = None

    if player_name_input:
        player_id = get_player_id(player_name_input.strip())
        if player_id:
            player_info = get_player_info(player_id)
            if player_info is not None:
                player_stats = get_player_stats(player_id)

                if player_stats is not None and not player_stats.empty:
                    player_name = player_name_input
                    field_goal_pct = player_stats['FG_PCT'].values[0]
        else:
            st.write(f"Player {player_name_input} not found.")

    # Create and display the Plotly chart for field goal percentage
    if player_name and field_goal_pct is not None:
        fig = go.Figure(data=[go.Indicator(
            mode="number+gauge",
            value=field_goal_pct * 100,
            title={'text': "Field Goal Percentage"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}})])

        st.plotly_chart(fig)
    else:
        st.write("Please enter a valid player name.")

if __name__ == "__main__":
    main()
