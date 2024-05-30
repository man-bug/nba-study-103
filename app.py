import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo, commonteamroster
from nba_api.stats.static import players, teams
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

# Function to get team colors
def get_team_colors(team_id):
    team_info = teams.find_team_name_by_id(team_id)
    primary_color = team_info['primary_color'] if 'primary_color' in team_info else '#FFFFFF'
    secondary_color = team_info['secondary_color'] if 'secondary_color' in team_info else '#000000'
    return primary_color, secondary_color

# Function to get team roster
def get_team_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        return roster
    except Exception as e:
        logger.error(f"Error fetching team roster: {e}")
        return None

# Streamlit app
def main():
    st.title("NBA Player Statistics Viewer")

    # Dropdown for team selection
    team_names = [team['full_name'] for team in teams.get_teams()]
    selected_team = st.selectbox("Select a team:", team_names)

    if selected_team:
        team_id = next(team['id'] for team in teams.get_teams() if team['full_name'] == selected_team)
        primary_color, secondary_color = get_team_colors(team_id)

        # Set the background color
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: {primary_color};
                color: {secondary_color};
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        # Dropdown for player selection
        team_roster = get_team_roster(team_id)
        if team_roster is not None:
            team_players = team_roster['PLAYER']
            selected_player = st.selectbox("Select a player:", team_players)

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

            if selected_player:
                player_id = get_player_id(selected_player.strip())
                if player_id:
                    player_info = get_player_info(player_id)
                    if player_info is not None:
                        player_stats = get_player_stats(player_id)

                        if player_stats is not None and not player_stats.empty:
                            display_player_headshot(player_id, selected_player)
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
                    st.write(f"Player {selected_player} not found.")
        else:
            st.write("Error fetching team roster.")
    else:
        st.write("Please select a team.")

if __name__ == "__main__":
    main()
