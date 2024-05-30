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
    st.title("NBA Player Statistics Viewer")

    player_name_input = st.text_input("Enter a player name:")
    stat_options = ['Field Goal Percentage', 'Points Per Game', 'Assists Per Game', 'Rebounds Per Game', 'Steals Per Game', 'Blocks Per Game']
    selected_stats = st.multiselect("Select stats to display:", stat_options)

    # Mapping stat options to corresponding DataFrame columns
    stat_mapping = {
        'Field Goal Percentage': 'FG_PCT',
        'Points Per Game': 'PTS',
        'Assists Per Game': 'AST',
        'Rebounds Per Game': 'REB',
        'Steals Per Game': 'STL',
        'Blocks Per Game': 'BLK'
    }

    # Initialize variables to store player data
    player_name = None

    if player_name_input:
        player_id = get_player_id(player_name_input.strip())
        if player_id:
            player_info = get_player_info(player_id)
            if player_info is not None:
                player_stats = get_player_stats(player_id)

                if player_stats is not None and not player_stats.empty:
                    player_name = player_name_input
                    for selected_stat in selected_stats:
                        stat_column = stat_mapping[selected_stat]
                        stat_value = player_stats[stat_column].values[0]
                        fig = go.Figure(data=[go.Box(y=player_stats[stat_column], name=selected_stat)])
                        fig.update_layout(title=f"{selected_stat} Distribution for {player_name}")
                        st.plotly_chart(fig)
        else:
            st.write(f"Player {player_name_input} not found.")

    else:
        st.write("Please enter a valid player name.")

if __name__ == "__main__":
    main()

