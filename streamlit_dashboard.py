import streamlit as st
import pandas as pd
import plotly.express as px
from data_cleaner import clean_scrim_form

st.set_page_config(page_title="Valorant Scrim Dashboard", layout="wide")
st.markdown("""
    <style>
    body { background-color: #0f172a; color: #f8fafc; }
    h1 { color: #f43f5e; text-align: center; font-family: 'Inter'; }
    </style>
""", unsafe_allow_html=True)

st.title("Valorant Scrim Dashboard")

# Load form.csv for overview and map comps
try:
    form_df = pd.read_csv("form.csv")
    form_df = form_df[['Column 1', 'Agent', 'Result']].dropna().reset_index(drop=True)
except Exception as e:
    form_df = pd.DataFrame()
    st.warning(f"⚠️ Couldn't load form.csv: {e}")

# Load cleaned_score.csv for Round Insights
try:
    score_df = pd.read_csv("cleaned_score.csv")
except Exception as e:
    score_df = pd.DataFrame()
    st.warning(f"⚠️ Couldn't load cleaned_score.csv: {e}")

tabs = st.tabs(["📊 Overview", "🧩 Map Composition Win Rates", "📈 Round Insights"])

# 📊 OVERVIEW TAB
with tabs[0]:
    st.subheader("Map Overview: Total Games, Wins, Draws, Losses, Win Rate")

    if not form_df.empty:
        team_rows = []
        for i in range(0, len(form_df) - 4, 5):
            block = form_df.iloc[i:i+5]
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
            st.info("No valid 5-player team data found to build overview.")
    else:
        st.info("form.csv not available or empty.")

# 🧩 MAP COMPOSITION TAB
with tabs[1]:
    st.subheader("Top 5-agent Composition Win Rates by Map")
    if not form_df.empty:
        valid_maps = []
        for i in range(0, len(form_df) - 4, 5):
            block = form_df.iloc[i:i+5]
            if len(block) == 5 and block['Column 1'].nunique() == 1 and block['Result'].nunique() == 1:
                valid_maps.append(block['Column 1'].iloc[0])

        valid_maps = sorted(set(valid_maps))
        selected_map = st.selectbox("Select a map:", valid_maps)

        teams = []
        for i in range(0, len(form_df) - 4, 5):
            block = form_df.iloc[i:i+5]
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
            st.info("No valid compositions found for this map.")
    else:
        st.info("form.csv not available or empty.")

# 📈 ROUND INSIGHTS TAB
with tabs[2]:
    st.subheader("📈 Round Insights from cleaned_score.csv")
    if not score_df.empty:
        maps = sorted(score_df['Map'].dropna().unique())
        teams = sorted(score_df['Team'].dropna().unique())

        col1, col2 = st.columns(2)
        selected_map = col1.selectbox("Filter by Map", ["All"] + maps)
        selected_team = col2.selectbox("Filter by Team", ["All"] + teams)

        filtered_df = score_df.copy()
        if selected_map != "All":
            filtered_df = filtered_df[filtered_df['Map'] == selected_map]
        if selected_team != "All":
            filtered_df = filtered_df[filtered_df['Team'] == selected_team]

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("### 🔍 Summary Stats")

        agg_dict = {
            'Games': ('Outcome', 'count'),
            'Wins': ('Outcome', lambda x: (x.str.lower() == 'win').sum()),
            'Draws': ('Outcome', lambda x: (x.str.lower() == 'draw').sum()),
            'Losses': ('Outcome', lambda x: (x.str.lower() == 'loss').sum()),
            'Avg_FH_WR': ('First Half WR', 'mean'),
            'Avg_SH_WR': ('Second Half WR', 'mean'),
        }

        if 'Atk PP %' in filtered_df.columns:
            agg_dict['Atk_PP_Success'] = ('Atk PP %', lambda x: pd.to_numeric(x.str.replace('%',''), errors='coerce').mean())

        if 'Def PP %' in filtered_df.columns:
            agg_dict['Def_PP_Success'] = ('Def PP %', lambda x: pd.to_numeric(x.str.replace('%',''), errors='coerce').mean())

        summary = filtered_df.groupby('Map').agg(**agg_dict).reset_index()
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("cleaned_score.csv not found or empty.")
