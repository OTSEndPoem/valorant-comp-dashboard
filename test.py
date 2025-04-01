import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load your full scrim data CSV
raw_df = pd.read_csv("form.csv")

# Drop rows without agents or results, reset index
raw_df = raw_df[['Column 1', 'Agent', 'Result']].dropna().reset_index(drop=True)

# Assign Team IDs based on intervals of 5
raw_df['Team_ID'] = raw_df.index // 5

# Group by each team of 5 players, sort agents in the composition
team_data = raw_df.groupby('Team_ID').agg({
    'Column 1': 'first',
    'Agent': lambda agents: tuple(sorted(agents.tolist())),
    'Result': 'first'
}).reset_index()

# Rename columns
team_data.rename(columns={'Column 1': 'Map', 'Agent': 'Composition'}, inplace=True)

# Compute win indicator
team_data['Win'] = team_data['Result'].apply(lambda x: 1 if x.lower() == 'win' else 0)

# Calculate win rates by map and composition
composition_win_rates = team_data.groupby(['Map', 'Composition']).agg(
    games=('Win', 'count'),
    wins=('Win', 'sum')
).reset_index()

composition_win_rates['Win Rate'] = composition_win_rates['wins'] / composition_win_rates['games']

# Convert composition tuple to readable string
composition_win_rates['Comp String'] = composition_win_rates['Composition'].apply(lambda x: '-'.join(x))

# Initialize Dash app with external stylesheet for clean font
external_stylesheets = ["https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Custom styles
app.layout = html.Div([
    html.H1("Valorant Map-wise Composition Win Rates", style={
        'fontFamily': 'Inter',
        'fontWeight': '600',
        'textAlign': 'center',
        'color': '#f43f5e',
        'padding': '10px 0'
    }),
    html.Div([
        dcc.Dropdown(
            id='map-dropdown',
            options=[{'label': m, 'value': m} for m in composition_win_rates['Map'].unique()],
            value=composition_win_rates['Map'].iloc[0],
            clearable=False,
            style={
                'fontFamily': 'Inter',
                'color': '#111827'
            }
        )
    ], style={
        'width': '50%',
        'margin': '0 auto',
        'paddingBottom': '20px'
    }),
    html.Div([
        dcc.Graph(id='winrate-graph')
    ], style={
        'padding': '0 40px'
    })
], style={
    'backgroundColor': '#0f172a',
    'color': '#f8fafc',
    'minHeight': '100vh',
    'padding': '20px'
})

@app.callback(
    Output('winrate-graph', 'figure'),
    Input('map-dropdown', 'value')
)
def update_graph(selected_map):
    filtered_df = composition_win_rates[composition_win_rates['Map'] == selected_map]
    filtered_df = filtered_df.sort_values(by='Win Rate', ascending=False).head(15)  # Top 15
    fig = px.bar(
        filtered_df,
        x='Win Rate',
        y='Comp String',
        text=filtered_df.apply(lambda row: f"{row['Win Rate']:.2%} ({row['games']} games)", axis=1),
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
        font=dict(color='#f8fafc', family='Inter'),
        yaxis={'categoryorder': 'total ascending'},
        title={
            'text': f'Top Compositions on {selected_map}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#f8fafc'}
        }
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
