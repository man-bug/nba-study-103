import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players

# Fetch all NBA players
nba_players = players.get_players()

# Create a mapping from player names to player info
player_dict = {player['full_name']: player for player in nba_players}

# Function to get player ID by name
def get_player_id(player_name):
    return player_dict.get(player_name, {}).get('id')

# Streamlit input
st.title("NBA Player PPG and RPG Comparison")
player_names_input = st.text_input("Enter three player names separated by commas").split(',')

# Initialize lists to store player data
ppg_values = []
rpg_values = []
player_names = []

for player_name in player_names_input:
    player_name = player_name.strip()
    player_id = get_player_id(player_name)
    if player_id:
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats = career_stats.get_data_frames()[0]
        
        # Get the latest season stats
        latest_season_stats = stats[stats['SEASON_ID'] == '2023-24']
        
        if not latest_season_stats.empty:
            player_names.append(player_name)
            ppg_values.append(latest_season_stats['PTS'].values[0])
            rpg_values.append(latest_season_stats['REB'].values[0])
    else:
        st.warning(f"Player {player_name} not found.")

# Create a bar chart for PPG and RPG
if player_names:
    fig = go.Figure(data=[
        go.Bar(name='PPG', x=player_names, y=ppg_values),
        go.Bar(name='RPG', x=player_names, y=rpg_values)
    ])

    # Add title and labels
    fig.update_layout(
        title='Player PPG and RPG Comparison 23-24 Season',
        xaxis_title='Players',
        yaxis_title='Values',
        barmode='group'
    )

    # Display the chart
    st.plotly_chart(fig)
else:
    st.info("Please enter at least one valid player name.")
