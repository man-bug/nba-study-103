import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from nba_api.stats.static import players
import logging
import requests
from PIL import Image
from io import BytesIO

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

# Function to fetch and display player headshot
def display_player_headshot(player_id, player_name):
    url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption=player_name, use_column_width=False)
    else:
        st.write(f"Could not retrieve headshot for {player_name}.")

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
                    display_player_headshot(player_id, player_name)
                    for selected_stat in selected_stats:
                        stat_column = stat_mapping[selected_stat]
                        stat_value = player_stats[stat_column].values[0]
                        fig = go.Figure(data=[go.Indicator(
                            mode="number+gauge",
                            value=stat_value if selected_stat != 'Field Goal Percentage' else stat_value * 100,
                            title={'text': selected_stat},
                            gauge={'axis': {'range': [None, 100 if selected_stat == 'Field Goal Percentage' else max(stat_value, 50)]},
                                   'bar': {'color': "darkblue"},
                                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}})])
                        st.plotly_chart(fig)
        else:
            st.write(f"Player {player_name_input} not found.")

    else:
        st.write("Please enter a valid player name.")

if __name__ == "__main__":
    main()
