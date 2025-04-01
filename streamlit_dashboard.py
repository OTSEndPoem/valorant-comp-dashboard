import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Valorant Map-wise Composition Win Rates", layout="wide")
st.markdown("""
    <style>
    body { background-color: #0f172a; color: #f8fafc; }
    h1 { color: #f43f5e; text-align: center; font-family: 'Inter'; }
    </style>
""", unsafe_allow_html=True)

st.title("Valorant Scrim Dashboard")

# Load data
raw_df = pd.read_csv("form.csv")
raw_df = raw_df[['Column 1', 'Agent', 'Result']].dropna().reset_index(drop=True)

# Prepare tab layout
tabs = st.tabs(["📊 Overview", "🧩 Map Composition Win Rates"])

# ----------------------
# 📊 OVERVIEW TAB
# ----------------------
with tabs[0]:
    st.subheader("Map Overview: Total Games, Wins, Draws, Losses, Win Rate")

    # Get only clean 5-player blocks
    team_rows = []
    for i in range(0, len(raw_df) - 4, 5):
        block = raw_df.iloc[i:i+5]
        if len(block) == 5 and block['Column 1'].nunique() == 1 and block['Result'].nunique() == 1:
            team_rows.append({
                'Map': block['Column 1'].iloc[0],
                'Result': block['Result'].iloc[0].lower()
            })

    team_df = pd.DataFrame(team_rows)
    if not team_df.empty:
        summary = team_df.groupby('Map').agg(
            Games=('Result', 'count'),
            Wins=('Result', lambda x: (x == 'win').sum()),
            Draws=('Result', lambda x: (x == 'draw').sum()),
            Losses=('Result', lambda x: (x == 'loss').sum())
        ).reset_index()
        summary['Win Rate'] = summary['Wins'] / summary['Games']
        st.dataframe(summary.sort_values(by='Map'), use_container_width=True)
    else:
        st.warning("No valid 5-player team data found to build overview.")

# ----------------------
# 🧩 MAP COMPOSITION TAB
# ----------------------
with tabs[1]:
    # Get all valid maps from clean 5-player blocks
    valid_maps = []
    for i in range(0, len(raw_df) - 4, 5):
        block = raw_df.iloc[i:i+5]
        if len(block) == 5 and block['Column 1'].nunique() == 1 and block['Result'].nunique() == 1:
            valid_maps.append(block['Column 1'].iloc[0])

    valid_maps = sorted(set(valid_maps))
    selected_map = st.selectbox("Select a map:", valid_maps)

    teams = []
    for i in range(0, len(raw_df) - 4, 5):
        block = raw_df.iloc[i:i+5]
        if (
            len(block) == 5 and
            block['Column 1'].nunique() == 1 and
            block['Result'].nunique() == 1 and
            block['Column 1'].iloc[0] == selected_map
        ):
            agents = tuple(sorted(block['Agent'].tolist()))
            teams.append({
                'Composition': agents,
                'Result': block['Result'].iloc[0]
            })

    df = pd.DataFrame(teams)
    if not df.empty:
        df['Win'] = df['Result'].apply(lambda x: 1 if x.lower() == 'win' else 0)
        df['Draw'] = df['Result'].apply(lambda x: 1 if x.lower() == 'draw' else 0)
        df['Loss'] = df['Result'].apply(lambda x: 1 if x.lower() == 'loss' else 0)
        df['Game'] = 1

        grouped = df.groupby('Composition').agg(
            games=('Game', 'sum'),
            wins=('Win', 'sum'),
            draws=('Draw', 'sum'),
            losses=('Loss', 'sum')
        ).reset_index()

        grouped['Win Rate'] = grouped['wins'] / grouped['games']
        grouped['Comp String'] = grouped['Composition'].apply(lambda x: '-'.join(x))
        grouped = grouped.sort_values(by='Win Rate', ascending=False).head(15)

        fig = px.bar(
            grouped,
            x='Win Rate',
            y='Comp String',
            text=grouped.apply(
                lambda row: f"{row['Win Rate']:.2%} ({row['wins']}W-{row['losses']}L-{row['draws']}D / {row['games']} games)",
                axis=1
            ),
            orientation='h',
            title=f'Top Compositions on {selected_map}',
            labels={'Win Rate': 'Win Rate', 'Comp String': 'Agent Composition'},
            color='Win Rate',
            color_continuous_scale='reds'
        )
        fig.update_traces(textposition='outside', marker_line_color='#1e293b', marker_line_width=1.5)
        fig.update_layout(
            plot_bgcolor='#0f172a',
            paper_bgcolor='#0f172a',
            font=dict(color='#f8fafc'),
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No valid compositions found for {selected_map}")
