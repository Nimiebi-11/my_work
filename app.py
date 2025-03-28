import os
import requests
import pandas as pd
import plotly.express as px
from flask import Flask, redirect, session, url_for
from dash import Dash, html, dcc, Input, Output
from sqlalchemy import create_engine
from authlib.integrations.flask_client import OAuth

# Load environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db")
COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

# Flask Setup
server = Flask(__name__)
server.secret_key = "supersecretkey"

# OAuth Setup (GitHub)
oauth = OAuth(server)
github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    client_kwargs={"scope": "user:email"},
)

# Dash Setup
app = Dash(__name__, server=server, routes_pathname_prefix="/")

# Database Setup
engine = create_engine(DATABASE_URL)

def fetch_data():
    """Fetches cryptocurrency data and stores it in the database."""
    response = requests.get(COINGECKO_API).json()
    df = pd.DataFrame(response)[["id", "symbol", "current_price", "market_cap", "total_volume"]]
    df.to_sql("crypto_data", engine, if_exists="replace", index=False)
    return df

def get_stored_data():
    """Retrieves stored data from the database."""
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM crypto_data", conn)

# Fetch initial data
fetch_data()

# Dash Layout
app.layout = html.Div([
    html.H1("Crypto Market Dashboard"),
    html.Button("Refresh Data", id="refresh-btn"),
    dcc.Graph(id="crypto-chart"),
])

# Callbacks
@app.callback(
    Output("crypto-chart", "figure"),
    Input("refresh-btn", "n_clicks")
)
def update_chart(n):
    """Fetch new data and update chart."""
    df = fetch_data()
    fig = px.bar(df, x="symbol", y="current_price", title="Crypto Prices (USD)")
    return fig

# Authentication Routes
@server.route("/login")
def login():
    return github.authorize_redirect(url_for("authorize", _external=True))

@server.route("/authorize")
def authorize():
    token = github.authorize_access_token()
    session["user"] = token
    return redirect("/")

@server.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
