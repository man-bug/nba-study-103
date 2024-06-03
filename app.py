import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from nba_api.stats.endpoints import commonplayerinfo, playergamelog, teamgamelog, shotchartdetail, CommonTeamRoster
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

# Function to fetch shot chart data
def get_shot_chart(player_id, season='2023-24'):
    shotchart = shotchartdetail.ShotChartDetail(
        player_id=player_id,
        team_id=0,
        context_measure_simple='FGA',
        season_nullable=season
    )
    return shotchart.get_data_frames()[0]

# Function to plot shot chart
def plot_shot_chart(df_shot_chart, player_name):
    # Using specific colors for made and missed shots
    fig = px.scatter(df_shot_chart, x='LOC_X', y='LOC_Y',
                     hover_data=['SHOT_DISTANCE', 'SHOT_MADE_FLAG'],
                     color='SHOT_MADE_FLAG',  # This column indicates if the shot was made or missed
                     color_discrete_map={0: 'red', 1: 'green'},  # Mapping 0 to red (missed) and 1 to green (made)
                     labels={'SHOT_MADE_FLAG': 'Shot Made Flag'})
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(title=f"{player_name}'s Shot Chart",
                      xaxis_showgrid=False, yaxis_showgrid=False,
                      xaxis_zeroline=False, yaxis_zeroline=False,
                      xaxis_visible=False, yaxis_visible=False)
    st.plotly_chart(fig)

# Function to get team roster
def get_team_roster(team_id):
    try:
        roster = CommonTeamRoster(team_id=team_id)
        roster_df = roster.common_team_roster.get_data_frame()
        return roster_df
    except Exception as e:
        st.error("Failed to fetch team roster: " + str(e))
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

# Function to compare two players
def compare_players(player1_stats, player2_stats, player1_name, player2_name):
    categories = ['PPG', 'FG%', 'APG', 'RPG']
    player1_values = [player1_stats[i] for i in range(4)]
    player2_values = [player2_stats[i] for i in range(4)]

    fig = go.Figure(data=[
        go.Bar(name=player1_name, x=categories, y=player1_values),
        go.Bar(name=player2_name, x=categories, y=player2_values)
    ])
    fig.update_layout(barmode='group', title="Player Comparison")
    st.plotly_chart(fig)



# Main function of the app
def main():
    st.title("NBA Player Statistics Viewer")

    # Dropdown for team selection
    team_names = [team['full_name'] for team in teams.get_teams()]
    selected_team = st.selectbox("Select a team:", team_names)

    if selected_team:
        team_id = next(team['id'] for team in teams.get_teams() if team['full_name'] == selected_team)
        team_roster = get_team_roster(team_id)
        if team_roster is not None:
            team_players = team_roster['PLAYER'].tolist()
            selected_player = st.selectbox("Select a player:", team_players)

            if selected_player:
                player_id = get_player_id(selected_player.strip())
                if player_id:
                    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
                    if not player_info.empty:
                        ppg, fg_percentage, apg, rpg, error = get_player_stats(player_id)
                        if ppg is not None:
                            shot_chart_df = get_shot_chart(player_id)
                            plot_shot_chart(shot_chart_df, selected_player)

                            st.write(f"Selected player: {selected_player}")
                            display_player_headshot(player_id, selected_player)

                            st.write(f"{selected_player}'s PPG: {ppg:.2f}")
                            st.write(f"{selected_player}'s FG%: {fg_percentage:.2f}%")
                            st.write(f"{selected_player}'s APG: {apg:.2f}")
                            st.write(f"{selected_player}'s RPG: {rpg:.2f}")

                            compare = st.checkbox("Compare with another player")
                            compare_team = st.checkbox("Compare with team average")
                            if compare_team:
                                team_ppg_avg, team_fg_avg, team_apg_avg, team_rpg_avg, team_error = get_team_stats(team_id)
                                if team_ppg_avg is not None:
                                    compare_players([ppg, fg_percentage, apg, rpg], [team_ppg_avg, team_fg_avg, team_apg_avg, team_rpg_avg], selected_player, "Team Average")

                            if compare:
                                compare_player = st.selectbox("Select another player for comparison:", [p for p in team_players if p != selected_player])
                                compare_player_id = get_player_id(compare_player.strip())
                                if compare_player_id:
                                    compare_ppg, compare_fg_percentage, compare_apg, compare_rpg, compare_error = get_player_stats(compare_player_id)
                                    if compare_ppg is not None:
                                        st.write(f"Comparison player: {compare_player}")
                                        display_player_headshot(compare_player_id, compare_player)

                                        compare_shot_chart_df = get_shot_chart(compare_player_id)
                                        plot_shot_chart(compare_shot_chart_df, compare_player)

                                        compare_players([ppg, fg_percentage, apg, rpg], [compare_ppg, compare_fg_percentage, compare_apg, compare_rpg], selected_player, compare_player)
                                    else:
                                        st.write(f"Error comparing players: {compare_error}")
                        else:
                            st.write(f"Error fetching player stats: {error}")
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
