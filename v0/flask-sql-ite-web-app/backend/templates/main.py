from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
import requests
from datetime import datetime

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'tornado_tracker.db')

# ============================================
# DATABASE SETUP AND HELPERS
# ============================================

def get_db():
    """Get database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with 3 related tables."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Table 1: States (locations where tornadoes occur)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            abbreviation TEXT NOT NULL UNIQUE,
            region TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 2: Tornadoes (main tornado events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tornadoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id INTEGER NOT NULL,
            date DATE NOT NULL,
            ef_rating INTEGER NOT NULL CHECK(ef_rating >= 0 AND ef_rating <= 5),
            width_yards INTEGER,
            length_miles REAL,
            fatalities INTEGER DEFAULT 0,
            injuries INTEGER DEFAULT 0,
            damage_cost REAL,
            description TEXT,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_id) REFERENCES states(id)
        )
    ''')
    
    # Table 3: Reports (user-submitted sighting reports)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tornado_id INTEGER,
            reporter_name TEXT NOT NULL,
            reporter_email TEXT NOT NULL,
            sighting_date DATE NOT NULL,
            location_description TEXT NOT NULL,
            wind_speed_estimate INTEGER,
            damage_description TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tornado_id) REFERENCES tornadoes(id)
        )
    ''')
    
    conn.commit()
    
    # Check if we need to seed data
    cursor.execute('SELECT COUNT(*) FROM states')
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
    
    conn.close()

def seed_data(conn):
    """Seed initial data into the database."""
    cursor = conn.cursor()
    
    # Seed states
    states = [
        ('Texas', 'TX', 'South'),
        ('Oklahoma', 'OK', 'South'),
        ('Kansas', 'KS', 'Midwest'),
        ('Nebraska', 'NE', 'Midwest'),
        ('Iowa', 'IA', 'Midwest'),
        ('Missouri', 'MO', 'Midwest'),
        ('Illinois', 'IL', 'Midwest'),
        ('Alabama', 'AL', 'Southeast'),
        ('Mississippi', 'MS', 'Southeast'),
        ('Arkansas', 'AR', 'South'),
        ('Tennessee', 'TN', 'Southeast'),
        ('Indiana', 'IN', 'Midwest'),
        ('Ohio', 'OH', 'Midwest'),
        ('Florida', 'FL', 'Southeast'),
        ('Georgia', 'GA', 'Southeast')
    ]
    cursor.executemany('INSERT INTO states (name, abbreviation, region) VALUES (?, ?, ?)', states)
    
    # Seed tornadoes
    tornadoes = [
        (1, '2024-04-12', 4, 880, 12.5, 3, 45, 125000000, 'Devastating tornado that struck rural communities', 'Perryton'),
        (1, '2024-05-21', 3, 400, 8.2, 0, 12, 45000000, 'Large tornado with significant structural damage', 'Amarillo'),
        (2, '2024-04-27', 5, 1200, 16.8, 8, 120, 500000000, 'Historic EF5 tornado with catastrophic damage', 'Moore'),
        (2, '2024-05-15', 3, 550, 9.1, 1, 23, 78000000, 'Strong tornado affecting multiple neighborhoods', 'Norman'),
        (3, '2024-05-20', 4, 750, 11.3, 2, 35, 95000000, 'Powerful tornado crossing open farmland', 'Wichita'),
        (3, '2024-06-01', 2, 200, 3.5, 0, 5, 12000000, 'Moderate tornado with limited damage', 'Topeka'),
        (4, '2024-05-10', 3, 450, 7.8, 0, 18, 55000000, 'Significant tornado affecting suburban areas', 'Omaha'),
        (5, '2024-06-15', 2, 180, 2.9, 0, 3, 8000000, 'Brief tornado with minor structural damage', 'Des Moines'),
        (6, '2024-05-25', 4, 680, 10.2, 4, 52, 110000000, 'Deadly tornado with widespread destruction', 'Joplin'),
        (8, '2024-04-05', 3, 520, 8.7, 2, 28, 67000000, 'Powerful tornado in tornado alley region', 'Birmingham'),
        (11, '2024-04-18', 3, 380, 6.4, 1, 15, 42000000, 'Strong tornado affecting residential areas', 'Nashville'),
        (14, '2024-06-20', 1, 100, 1.2, 0, 1, 2000000, 'Weak tornado with minimal damage', 'Tampa'),
    ]
    cursor.executemany('''
        INSERT INTO tornadoes (state_id, date, ef_rating, width_yards, length_miles, fatalities, injuries, damage_cost, description, city) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', tornadoes)
    
    # Seed some reports
    reports = [
        (3, 'John Smith', 'john.smith@email.com', '2024-04-27', 'Near I-35 and Main Street intersection', 180, 'Multiple houses destroyed, vehicles thrown', 1),
        (3, 'Maria Garcia', 'maria.g@email.com', '2024-04-27', 'West side of town near the high school', 165, 'Roof damage to school building', 1),
        (1, 'Robert Johnson', 'rjohnson@email.com', '2024-04-12', 'County Road 15, about 5 miles east of town', 150, 'Barn completely destroyed, debris field extensive', 1),
        (5, 'Sarah Williams', 'swilliams@email.com', '2024-05-20', 'Downtown area near the courthouse', 140, 'Windows blown out, trees uprooted', 1),
        (9, 'Michael Brown', 'mbrown@email.com', '2024-05-25', 'Highway 71 corridor', 175, 'Multiple businesses damaged, power lines down', 0),
    ]
    cursor.executemany('''
        INSERT INTO reports (tornado_id, reporter_name, reporter_email, sighting_date, location_description, wind_speed_estimate, damage_description, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', reports)
    
    conn.commit()

# Initialize database on startup
init_db()

# ============================================
# PAGE ROUTES (Rendered HTML Pages)
# ============================================

@app.route('/')
def home():
    """Home page with tornado statistics and recent activity."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*) FROM tornadoes')
    total_tornadoes = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(fatalities), SUM(injuries) FROM tornadoes')
    stats = cursor.fetchone()
    total_fatalities = stats[0] or 0
    total_injuries = stats[1] or 0
    
    cursor.execute('SELECT COUNT(*) FROM reports')
    total_reports = cursor.fetchone()[0]
    
    # Get recent tornadoes
    cursor.execute('''
        SELECT t.*, s.name as state_name, s.abbreviation 
        FROM tornadoes t 
        JOIN states s ON t.state_id = s.id 
        ORDER BY t.date DESC LIMIT 5
    ''')
    recent_tornadoes = cursor.fetchall()
    
    conn.close()
    
    return render_template('home.html', 
                         total_tornadoes=total_tornadoes,
                         total_fatalities=total_fatalities,
                         total_injuries=total_injuries,
                         total_reports=total_reports,
                         recent_tornadoes=recent_tornadoes)

@app.route('/tornadoes')
def tornadoes_list():
    """Browse all tornadoes with filtering."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get filter parameters
    state_filter = request.args.get('state', '')
    ef_filter = request.args.get('ef_rating', '')
    year_filter = request.args.get('year', '')
    
    # Build query with filters
    query = '''
        SELECT t.*, s.name as state_name, s.abbreviation 
        FROM tornadoes t 
        JOIN states s ON t.state_id = s.id 
        WHERE 1=1
    '''
    params = []
    
    if state_filter:
        query += ' AND s.id = ?'
        params.append(state_filter)
    if ef_filter:
        query += ' AND t.ef_rating = ?'
        params.append(ef_filter)
    if year_filter:
        query += ' AND strftime("%Y", t.date) = ?'
        params.append(year_filter)
    
    query += ' ORDER BY t.date DESC'
    
    cursor.execute(query, params)
    tornadoes = cursor.fetchall()
    
    # Get states for filter dropdown
    cursor.execute('SELECT * FROM states ORDER BY name')
    states = cursor.fetchall()
    
    # Get distinct years
    cursor.execute('SELECT DISTINCT strftime("%Y", date) as year FROM tornadoes ORDER BY year DESC')
    years = [row['year'] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('tornadoes.html', 
                         tornadoes=tornadoes, 
                         states=states,
                         years=years,
                         current_state=state_filter,
                         current_ef=ef_filter,
                         current_year=year_filter)

@app.route('/tornado/<int:tornado_id>')
def tornado_detail(tornado_id):
    """Detailed view of a single tornado."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get tornado details
    cursor.execute('''
        SELECT t.*, s.name as state_name, s.abbreviation, s.region
        FROM tornadoes t 
        JOIN states s ON t.state_id = s.id 
        WHERE t.id = ?
    ''', (tornado_id,))
    tornado = cursor.fetchone()
    
    if not tornado:
        conn.close()
        return render_template('404.html'), 404
    
    # Get related reports
    cursor.execute('''
        SELECT * FROM reports 
        WHERE tornado_id = ? 
        ORDER BY created_at DESC
    ''', (tornado_id,))
    reports = cursor.fetchall()
    
    conn.close()
    
    return render_template('tornado_detail.html', tornado=tornado, reports=reports)

@app.route('/report', methods=['GET', 'POST'])
def submit_report():
    """Form to submit a tornado sighting report."""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle form submission
        tornado_id = request.form.get('tornado_id') or None
        reporter_name = request.form.get('reporter_name')
        reporter_email = request.form.get('reporter_email')
        sighting_date = request.form.get('sighting_date')
        location_description = request.form.get('location_description')
        wind_speed_estimate = request.form.get('wind_speed_estimate') or None
        damage_description = request.form.get('damage_description')
        
        cursor.execute('''
            INSERT INTO reports (tornado_id, reporter_name, reporter_email, sighting_date, location_description, wind_speed_estimate, damage_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tornado_id, reporter_name, reporter_email, sighting_date, location_description, wind_speed_estimate, damage_description))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('report_success'))
    
    # GET request - show form
    cursor.execute('''
        SELECT t.id, t.date, t.city, s.abbreviation 
        FROM tornadoes t 
        JOIN states s ON t.state_id = s.id 
        ORDER BY t.date DESC
    ''')
    tornadoes = cursor.fetchall()
    
    conn.close()
    
    return render_template('report.html', tornadoes=tornadoes)

@app.route('/report/success')
def report_success():
    """Success page after submitting a report."""
    return render_template('report_success.html')

@app.route('/statistics')
def statistics():
    """Statistics and charts page."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tornadoes by EF rating
    cursor.execute('''
        SELECT ef_rating, COUNT(*) as count 
        FROM tornadoes 
        GROUP BY ef_rating 
        ORDER BY ef_rating
    ''')
    by_rating = cursor.fetchall()
    
    # Tornadoes by state
    cursor.execute('''
        SELECT s.name, s.abbreviation, COUNT(t.id) as count 
        FROM states s 
        LEFT JOIN tornadoes t ON s.id = t.state_id 
        GROUP BY s.id 
        HAVING count > 0
        ORDER BY count DESC
    ''')
    by_state = cursor.fetchall()
    
    # Tornadoes by month
    cursor.execute('''
        SELECT strftime("%m", date) as month, COUNT(*) as count 
        FROM tornadoes 
        GROUP BY month 
        ORDER BY month
    ''')
    by_month = cursor.fetchall()
    
    # Total damage by state
    cursor.execute('''
        SELECT s.name, SUM(t.damage_cost) as total_damage 
        FROM states s 
        JOIN tornadoes t ON s.id = t.state_id 
        GROUP BY s.id 
        ORDER BY total_damage DESC
        LIMIT 10
    ''')
    damage_by_state = cursor.fetchall()
    
    conn.close()
    
    return render_template('statistics.html', 
                         by_rating=by_rating,
                         by_state=by_state,
                         by_month=by_month,
                         damage_by_state=damage_by_state)

# ============================================
# API ROUTES (JSON responses for JavaScript)
# ============================================

@app.route('/api/tornadoes')
def api_tornadoes():
    """API endpoint to get tornadoes as JSON."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, s.name as state_name, s.abbreviation 
        FROM tornadoes t 
        JOIN states s ON t.state_id = s.id 
        ORDER BY t.date DESC
    ''')
    tornadoes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(tornadoes)

@app.route('/api/statistics')
def api_statistics():
    """API endpoint to get statistics as JSON."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get various statistics
    cursor.execute('SELECT ef_rating, COUNT(*) as count FROM tornadoes GROUP BY ef_rating ORDER BY ef_rating')
    by_rating = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT s.abbreviation, COUNT(t.id) as count 
        FROM states s 
        LEFT JOIN tornadoes t ON s.id = t.state_id 
        GROUP BY s.id
        ORDER BY count DESC
    ''')
    by_state = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'by_rating': by_rating, 'by_state': by_state})

@app.route('/api/weather/<city>')
def api_weather(city):
    """Fetch weather data from external API (Open-Meteo)."""
    try:
        # First, geocode the city using Open-Meteo's geocoding API
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geocode_url, timeout=5)
        geo_data = geo_response.json()
        
        if 'results' not in geo_data or len(geo_data['results']) == 0:
            return jsonify({'error': 'City not found'}), 404
        
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        city_name = geo_data['results'][0]['name']
        
        # Fetch weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()
        
        # Format response
        current = weather_data.get('current', {})
        daily = weather_data.get('daily', {})
        
        result = {
            'city': city_name,
            'latitude': lat,
            'longitude': lon,
            'current': {
                'temperature': current.get('temperature_2m'),
                'humidity': current.get('relative_humidity_2m'),
                'wind_speed': current.get('wind_speed_10m'),
                'wind_gusts': current.get('wind_gusts_10m'),
                'weather_code': current.get('weather_code')
            },
            'forecast': {
                'dates': daily.get('time', [])[:5],
                'max_temps': daily.get('temperature_2m_max', [])[:5],
                'min_temps': daily.get('temperature_2m_min', [])[:5],
                'precipitation_chance': daily.get('precipitation_probability_max', [])[:5]
            }
        }
        
        return jsonify(result)
        
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to fetch weather data', 'details': str(e)}), 500

@app.route('/api/reports', methods=['POST'])
def api_submit_report():
    """API endpoint to submit a report via AJAX."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO reports (tornado_id, reporter_name, reporter_email, sighting_date, location_description, wind_speed_estimate, damage_description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('tornado_id'),
        data.get('reporter_name'),
        data.get('reporter_email'),
        data.get('sighting_date'),
        data.get('location_description'),
        data.get('wind_speed_estimate'),
        data.get('damage_description')
    ))
    
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'report_id': report_id})

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
