import streamlit as st
import pandas as pd
from PIL import Image
import os
import plotly.express as px
from data_cleaner import clean_scrim_form
import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

st.set_page_config(page_title="Valorant Scrim Dashboard", layout="wide")
encoded_bg = get_base64_image("wallp.png")
st.markdown(f"""
    <style>
    body {{
        background-image: url("data:image/jpg;base64,{encoded_bg}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        color: #ffffff;
    }}

    .stApp {{
        background-color: rgba(0, 0, 0, 0.85);
    }}

    .block-container {{
        padding: 2rem;
        border-radius: 12px;
    }}

    h1, h2, h3, .stTabs, .stButton {{
        font-family: 'Inter', sans-serif;
        color: #FDB913;
    }}

    .stDataFrame, .stTable {{
        background-color: #1a1a1a;
    }}
    </style>
""", unsafe_allow_html=True)

st.title("Valorant Scrim Dashboard")
st.image("wolves_logo.png", width=100)


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

tabs = st.tabs(["📊 Overview", "🧩 Map Composition Win Rates", "📈 Round Insights","🔫 Pistol Insights","🔢 Player Stats"])

# 📊 OVERVIEW TAB
with tabs[0]:
    st.markdown("### 📅 Filter by Date Range")
    overview_dates = sorted(score_df['Date'].dropna().unique())
    date_col1, date_col2 = st.columns(2)
    start_date_overview = date_col1.selectbox("Start Date (Overview)", overview_dates, key="overview_start")
    end_date_overview = date_col2.selectbox("End Date (Overview)", overview_dates, index=len(overview_dates)-1, key="overview_end")

    filtered_score = score_df[(score_df['Date'] >= start_date_overview) & (score_df['Date'] <= end_date_overview)]

    st.subheader("Map Overview: Total Games, Wins, Draws, Losses, Win Rate")
    if not filtered_score.empty:
        summary = filtered_score.groupby('Map').agg(
            Games=('Outcome', 'count'),
            Wins=('Outcome', lambda x: (x.str.lower() == 'win').sum()),
            Draws=('Outcome', lambda x: (x.str.lower() == 'draw').sum()),
            Losses=('Outcome', lambda x: (x.str.lower() == 'loss').sum())
        ).reset_index()
        summary['Win Rate'] = summary['Wins'] / summary['Games']
        st.dataframe(summary.sort_values(by='Map'), use_container_width=True)
        # 📊 Map Win Rate Horizontal Bar Chart
        st.markdown("### 🗺️ Map Win Rates")

        winrate_df = summary[['Map', 'Win Rate']].dropna().copy()
        winrate_df['Win Rate %'] = winrate_df['Win Rate'] * 100
        winrate_df = winrate_df.sort_values(by='Win Rate %', ascending=False)

        fig_map_wr = px.bar(
            winrate_df,
            x='Win Rate %',
            y='Map',
            orientation='h',
            text=winrate_df['Win Rate %'].apply(lambda x: f"{x:.1f}%"),
            title="Map Win Rates",
            labels={'Win Rate %': 'Win Rate (%)', 'Map': 'Map'},
            color='Win Rate %',
            color_continuous_scale=['#ff0000', '#FDB913']
        )

        fig_map_wr.update_traces(
            textposition='outside',
            marker_line_color='#000000',
            marker_line_width=1.2
        )

        fig_map_wr.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(family='Inter', size=14, color='#FDB913'),
            title_font=dict(size=20, color='#FDB913'),
            yaxis=dict(
                tickfont=dict(color='#ffffff'),
                categoryorder='total ascending',
                gridcolor='#333333'
            ),
            xaxis=dict(
                title='Win Rate (%)',
                title_font=dict(color='#FDB913'),
                tickfont=dict(color='#ffffff'),
                gridcolor='#333333',
                range=[0, 100]
            )
        )

        st.plotly_chart(fig_map_wr, use_container_width=True)

    else:
        st.info("No scrim data in this date range.")

### --- Composition Win Rate Chart (Styled like rib.gg) ---

# This block should only be inside the Map Composition tab
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
        filtered_dates = set(score_df['Date'])
        for i in range(0, len(form_df) - 4, 5):
            block = form_df.iloc[i:i+5]
            map_match = block['Column 1'].iloc[0]
            result_match = block['Result'].iloc[0]

            if (
                len(block) == 5 and
                block['Column 1'].nunique() == 1 and
                block['Result'].nunique() == 1 and
                block['Column 1'].iloc[0] == selected_map
            ):
                match_filter = (
                    (score_df['Map'] == map_match) &
                    (score_df['Outcome'].str.lower() == result_match.lower()) &
                    (score_df['Date'].isin(filtered_dates))
                )
                if not score_df[match_filter].empty:
                    agents = tuple(sorted(block['Agent'].tolist()))
                    teams.append({
                        'Composition': agents,
                        'Result': result_match
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

            grouped['Win Rate %'] = grouped['wins'] / grouped['games'] * 100
            grouped['Comp String'] = grouped['Composition'].apply(lambda x: '-'.join(x))
            grouped = grouped.sort_values(by='Win Rate %', ascending=False).head(15)

        def get_agent_icon(agent_name):
            path = f"assets/{agent_name}.png"
            if os.path.exists(path):
                return Image.open(path)
            return None

        # Add a column with the first agent's icon
        grouped['Win Rate %'] = grouped['wins'] / grouped['games'] * 100
        grouped['Comp String'] = grouped['Composition'].apply(lambda x: '-'.join(x))
        grouped = grouped.sort_values(by='Win Rate %', ascending=False).head(15)

        # 👇 Add this directly below — no extra indentation
        grouped['First Agent'] = grouped['Composition'].apply(lambda x: x[0])
        grouped['Icon Path'] = grouped['First Agent'].apply(lambda agent: f"assets/{agent}.png" if os.path.exists(f"assets/{agent}.png") else None)

        fig_comp = px.bar(
            grouped,
            x='Win Rate %',
            y='Comp String',
            text=grouped['Win Rate %'].apply(lambda x: f"{x:.2f}%"),
            hover_data={'games': True, 'wins': True, 'losses': True, 'draws': True},
            orientation='h',
            title=f"Top Compositions on {selected_map}",
            labels={'Win Rate %': 'Win Rate (%)', 'Comp String': 'Agent Composition'},
            color_discrete_sequence=['#FDB913']
        )

        fig_comp.update_traces(
            textposition='outside',
            marker_line_color='#000000',
            marker_line_width=0.5,
            customdata=grouped[['games']].values,
            hovertemplate='%{y}<br>Win Rate: %{x:.2f}%<br>Games Played: %{customdata[0]}'
        )

        fig_comp.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#FDB913', family='Inter'),
            title_font=dict(size=20, color='#FDB913'),
            margin=dict(t=40, l=100, r=40, b=20),
            yaxis=dict(
                categoryorder='total ascending',
                tickfont=dict(color='#ffffff'),
                showgrid=False,
                showline=False,
                zeroline=False
            ),
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                visible=False
            ),
            showlegend=False
        )


        st.plotly_chart(fig_comp, use_container_width=True)


# 📈 ROUND INSIGHTS TAB
with tabs[2]:
    st.subheader("📈 Round Insights from cleaned_score.csv")
    if not score_df.empty:
        maps = sorted(score_df['Map'].dropna().unique())
        dates = sorted(score_df['Date'].dropna().unique())

        col1, col2 = st.columns(2)
        selected_map = col1.selectbox("Filter by Map", ["All"] + maps)
        start_date = col1.selectbox("Start Date", dates, key="insight_start")
        end_date = col2.selectbox("End Date", dates, index=len(dates)-1, key="insight_end")

        filtered_df = score_df.copy()
        if selected_map != "All":
            filtered_df = filtered_df[filtered_df['Map'] == selected_map]

        if start_date and end_date:
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

        # Derive Atk/Def WR based on Star Side
        def extract_wr(row, side):
            if pd.isna(row['Start']) or pd.isna(row['First Half WR']) or pd.isna(row['Second Half WR']):
                return None
            if side == 'Attack':
                return row['First Half WR'] if row['Start'] == 'Attack' else row['Second Half WR']
            elif side == 'Defence':
                return row['First Half WR'] if row['Start'] == 'Defence' else row['Second Half WR']
            return None

        filtered_df['Atk WR Derived'] = filtered_df.apply(lambda row: extract_wr(row, 'Attack'), axis=1)
        filtered_df['Def WR Derived'] = filtered_df.apply(lambda row: extract_wr(row, 'Defence'), axis=1)

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("### 🔍 Summary Stats")

        agg_dict = {
            'Games': ('Outcome', 'count'),
            'Wins': ('Outcome', lambda x: (x.str.lower() == 'win').sum()),
            'Draws': ('Outcome', lambda x: (x.str.lower() == 'draw').sum()),
            'Losses': ('Outcome', lambda x: (x.str.lower() == 'loss').sum()),
            'Avg_Atk_WR': ('Atk WR Derived', lambda x: pd.to_numeric(x.astype(str).str.replace('%','', regex=False), errors='coerce').mean()),
            'Avg_Def_WR': ('Def WR Derived', lambda x: pd.to_numeric(x.astype(str).str.replace('%','', regex=False), errors='coerce').mean()),

        }

        if 'Atk PP %' in filtered_df.columns:
            agg_dict['Atk_PP_Success'] = (
                'Atk PP %',
                lambda x: pd.to_numeric(x.fillna('0').str.replace('%', ''), errors='coerce').mean()
            )

        if 'Def PP %' in filtered_df.columns:
            agg_dict['Def_PP_Success'] = (
                'Def PP %',
                lambda x: pd.to_numeric(x.fillna('0').str.replace('%', ''), errors='coerce').mean()
            )


        summary = filtered_df.groupby('Map').agg(**agg_dict).reset_index()
        # Calculate Round Win Rate using (Atk + Def) / 2
        summary['Raw_Round_WR'] = (summary['Avg_Atk_WR'] + summary['Avg_Def_WR']) / 2
        summary['Round WR'] = summary['Raw_Round_WR'].apply(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "-")


        # Optional: Format WRs as percentages
        # Save raw numeric values for chart use (before formatting to %)
        summary['Raw_Atk_WR'] = summary['Avg_Atk_WR']
        summary['Raw_Def_WR'] = summary['Avg_Def_WR']
        summary['Raw_Round_WR'] = (summary['Raw_Atk_WR'] + summary['Raw_Def_WR']) / 2
        summary['Round WR'] = summary['Raw_Round_WR'].apply(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "-")



        summary['Avg_Atk_WR'] = summary['Avg_Atk_WR'].apply(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "-")
        summary['Avg_Def_WR'] = summary['Avg_Def_WR'].apply(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "-")
        display_cols = ['Map', 'Games', 'Wins', 'Draws', 'Losses', 'Avg_Atk_WR', 'Avg_Def_WR','Round WR']

        def highlight_win_rates(val, threshold_low=40, threshold_high=60):
            try:
                val = float(val.replace('%', ''))
            except:
                return ''
            if val >= threshold_high:
                return 'background-color: #14532d; color: white;'  # green
            elif val < threshold_low:
                return 'background-color: #7f1d1d; color: white;'  # red
            else:
                return 'background-color: #78350f; color: white;'  # amber

        styled_df = summary[display_cols].style\
            .applymap(highlight_win_rates, subset=['Avg_Atk_WR', 'Avg_Def_WR','Round WR'])\
            .set_properties(**{'text-align': 'center'})\
            .set_table_styles([{
                'selector': 'th',
                'props': [('background-color', '#1a1a1a'), ('color', '#FDB913'), ('text-align', 'center')]
            }])

        # Only show selected columns in the summary table (hide raw WRs)
        display_cols = ['Map', 'Games', 'Wins', 'Draws', 'Losses', 'Avg_Atk_WR', 'Avg_Def_WR','Round WR']
        st.dataframe(styled_df, use_container_width=True)

        # Visualize Attack vs Defense Win Rates
        # Prepare data
        plot_df = summary[['Map', 'Raw_Atk_WR', 'Raw_Def_WR']].copy()
        plot_df.rename(columns={'Raw_Atk_WR': 'Attack', 'Raw_Def_WR': 'Defense'}, inplace=True)
        plot_df['Attack'] *= 100
        plot_df['Defense'] *= 100

        # Melt for plotting
        plot_df = plot_df.melt(id_vars='Map', var_name='Side', value_name='Win Rate (%)')
        plot_df['Map'] = pd.Categorical(plot_df['Map'], categories=plot_df.groupby('Map')['Win Rate (%)'].mean().sort_values(ascending=False).index, ordered=True)

        # Wolves color map
        color_map = {
            'Attack': '#FDB913',   # Gold
            'Defense': '#ffffff'   # White
        }

        fig = px.bar(
            plot_df,
            x='Map',
            y='Win Rate (%)',
            color='Side',
            color_discrete_map=color_map,
            barmode='group',
            text=plot_df['Win Rate (%)'].apply(lambda x: f"{x:.1f}%"),
            title="Attack vs Defense Win Rates by Map"
        )

        fig.update_traces(
            textposition='outside',
            marker_line_color='#333333',
            marker_line_width=1.2,
            width=0.4
        )

        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#FDB913', family='Inter'),
            title_font=dict(color='#FDB913', size=20),
            legend_title_text='Side',
            xaxis=dict(tickangle=-25, gridcolor='#333333'),
            yaxis=dict(range=[0, 100], gridcolor='#333333')
        )

        st.plotly_chart(fig, use_container_width=True)

        #--- Post-Plant Success Rate Bar Chart ---

        if 'Atk_PP_Success' in summary.columns and 'Def_PP_Success' in summary.columns:

            st.markdown("### 📊 Post-Plant Success Rate by Map")

            label_map = {
                "Atk_PP_Success": "Post Plant",
                "Def_PP_Success": "Retakes"
            }

            sort_label = st.selectbox("Sort by", list(label_map.values()), index=0)
            sort_col = [k for k, v in label_map.items() if v == sort_label][0]
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
            ascending = sort_order == "Ascending"

            pp_df = summary[['Map', 'Atk_PP_Success', 'Def_PP_Success']].copy()
            pp_df = pp_df.fillna(0)

            pp_df['Atk_PP_Success'] = pd.to_numeric(pp_df['Atk_PP_Success'], errors='coerce')
            pp_df['Def_PP_Success'] = pd.to_numeric(pp_df['Def_PP_Success'], errors='coerce')
            if pp_df['Atk_PP_Success'].max() <= 1.0:
                pp_df['Atk_PP_Success'] *= 100
                pp_df['Def_PP_Success'] *= 100

            # Sort before renaming columns
            pp_df = pp_df.sort_values(by=sort_col, ascending=ascending)
            pp_df['Map'] = pd.Categorical(pp_df['Map'], categories=pp_df['Map'], ordered=True)

            # Rename for nicer legend labels
            pp_df.rename(columns=label_map, inplace=True)

            pp_df_long = pp_df.melt(id_vars='Map', var_name='Side', value_name='Post-Plant Success (%)')

            # Plot
            fig_pp = px.bar(
                pp_df_long,
                x='Map',
                y='Post-Plant Success (%)',
                color='Side',
                barmode='stack',
                text=pp_df_long['Post-Plant Success (%)'].apply(lambda x: f"{x:.1f}%"),
                title="Post-Plant Success Rate (Stacked Atk + Def)",
                color_discrete_map={
                    'Post Plant': '#FDB913',
                    'Retakes': '#ffffff'
                }
            )

            fig_pp.update_traces(
                textposition='inside',
                marker_line_color='#333333',
                marker_line_width=1.2
            )

            fig_pp.update_layout(
                plot_bgcolor='#000000',
                paper_bgcolor='#000000',
                font=dict(family='Inter, sans-serif', size=14, color='#FDB913'),
                title_font=dict(size=20, color='#FDB913'),
                xaxis=dict(
                    title='Map',
                    title_font=dict(size=16, color='#FDB913'),
                    tickfont=dict(size=14, color='#ffffff'),
                    tickangle=-25,
                    gridcolor='#333333'
                ),
                yaxis=dict(
                    title='Post-Plant Success (%)',
                    title_font=dict(size=16, color='#FDB913'),
                    tickfont=dict(size=14, color='#ffffff'),
                    gridcolor='#333333',
                    range=[0, 100]
                ),
                legend=dict(
                    font=dict(size=13, color='#ffffff')
                )
            )

            st.plotly_chart(fig_pp, use_container_width=True)

from datetime import datetime

from datetime import datetime

# 📊 GRAPH INSIGHTS TAB
with tabs[3]:
    st.subheader("🔫 Pistol Round Win Rate by Map")

    if not score_df.empty:
        # Ensure date column is in datetime format
        score_df['Date'] = pd.to_datetime(score_df['Date'], errors='coerce')

        # Date filter
        min_date = score_df['Date'].min()
        max_date = score_df['Date'].max()

        start_date, end_date = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        # Filter dataframe by date range
        filtered_df = score_df[(score_df['Date'] >= pd.to_datetime(start_date)) & (score_df['Date'] <= pd.to_datetime(end_date))]

        # Calculate pistol stats
        filtered_df['Total Pistols Won'] = filtered_df['First Pistol'] + filtered_df['Second Pistol']
        grouped = filtered_df.groupby('Map').agg(
            Total_Pistols_Won=('Total Pistols Won', 'sum'),
            Total_Pistols_Played=('Map', 'count')
        ).reset_index()

        grouped['Total_Pistols_Played'] *= 2  # 2 pistol rounds per map
        grouped['Pistol Win Rate (%)'] = (grouped['Total_Pistols_Won'] / grouped['Total_Pistols_Played']) * 100

        grouped = grouped.sort_values(by='Pistol Win Rate (%)', ascending=False)

        # Plotly bar chart
        fig_pistol = px.bar(
            grouped,
            x='Map',
            y='Pistol Win Rate (%)',
            text=grouped['Pistol Win Rate (%)'].apply(lambda x: f"{x:.1f}%"),
            color='Pistol Win Rate (%)',
            color_continuous_scale=['#ff0000', '#FDB913'],
            title="Pistol Win Rates by Map"
        )

        fig_pistol.update_traces(
            textposition='outside',
            marker_line_color='#000000',
            marker_line_width=1.2
        )

        fig_pistol.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(family='Inter', size=14, color='#FDB913'),
            title_font=dict(size=20, color='#FDB913'),
            xaxis=dict(tickfont=dict(color='#ffffff'), gridcolor='#333333'),
            yaxis=dict(range=[0, 100], title='Win Rate (%)', title_font=dict(color='#FDB913'), tickfont=dict(color='#ffffff'), gridcolor='#333333')
        )

        st.plotly_chart(fig_pistol, use_container_width=True)

        # --- 2nd Round Conversion Pie Charts (WW/WL and LL/LW) ---
        # --- 2nd Round Conversion Pie Charts (WW/WL and LL/LW) ---
        st.markdown("### 🍰 2nd Round Outcomes by Map")

        if 'Atk 2nd' in filtered_df.columns and 'Def 2nd' in filtered_df.columns:

             conversion_data = pd.concat([
                 filtered_df[['Map', 'Atk 2nd']].rename(columns={'Atk 2nd': 'Conversion'}),
                 filtered_df[['Map', 'Def 2nd']].rename(columns={'Def 2nd': 'Conversion'})
             ])

             map_list = conversion_data['Map'].dropna().unique()
             selected_map = st.selectbox("Select a map to view 2nd round breakdown:", sorted(map_list))

             map_conversions = conversion_data[conversion_data['Map'] == selected_map]

             col1, col2 = st.columns(2)

             with col1:
                 st.markdown("#### 🔁 After Winning Pistol (WW/WL)")
                 filtered_win = map_conversions[map_conversions['Conversion'].isin(['WW', 'WL'])]

                 if filtered_win.empty:
                     st.info("No conversion attempts found for pistol round wins on this map.")
                 else:
                     pie_data_win = filtered_win['Conversion'].value_counts(normalize=True).reset_index()
                     pie_data_win.columns = ['Conversion', 'Percentage']
                     pie_data_win['Percentage'] *= 100

                     fig_pie_win = px.pie(
                         pie_data_win,
                         names='Conversion',
                         values='Percentage',
                         title=f"Pistol Conversion - {selected_map}",
                         color='Conversion',
                         color_discrete_map={
                             'WW': '#FDB913',
                             'WL': '#666666'
                         },
                         hole=0.4
                     )

                     fig_pie_win.update_traces(
                         textinfo='label+percent',
                         marker_line_color='#000000',
                         marker_line_width=1.5
                     )

                     fig_pie_win.update_layout(
                         plot_bgcolor='#000000',
                         paper_bgcolor='#000000',
                         font=dict(family='Inter', size=14, color='#FDB913'),
                         title_font=dict(size=18, color='#FDB913'),
                         legend=dict(font=dict(color='#ffffff'))
                     )

                     st.plotly_chart(fig_pie_win, use_container_width=True)

             with col2:
                 st.markdown("#### 🔁 After Losing Pistol (LL/LW)")
                 filtered_loss = map_conversions[map_conversions['Conversion'].isin(['LL', 'LW'])]

                 if filtered_loss.empty:
                     st.info("No eco round outcomes found for pistol round losses on this map.")
                 else:
                     pie_data_loss = filtered_loss['Conversion'].value_counts(normalize=True).reset_index()
                     pie_data_loss.columns = ['Conversion', 'Percentage']
                     pie_data_loss['Percentage'] *= 100

                     fig_pie_loss = px.pie(
                         pie_data_loss,
                         names='Conversion',
                         values='Percentage',
                         title=f"Eco Round Outcomes - {selected_map}",
                         color='Conversion',
                         color_discrete_map={
                             'LL': '#444444',
                             'LW': '#3b82f6'
                         },
                         hole=0.4
                     )

                     fig_pie_loss.update_traces(
                         textinfo='label+percent',
                         marker_line_color='#000000',
                         marker_line_width=1.5
                     )

                     fig_pie_loss.update_layout(
                         plot_bgcolor='#000000',
                         paper_bgcolor='#000000',
                         font=dict(family='Inter', size=14, color='#FDB913'),
                         title_font=dict(size=18, color='#FDB913'),
                         legend=dict(font=dict(color='#ffffff'))
                     )

                     st.plotly_chart(fig_pie_loss, use_container_width=True)

    else:
         st.info("No data available for pistol or 2nd round conversion insights.")


## 🔢 PLAYER STATS TAB
with tabs[4]:
    st.subheader("🧑‍💼 Player Agent Stats")

    try:
        player_df = pd.read_csv("form.csv")
    except Exception as e:
        st.warning(f"Could not load player data: {e}")
        player_df = pd.DataFrame()

    if not player_df.empty:
        player_df['Date'] = pd.to_datetime(player_df['Date'], errors='coerce')
        player_df = player_df.dropna(subset=['Date'])

        all_players = sorted(player_df['Player'].dropna().unique())
        all_maps = sorted(player_df['Column 1'].dropna().unique())

        min_date = player_df['Date'].min().date()
        max_date = player_df['Date'].max().date()

        col1, col2 = st.columns(2)
        selected_player = col1.selectbox("Select a player:", all_players)
        start_date = col1.date_input("Start date:", min_value=min_date, max_value=max_date, value=min_date)
        end_date = col2.date_input("End date:", min_value=min_date, max_value=max_date, value=max_date)
        selected_map = col2.selectbox("Filter by Map:", ["All"] + all_maps)

        filtered = player_df[
            (player_df['Player'] == selected_player) &
            (player_df['Date'].dt.date >= start_date) &
            (player_df['Date'].dt.date <= end_date)
        ]

        if selected_map != "All":
            filtered = filtered[filtered['Column 1'] == selected_map]

        if not filtered.empty:
            agent_stats = filtered.groupby('Agent').agg(
                Rounds=('Rounds', 'sum'),
                Kills=('Kills', 'sum'),
                Deaths=('Deaths', 'sum'),
                Assists=('Assists', 'sum'),
                ACS=('ACS', 'mean'),
                FK=('FK', 'sum'),
                Plants=('Plants', 'sum')
            ).reset_index()

            agent_stats['K/D Ratio'] = agent_stats['Kills'] / agent_stats['Deaths'].replace(0, float('nan'))
            agent_stats['K+A per Round'] = (agent_stats['Kills'] + agent_stats['Assists']) / agent_stats['Rounds'].replace(0, float('nan'))

            display_df = agent_stats.round(2)[['Agent', 'Rounds', 'Kills', 'Deaths', 'Assists', 'ACS', 'FK', 'Plants', 'K/D Ratio', 'K+A per Round']]

            st.markdown(f"### 🔍 Agent Performance for {selected_player} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            st.dataframe(display_df, use_container_width=True)

        else:
            st.info("No data for this player in the selected filters.")

    else:
        st.warning("No player stats found in form.csv")


# Footer in bottom-right corner
# Full-width footer pinned to bottom
st.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #000000;
            color: #FDB913;
            text-align: center;
            font-size: 13px;
            font-family: Inter, sans-serif;
            padding: 0.5rem 0;
            opacity: 0.8;
            z-index: 9999;
        }
    </style>
    <div class="footer">
        Made by: <b>Ominous</b> | X:
        <a href="https://x.com/_SushantJha" target="_blank" style="color: #FDB913; text-decoration: none;">@_SushantJha</a>
    </div>
""", unsafe_allow_html=True)
