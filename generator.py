import json, os, random, time
from datetime import datetime

output_dir = "data/stream"
os.makedirs(output_dir, exist_ok=True)

SOCCER_TEAMS = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Liverpool", "Luton Town", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Sheffield United",
    "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers", "Czarni Jaslo"
]

BOOKMAKERS = ["Bet365", "Unibet", "Pinnacle", "Betway", "Ladbrokes", "Betclick"]

def generate_soccer_event():
    t1, t2 = random.sample(SOCCER_TEAMS, 2)
    event_name = f"{t1} vs {t2}"
    timestamp = datetime.utcnow().isoformat()

    records = []
    for bookmaker in BOOKMAKERS:
        record = {
            "sport": "soccer_epl",
            "event_name": event_name,
            "bookmaker": bookmaker,
            "home_odds": round(random.uniform(1.4, 3.5), 2),
            "away_odds": round(random.uniform(1.8, 4.5), 2),
            "draw_odds": round(random.uniform(3.0, 6.0), 2),
            "timestamp": timestamp
        }
        records.append(record)
    return records

while True:
    batch = []
    for _ in range(4):  # dokładnie 4 mecze
        batch.extend(generate_soccer_event())

    filename = f"{output_dir}/odds_{int(time.time())}.json"
    with open(filename, "w") as f:
        for record in batch:
            f.write(json.dumps(record) + "\n")

    print(f"Wrote: {filename} ({len(batch)} records)")
    time.sleep(5)
