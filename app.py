from flask import Flask, render_template, request, redirect
import sqlite3
import requests

app = Flask(__name__)

DATABASE = 'tornadoes.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/ef-scale')
def ef_scale():
    return render_template('ef_scale.html')

@app.route('/')
def home():
    # NOAA weather alerts API
    api_url = 'https://api.weather.gov/alerts/active'

    alerts = []

    try:
        response = requests.get(api_url)
        data = response.json()

        alerts = data['features'][:5]

    except:
        alerts = []

    return render_template('home.html', alerts=alerts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/tornadoes')
def tornadoes():
    conn = get_db_connection()

    tornado_data = conn.execute('''
    SELECT tornadoes.*, states.state_name
    FROM tornadoes
    JOIN states ON tornadoes.state_id = states.state_id
    ORDER BY wind_speed DESC
    ''').fetchall()

    conn.close()

    return render_template('tornadoes.html', tornadoes=tornado_data)

@app.route('/how-tornadoes-form')
def tornado_formation():
    return render_template('tornado_formation.html')

@app.route('/stats')
def stats():
    conn = get_db_connection()

    total_tornadoes = conn.execute(
        'SELECT COUNT(*) FROM tornadoes'
    ).fetchone()[0]

    avg_speed = conn.execute(
        'SELECT AVG(wind_speed) FROM tornadoes'
    ).fetchone()[0]

    strongest = conn.execute('''
    SELECT tornado_name, wind_speed
    FROM tornadoes
    ORDER BY wind_speed DESC
    LIMIT 1
    ''').fetchone()

    conn.close()

    return render_template(
        'stats.html',
        total_tornadoes=total_tornadoes,
        avg_speed=round(avg_speed, 2),
        strongest=strongest
    )


app.run(debug=True)