import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import commonplayerinfo, commonteamroster, playergamelog, teamgamelog
from nba_api.stats.static import players, teams
import requests
from PIL import Image
from io import BytesIO

# Function to get player ID by name
def get_player_id(player_name):
    nba_players = players.get_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

# Function to fetch player stats
def get_player_stats(player_id, season='2023-24'):
    try:
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        gamelog_df = gamelog.get_data_frames()[0]
        if gamelog_df.empty:
            return None, "No games played in the selected season."
        ppg = gamelog_df['PTS'].mean()
        fg_percentage = (gamelog_df['FGM'].sum() / gamelog_df['FGA'].sum()) * 100
        apg = gamelog_df['AST'].mean()
        rpg = gamelog_df['REB'].mean()
        return ppg, fg_percentage, apg, rpg, None
    except Exception as e:
        return None, str(e)

# Function to fetch and display player headshot
def display_player_headshot(player_id, player_name):
    url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption=player_name, use_column_width=False)
    else:
        st.write(f"Could not retrieve headshot for {player_name}.")

# Function to get team roster
def get_team_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        return roster
    except Exception as e:
        return None

# Function to get team stats
def get_team_stats(team_id, season='2023-24'):
    try:
        team_log = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        team_log_df = team_log.get_data_frames()[0]
        if team_log_df.empty:
            return None, "No games played in the selected season."

        ppg = team_log_df['PTS'].mean()
        fg_percentage = (team_log_df['FGM'].sum() / team_log_df['FGA'].sum()) * 100
        apg = team_log_df['AST'].mean()
        rpg = team_log_df['REB'].mean()
        return ppg, fg_percentage, apg, rpg, None
    except Exception as e:
        return None, str(e)

# Function to plot bar charts
def plot_stats(player_stats, team_stats, player_name):
    categories = ['PPG', 'FG%', 'APG', 'RPG']
    player_values = player_stats
    team_values = team_stats

    fig = go.Figure(data=[
        go.Bar(name=player_name, x=categories, y=player_values),
        go.Bar(name='Team Average', x=categories, y=team_values)
    ])
    fig.update_layout(barmode='group')
    st.plotly_chart(fig)

# Streamlit app
def main():
    st.title("NBA Player Statistics Viewer")

    # Dropdown for team selection
    team_names = [team['full_name'] for team in teams.get_teams()]
    selected_team = st.selectbox("Select a team:", team_names)

    if selected_team:
        team_id = next(team['id'] for team in teams.get_teams() if team['full_name'] == selected_team)

        # Dropdown for player selection
        team_roster = get_team_roster(team_id)
        if team_roster is not None:
            team_players = team_roster['PLAYER']
            selected_player = st.selectbox("Select a player:", team_players)

            if selected_player:
                player_id = get_player_id(selected_player.strip())
                if player_id:
                    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
                    if not player_info.empty:
                        ppg, fg_percentage, apg, rpg, error = get_player_stats(player_id)
                        team_ppg_avg, team_fg_avg, team_apg_avg, team_rpg_avg, team_error = get_team_stats(team_id)

                        if ppg is not None and fg_percentage is not None and apg is not None and rpg is not None:
                            display_player_headshot(player_id, selected_player)
                            st.write(f"{selected_player}'s PPG for the 2023-24 season is: {ppg:.2f}")
                            st.write(f"{selected_player}'s FG% for the 2023-24 season is: {fg_percentage:.2f}%")
                            st.write(f"{selected_player}'s APG for the 2023-24 season is: {apg:.2f}")
                            st.write(f"{selected_player}'s RPG for the 2023-24 season is: {rpg:.2f}")

                            if team_ppg_avg is not None and team_fg_avg is not None and team_apg_avg is not None and team_rpg_avg is not None:
                                plot_stats([ppg, fg_percentage, apg, rpg], [team_ppg_avg, team_fg_avg, team_apg_avg, team_rpg_avg], selected_player)
                            else:
                                st.write(f"Error: {team_error}")
                        else:
                            st.write(f"Error: {error}")
                    else:
                        st.write("Error fetching player info.")
                else:
                    st.write(f"Player {selected_player} not found.")
        else:
            st.write("Error fetching team roster.")
    else:
        st.write("Please select a team.")

if __name__ == "__main__":
    main()
