import sqlite3

conn = sqlite3.connect('tornadoes.db')
cur = conn.cursor()

# STATES TABLE
cur.execute('''
CREATE TABLE IF NOT EXISTS states (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name TEXT NOT NULL
)
''')

# TORNADOES TABLE
cur.execute('''
CREATE TABLE IF NOT EXISTS tornadoes (
    tornado_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tornado_name TEXT NOT NULL,
    category TEXT NOT NULL,
    wind_speed INTEGER,
    date_occurred TEXT,
    state_id INTEGER,
    description TEXT,
    FOREIGN KEY (state_id) REFERENCES states(state_id)
)
''')

# REPORTS TABLE
cur.execute('''
CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    location TEXT NOT NULL,
    tornado_seen TEXT,
    damage_level TEXT,
    report_date TEXT
)
''')

# Insert sample states
states = [
    ('Texas',),
    ('Oklahoma',),
    ('Kansas',),
    ('Nebraska',),
    ('Alabama',)
]

cur.executemany('INSERT INTO states (state_name) VALUES (?)', states)

# Insert sample tornadoes
sample_tornadoes = [
    ('Red River Tornado', 'EF4', 190, '2024-05-01', 1, 'Major tornado across rural Texas'),
    ('Great Plains Cyclone', 'EF3', 165, '2024-04-15', 2, 'Strong tornado with hail damage'),
    ('Midwest Funnel', 'EF2', 130, '2024-03-20', 3, 'Moderate tornado causing power outages'),
    ('Nebraska Twister', 'EF5', 220, '2024-05-10', 4, 'Extremely destructive tornado event')
]

cur.executemany('''
INSERT INTO tornadoes
(tornado_name, category, wind_speed, date_occurred, state_id, description)
VALUES (?, ?, ?, ?, ?, ?)
''', sample_tornadoes)

conn.commit()
conn.close()

print('Database initialized successfully!')