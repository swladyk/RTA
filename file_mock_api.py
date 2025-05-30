import os
import json
from glob import glob


class FileMockOddsAPI:
    """Symulowane API — wczytuje dane z najnowszego pliku .json"""
    

    def __init__(self, folder="data/stream"):
        self.folder = folder

    async def get_odds(self, sport):
        from producer import SimpleOdds
        if sport != "soccer_epl":
            return []

        # Znajdź najnowszy plik
        files = sorted(glob(os.path.join(self.folder, "*.json")), reverse=True)
        if not files:
            return []

        latest_file = files[0]
        odds_list = []

        with open(latest_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("sport") != "soccer_epl":
                        continue

                    odds = SimpleOdds(
                        sport=data["sport"],
                        event_name=data["event_name"],
                        bookmaker=data["bookmaker"],
                        home_odds=float(data["home_odds"]),
                        away_odds=float(data["away_odds"]),
                        draw_odds=float(data["draw_odds"]),
                        timestamp=data["timestamp"]
                    )
                    odds_list.append(odds)
                except Exception as e:
                    print(f"Error parsing line: {e}")

        return odds_list
