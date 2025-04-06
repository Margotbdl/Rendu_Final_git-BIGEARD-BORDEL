import dash
from dash import dcc, html
from dash import dash_table
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import os

# -- FONCTIONS UTILES --

def group_small_categories(df, label_col, value_col, threshold_percent=0.5):
    """
    Regroupe dans une catégorie 'Other' toutes les lignes dont la valeur
    est inférieure à 'threshold_percent' % du total.
    """
    if df.empty:
        return df

    total_value = df[value_col].sum()
    if total_value == 0:
        return df

    threshold_value = (threshold_percent / 100.0) * total_value

    # Sépare les petites catégories
    small_df = df[df[value_col] < threshold_value]
    other_sum = small_df[value_col].sum()

    # Conserve les grandes catégories
    df = df[df[value_col] >= threshold_value].copy()

    # Ajoute la catégorie 'Other' si nécessaire
    if other_sum > 0:
        df = pd.concat([
            df,
            pd.DataFrame([{label_col: 'Other', value_col: other_sum}])
        ], ignore_index=True)

    return df

def make_aggregated_chart(df, chart_type, label_col, value_col, title):
    """
    Crée soit un Pie Chart (avec regroupement <0.5% en 'Other'), soit un Histogram.
    chart_type peut être 'pie' ou 'hist'.
    """
    # Si le DataFrame est vide, renvoie un graphe vide
    if df.empty:
        return px.scatter(title=f"{title}: No Data Available")

    if chart_type == 'pie':
        # Regroupe les petites catégories
        df_grouped = group_small_categories(df, label_col, value_col, threshold_percent=0.5)
        fig = px.pie(df_grouped, names=label_col, values=value_col, title=title)
    else:
        # Histogram (bar) affichant toutes les catégories
        fig = px.histogram(df, x=label_col, y=value_col, title=title)
        fig.update_layout(bargap=0.2)  # ajustement du gap entre barres si besoin

    return fig

def make_time_series(df, graph_type, x, y, title):
    """Génère un graphique de séries temporelles (line ou area).
       Si un seul point, on utilise scatter pour éviter les problèmes d'affichage."""
    if df.empty or df.shape[0] < 2:
        return px.scatter(df, x=x, y=y, title=title)
    if graph_type == 'area':
        return px.area(df, x=x, y=y, title=title)
    return px.line(df, x=x, y=y, title=title)

# -- CHEMINS DES FICHIERS --

DATA_FILE1  = os.path.join(os.path.expanduser('~/project_data/data'), 'crypto_pools_extended.csv')
DATA_FILE2  = os.path.join(os.path.expanduser('~/project_data/data'), 'crypto_pools_biggest.csv')
PRICES_FILE = os.path.join(os.path.expanduser('~/project_data/data'), 'crypto_prices.csv')

REPORT_DIR  = os.path.expanduser('~/project_data/reports')

# -- INITIALISATION DE L'APP --

app = dash.Dash(__name__)
app.title = "Crypto Pools Dashboard"

time_series_options = [
    {'label': 'Line', 'value': 'line'},
    {'label': 'Area', 'value': 'area'}
]

aggregated_options = [
    {'label': 'Pie', 'value': 'pie'},
    {'label': 'Histogram', 'value': 'hist'}
]

app.layout = html.Div([
    html.H1("Crypto Pools Dashboard"),

    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # update every 5 minutes
        n_intervals=0
    ),

    # Filtre global
    dcc.Input(
        id='crypto-filter',
        type='text',
        placeholder="Type crypto token or pool to filter (e.g., WETH)",
        value="",
        style={'marginBottom': '20px', 'width': '50%'}
    ),

    # --- Project 1 Section ---
    html.Div([
        html.H2("Project 1: Pools (<72 hours)"),

        # Choix du type de graphique pour la time series
        html.Label("Time Series Graph Type:"),
        dcc.Dropdown(
            id='p1-total-type',
            options=time_series_options,
            value='line',
            clearable=False,
            style={'width': '30%', 'marginBottom': '10px'}
        ),

        dcc.Graph(id='p1-total-volume'),

        # Choix du type de graphique pour l'agrégation (Pie ou Histogram)
        html.Label("Aggregated Volume by Token:"),
        dcc.Dropdown(
            id='p1-token-type',
            options=aggregated_options,
            value='pie',
            clearable=False,
            style={'width': '30%', 'marginBottom': '10px'}
        ),
        dcc.Graph(id='p1-token-volume')
    ], style={'border': '2px solid #ccc', 'padding': '10px', 'marginBottom': '20px'}),

    # --- Project 2 Section ---
    html.Div([
        html.H2("Project 2: Biggest Pools"),

        # Choix du type de graphique pour Biggest Pools
        html.Label("Biggest Pools:"),
        dcc.Dropdown(
            id='p2-biggest-pools-type',
            options=aggregated_options,
            value='pie',
            clearable=False,
            style={'width': '30%', 'marginBottom': '10px'}
        ),
        dcc.Graph(id='p2-biggest-pools'),

        # Choix du type de graphique pour l'agrégation (Pie ou Histogram)
        html.Label("Aggregated Volume by Token:"),
        dcc.Dropdown(
            id='p2-token-type',
            options=aggregated_options,
            value='pie',
            clearable=False,
            style={'width': '30%', 'marginBottom': '10px'}
        ),
        dcc.Graph(id='p2-token-volume'),

        html.Label("Total Pool Volume Over Time:"),
        dcc.Dropdown(
            id='p2-total-type',
            options=time_series_options,
            value='line',
            clearable=False,
            style={'width': '30%', 'marginBottom': '10px'}
        ),
        dcc.Graph(id='p2-total-volume')
    ], style={'border': '2px solid #ccc', 'padding': '10px', 'marginBottom': '20px'}),

    # --- Project 3 Section: Crypto Prices ---
    html.Div([
        html.H2("Crypto Prices"),
        html.Div(id='crypto-price-table', style={'width': '70%', 'margin': 'auto'})
    ], style={'border': '2px solid #ccc', 'padding': '10px', 'marginBottom': '20px'}),

    # --- Daily Report Section ---
    html.H2("Daily Report"),
    html.Div(id='daily-report', style={'whiteSpace': 'pre-wrap', 'border': '1px solid #ccc', 'padding': '10px'})
])

@app.callback(
    Output('p1-total-volume', 'figure'),
    Output('p1-token-volume', 'figure'),
    Output('p2-biggest-pools', 'figure'),
    Output('p2-token-volume', 'figure'),
    Output('p2-total-volume', 'figure'),
    Output('crypto-price-table', 'children'),
    Output('daily-report', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('crypto-filter', 'value'),
    Input('p1-total-type', 'value'),
    Input('p1-token-type', 'value'),
    Input('p2-biggest-pools-type', 'value'),
    Input('p2-token-type', 'value'),
    Input('p2-total-type', 'value')
)
def update_dashboard(n_intervals,
                     crypto_filter,
                     p1_total_type,
                     p1_token_type,
                     p2_biggest_pools_type,
                     p2_token_type,
                     p2_total_type):

    # --------------------
    # Project 1 Data (Pools <72h)
    try:
        df1 = pd.read_csv(DATA_FILE1, header=None, names=["timestamp", "pool", "volume"])
        df1['timestamp'] = pd.to_datetime(df1['timestamp'])
    except Exception:
        df1 = pd.DataFrame(columns=["timestamp", "pool", "volume"])
    df1['volume'] = pd.to_numeric(df1['volume'], errors='coerce')

    if crypto_filter and not df1.empty:
        df1 = df1[df1['pool'].str.contains(crypto_filter, case=False, na=False)]

    if not df1.empty:
        df1.sort_values('timestamp', inplace=True)
        df1.set_index('timestamp', inplace=True)
        df1 = df1[~df1.index.duplicated(keep='last')]
        df1 = df1.resample('1min').ffill()
        df1.reset_index(inplace=True)

        # Time series total
        df1_total = df1.groupby('timestamp')['volume'].sum().reset_index()
        fig_p1_total = make_time_series(df1_total, p1_total_type, x='timestamp', y='volume',
                                        title='Project 1: Total Pool Volume Over Time')

        # Aggregated volume by token
        token_rows1 = []
        for _, row in df1.iterrows():
            if not isinstance(row['pool'], str):
                continue
            tokens = [t.strip() for t in row['pool'].split('/')] if '/' in row['pool'] else [row['pool'].strip()]
            for token in tokens:
                token_rows1.append({'token': token, 'volume': row['volume']})

        if token_rows1:
            df_tokens1 = pd.DataFrame(token_rows1)
            token_sum1 = df_tokens1.groupby('token')['volume'].sum().reset_index()
            fig_p1_tokens = make_aggregated_chart(token_sum1, p1_token_type,
                                                  label_col='token',
                                                  value_col='volume',
                                                  title='Project 1: Aggregated Volume by Token')
        else:
            fig_p1_tokens = px.pie(title='Project 1: No Token Data Available')

    else:
        fig_p1_total = px.line(title='Project 1: No Data Available')
        fig_p1_tokens = px.pie(title='Project 1: No Data Available')

    # --------------------
    # Project 2 Data (Biggest Pools)
    try:
        df2 = pd.read_csv(DATA_FILE2, header=None, names=["timestamp", "pool", "volume"])
        df2['timestamp'] = pd.to_datetime(df2['timestamp'])
    except Exception:
        df2 = pd.DataFrame(columns=["timestamp", "pool", "volume"])
    df2['volume'] = pd.to_numeric(df2['volume'], errors='coerce')

    if crypto_filter and not df2.empty:
        df2 = df2[df2['pool'].str.contains(crypto_filter, case=False, na=False)]

    if not df2.empty:
        df2.sort_values('timestamp', inplace=True)

        # Biggest Pools: dernier enregistrement par pool
        df2_latest = df2.groupby('pool').last().reset_index()
        df2_sorted = df2_latest.sort_values('volume', ascending=False)

        fig_p2_biggest = make_aggregated_chart(df2_sorted, p2_biggest_pools_type,
                                               label_col='pool',
                                               value_col='volume',
                                               title='Project 2: Biggest Pools by Volume')

        # Aggregated Volume by Token
        token_rows2 = []
        for _, row in df2.iterrows():
            if not isinstance(row['pool'], str):
                continue
            tokens = [t.strip() for t in row['pool'].split('/')] if '/' in row['pool'] else [row['pool'].strip()]
            for token in tokens:
                token_rows2.append({'token': token, 'volume': row['volume']})

        if token_rows2:
            df_tokens2 = pd.DataFrame(token_rows2)
            token_sum2 = df_tokens2.groupby('token')['volume'].sum().reset_index()
            fig_p2_tokens = make_aggregated_chart(token_sum2, p2_token_type,
                                                  label_col='token',
                                                  value_col='volume',
                                                  title='Project 2: Aggregated Volume by Token')
        else:
            fig_p2_tokens = px.pie(title='Project 2: No Token Data Available')

        # Total Pool Volume Over Time
        df2.set_index('timestamp', inplace=True)
        df2 = df2[~df2.index.duplicated(keep='last')]
        df2 = df2.resample('1min').ffill()
        df2.reset_index(inplace=True)
        df2_total = df2.groupby('timestamp')['volume'].sum().reset_index()
        fig_p2_total = make_time_series(df2_total, p2_total_type, x='timestamp', y='volume',
                                        title='Project 2: Total Pool Volume Over Time')
    else:
        fig_p2_biggest = px.pie(title='Project 2: No Data Available')
        fig_p2_tokens  = px.pie(title='Project 2: No Data Available')
        fig_p2_total   = px.line(title='Project 2: No Data Available')

    # --------------------
    # Project 3: Crypto Prices
    try:
        df_prices = pd.read_csv(PRICES_FILE)
    except Exception:
        df_prices = pd.DataFrame(columns=["Token", "Price(USD)"])

    if crypto_filter and not df_prices.empty:
        df_prices = df_prices[df_prices['Token'].str.contains(crypto_filter, case=False, na=False)]

    df_prices['Price(USD)'] = df_prices['Price(USD)'].replace({"N/A": "unknown"})

    if df_prices.empty:
        price_table = html.Div("No Price Data Available")
    else:
        price_table = dash_table.DataTable(
            columns=[
                {"name": "Token", "id": "Token"},
                {"name": "Price (USD)", "id": "Price(USD)"}
            ],
            data=df_prices.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'border': '1px solid #ccc'},
            style_header={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'},
            page_size=20
        )

    # --------------------
    # Daily Report
    today = pd.Timestamp('today')
    today_str = today.strftime('%Y-%m-%d')
    today_report_path = os.path.join(REPORT_DIR, f"daily_report_{today_str}.txt")
    
    if os.path.exists(today_report_path):
        with open(today_report_path, 'r') as f:
            report_text = f.read()
        report_text = f"Daily Report for {today_str}\n\n" + report_text
    else:
        # Si le rapport du jour n'existe pas, on tente de récupérer celui d'hier
        yesterday = today - pd.Timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        yesterday_report_path = os.path.join(REPORT_DIR, f"daily_report_{yesterday_str}.txt")
        if os.path.exists(yesterday_report_path):
            with open(yesterday_report_path, 'r') as f:
                report_text = f.read()
            report_text = (f"No report available yet for {today_str} (before 20h).\n"
                           f"Showing yesterday's report ({yesterday_str}):\n\n" + report_text)
        else:
            report_text = f"No report available for today ({today_str}) or yesterday ({yesterday_str})."

    return (
        fig_p1_total,
        fig_p1_tokens,
        fig_p2_biggest,
        fig_p2_tokens,
        fig_p2_total,
        price_table,
        report_text
    )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
