import streamlit as st
import plotly.graph_objects as go
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, shotchartdetail, leagueleaders
from nba_api.stats.static import players, teams
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO

# Constants
DEFAULT_SEASON = '2024-25'

# --- Utility Functions ---

def get_player_id(player_name):
    nba_players = players.get_active_players()
    player_dict = {player['full_name']: player for player in nba_players}
    return player_dict.get(player_name, {}).get('id')

@st.cache_data
def get_player_stats(player_id, season=DEFAULT_SEASON):
    try:
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        df = gamelog.get_data_frames()[0]
        return (df, None) if not df.empty else (None, "No games played in the selected season.")
    except Exception as e:
        return None, str(e)

def train_random_forest(data):
    data['GameNumber'] = np.arange(len(data)) + 1
    features = ['GameNumber', 'FGM', 'FGA', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    X = data[features]
    y = data['PTS']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    mse = mean_squared_error(y_test, model.predict(X_test))
    return model, mse

def predict_next_game(model, data):
    next_input = {
        'GameNumber': data['GameNumber'].max() + 1,
        'FGM': data['FGM'].mean(),
        'FGA': data['FGA'].mean(),
        'REB': data['REB'].mean(),
        'AST': data['AST'].mean(),
        'STL': data['STL'].mean(),
        'BLK': data['BLK'].mean(),
        'TOV': data['TOV'].mean()
    }
    prediction = model.predict(pd.DataFrame([next_input]))
    return prediction[0]

def display_player_headshot(player_id, player_name):
    url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption=player_name, use_container_width=True)
    else:
        st.write(f"Could not retrieve headshot for {player_name}.")

def get_player_team(player_id):
    try:
        df = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
        if not df.empty:
            team_id = df['TEAM_ID'].iloc[0]
            team = teams.find_team_name_by_id(team_id)
            return team['full_name'] if team else "Unknown Team"
    except:
        pass
    return "Unknown Team"

def plot_shot_chart(player_id, player_name, season=DEFAULT_SEASON):
    try:
        chart = shotchartdetail.ShotChartDetail(
            team_id=0, player_id=player_id,
            season_nullable=season, season_type_all_star='Regular Season',
            context_measure_simple='FGA'
        )
        df = chart.get_data_frames()[0]

        fig = go.Figure()
        for made in [1, 0]:
            subset = df[df['SHOT_MADE_FLAG'] == made]
            fig.add_trace(go.Scatter(
                x=subset['LOC_X'], y=subset['LOC_Y'],
                mode='markers',
                marker=dict(color='green' if made else 'red'),
                name='Made' if made else 'Missed'
            ))

        fig.update_layout(
            title=f'Shot Chart for {player_name} ({season})',
            xaxis_title='Court Length', yaxis_title='Court Width'
        )
        st.plotly_chart(fig)
    except Exception as e:
        st.write(f"Shot chart error: {e}")

def plot_spider_chart(stats, player_name):
    categories = ['Points', 'Assists', 'Rebounds', 'Steals', 'Blocks', 'Turnovers']
    values = [
        stats['PTS'].mean(), stats['AST'].mean(), stats['REB'].mean(),
        stats['STL'].mean(), stats['BLK'].mean(), stats['TOV'].mean()
    ]
    fig = go.Figure(data=go.Scatterpolar(
        r=values + values[:1],
        theta=categories + categories[:1],
        fill='toself', name=player_name
    ))
    fig.update_layout(
        title=f"Spider Chart of Key Stats for {player_name}",
        polar=dict(radialaxis=dict(visible=True)), showlegend=True
    )
    st.plotly_chart(fig)

def get_top_league_players(category, season=DEFAULT_SEASON):
    try:
        leaders = leagueleaders.LeagueLeaders(
            stat_category_abbreviation=category,
            season=season, season_type_all_star='Regular Season'
        )
        df = leaders.get_data_frames()[0].head(10)
        if category in ['PTS', 'AST', 'REB', 'STL', 'BLK']:
            df[category] = df[category] / df['GP']
        elif category == 'FG_PCT':
            df[category] *= 100
        return df[['PLAYER', 'TEAM', category]]
    except:
        return None

# --- Main App ---

def main():
    st.title("🏀 NBA Player Performance Prediction - 2024-2025")

    nba_players = players.get_active_players()
    player_names = sorted([p['full_name'] for p in nba_players])
    selected_player = st.selectbox("Select a player to predict performance:", player_names)

    if not selected_player:
        return

    player_id = get_player_id(selected_player)
    if not player_id:
        st.warning(f"Player {selected_player} not found.")
        return

    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
    if player_info.empty:
        st.warning("Could not load player information.")
        return

    gamelog_df, error = get_player_stats(player_id)
    if gamelog_df is None:
        st.error(f"Error fetching stats: {error}")
        return

    if len(gamelog_df) < 10:
        st.warning("Not enough data to train model.")
        return

    team_name = get_player_team(player_id)
    st.success(f"{selected_player} will be playing for **{team_name}** in {DEFAULT_SEASON}.")

    model, mse = train_random_forest(gamelog_df)
    st.metric("Model Mean Squared Error", f"{mse:.2f}")

    predicted_pts = predict_next_game(model, gamelog_df)
    st.metric("Predicted Points for Next Game", f"{predicted_pts:.2f}")

    display_player_headshot(player_id, selected_player)

    # Visualizations
    st.subheader("📊 Game Performance")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=gamelog_df['GameNumber'], y=gamelog_df['PTS'], mode='lines+markers', name='Points'))
    fig.update_layout(title='Game-by-Game Scoring', xaxis_title='Game Number', yaxis_title='Points')
    st.plotly_chart(fig)

    st.subheader("🎯 Shot Chart")
    plot_shot_chart(player_id, selected_player)

    st.subheader("🕸️ Key Stats Spider Chart")
    plot_spider_chart(gamelog_df, selected_player)

    st.subheader("📈 Field Goal % Over Time")
    gamelog_df['FG%'] = (gamelog_df['FGM'] / gamelog_df['FGA']) * 100
    fig_fg = go.Figure()
    fig_fg.add_trace(go.Scatter(x=gamelog_df['GameNumber'], y=gamelog_df['FG%'], mode='lines+markers'))
    fig_fg.update_layout(title='Field Goal % Over Time', xaxis_title='Game', yaxis_title='FG%')
    st.plotly_chart(fig_fg)

    st.subheader("📊 Avg Points, Assists, Rebounds")
    comp_fig = go.Figure()
    comp_fig.add_trace(go.Bar(
        x=['Points', 'Assists', 'Rebounds'],
        y=[gamelog_df['PTS'].mean(), gamelog_df['AST'].mean(), gamelog_df['REB'].mean()],
        name='Averages'
    ))
    comp_fig.update_layout(title='Average Performance', yaxis_title='Per Game')
    st.plotly_chart(comp_fig)

    st.subheader("🏅 League Leaders (2024-2025)")
    categories = {"PTS": "Points Per Game", "AST": "Assists Per Game", "REB": "Rebounds Per Game"}
    for cat, label in categories.items():
        st.markdown(f"**{label}**")
        top_players = get_top_league_players(cat)
        if top_players is not None:
            st.dataframe(top_players, use_container_width=True)
        else:
            st.write("Unable to load leaderboard data.")

if __name__ == "__main__":
    main()
