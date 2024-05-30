import plotly.graph_objects as go
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from nba_api.stats.static import players

# Function to get player ID by name
def get_player_id(player_name):
    nba_players = players.get_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

# Function to get player info
def get_player_info(player_id):
    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    return player_info.get_data_frames()[0]

# Function to fetch player stats
def get_player_stats(player_id, season='2023-24'):
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    stats = career_stats.get_data_frames()[0]
    return stats[stats['SEASON_ID'] == season]

# Main function
def main():
    player_name_input = input("Enter a player name: ")

    # Initialize variables to store player data
    field_goal_pct = None
    player_name = None

    if player_name_input:
        player_id = get_player_id(player_name_input.strip())
        if player_id:
            player_info = get_player_info(player_id)
            if player_info is not None:
                player_stats = get_player_stats(player_id)
                
                if not player_stats.empty:
                    player_name = player_name_input
                    field_goal_pct = player_stats['FG_PCT'].values[0]
        else:
            print(f"Player {player_name_input} not found.")

    # Create and display the Plotly chart for field goal percentage
    if player_name and field_goal_pct is not None:
        fig = go.Figure(data=[go.Indicator(
            mode="number+gauge",
            value=field_goal_pct * 100,
            title={'text': "Field Goal Percentage"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}})])

        fig.show()
    else:
        print("Please enter a valid player name.")

if __name__ == "__main__":
    main()
