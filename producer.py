"""
Simplified data producer for arbitrage betting
Fetches odds from API and stores in database + Kafka
"""
import asyncio
import aiohttp
import json
import sqlite3
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from kafka import KafkaProducer
from config import *

#dodanie fałszywego API z osobnego pliku


# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SimpleOdds:
    """Simple odds data structure"""
    sport: str
    event_name: str
    bookmaker: str
    home_odds: float
    away_odds: float
    draw_odds: float
    timestamp: str

class SimpleDatabase:
    """Simple SQLite database for storing odds"""
    
    def __init__(self, db_file):
        self.db_file = db_file
        self.setup_database()
    
    def setup_database(self):
        """Create database table if it doesn't exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT,
                event_name TEXT,
                bookmaker TEXT,
                home_odds REAL,
                away_odds REAL,
                draw_odds REAL,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database ready: {self.db_file}")
    
    def save_odds(self, odds_data):
        """Save odds to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for odds in odds_data:
            cursor.execute('''
                INSERT INTO odds (sport, event_name, bookmaker, home_odds, away_odds, draw_odds, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                odds.sport,
                odds.event_name,
                odds.bookmaker,
                odds.home_odds,
                odds.away_odds,
                odds.draw_odds,
                odds.timestamp
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(odds_data)} odds records to database")

class SimpleOddsAPI:
    
    """Simple API client for The Odds API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    async def get_odds(self, sport):
        """Get odds for a sport"""
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": "us,uk,eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_odds(data, sport)
                    else:
                        logger.error(f"API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching odds: {e}")
                return []
    
    def parse_odds(self, data, sport):
        """Parse API response into simple odds"""
        odds_list = []
        timestamp = datetime.now().isoformat()
        
        for event in data:
            event_name = f"{event.get('home_team')} vs {event.get('away_team')}"
            
            for bookmaker in event.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title")
                
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "h2h":
                        outcomes = market.get("outcomes", [])
                        
                        home_odds = 0
                        away_odds = 0
                        draw_odds = 0
                        
                        for outcome in outcomes:
                            name = outcome.get("name")
                            price = outcome.get("price", 0)
                            
                            if name == event.get('home_team'):
                                home_odds = price
                            elif name == event.get('away_team'):
                                away_odds = price
                            elif name == "Draw":
                                draw_odds = price
                        
                        # Only add if we have valid odds
                        if home_odds > 0 and away_odds > 0:
                            odds = SimpleOdds(
                                sport=sport,
                                event_name=event_name,
                                bookmaker=bookmaker_name,
                                home_odds=home_odds,
                                away_odds=away_odds,
                                draw_odds=draw_odds,
                                timestamp=timestamp
                            )
                            odds_list.append(odds)
        
        return odds_list

class SimpleProducer:
    """Simple producer that fetches odds and stores them"""
    
    def __init__(self):
        from file_mock_api import FileMockOddsAPI
        #self.api = SimpleOddsAPI(API_KEY)
        self.api = FileMockOddsAPI() #zmiana poboru danych z API na fałszywe API które pobiera dane z generatora
        self.database = SimpleDatabase(DATABASE_FILE)
        
        # Try to connect to Kafka (optional)
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_SERVER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.kafka_enabled = True
            logger.info("Kafka connected")
        except Exception as e:
            logger.warning(f"Kafka not available: {e}")
            self.kafka_enabled = False
    
    async def fetch_and_store(self):
        from file_mock_api import FileMockOddsAPI
        """Fetch odds and store in database + Kafka"""
        logger.info("Fetching odds...")
        
        all_odds = []
        
        for sport in SPORTS_TO_MONITOR:
            logger.info(f"Getting odds for {sport}")
            odds_data = await self.api.get_odds(sport)
            all_odds.extend(odds_data)
            logger.info(f"Found {len(odds_data)} odds for {sport}")
        
        if all_odds:
            # Save to database
            self.database.save_odds(all_odds)
            
            # Send to Kafka if available
            if self.kafka_enabled:
                for odds in all_odds:
                    try:
                        self.kafka_producer.send('odds_data', asdict(odds))
                    except Exception as e:
                        logger.error(f"Kafka send error: {e}")
                
                if self.kafka_enabled:
                    self.kafka_producer.flush()
                    logger.info("Sent to Kafka")
        
        logger.info(f"Total odds collected: {len(all_odds)}")
        return len(all_odds)
    
    async def run(self):
        """Main loop"""
        logger.info("Starting simple arbitrage data collector")
        logger.info(f"Monitoring sports: {SPORTS_TO_MONITOR}")
        logger.info(f"Fetch interval: {FETCH_INTERVAL} seconds")
        
        while True:
            try:
                count = await self.fetch_and_store()
                logger.info(f"Waiting {FETCH_INTERVAL} seconds...")
                await asyncio.sleep(FETCH_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Stopping...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(10)  # Wait before retry

def main():
    producer = SimpleProducer()
    asyncio.run(producer.run())

if __name__ == "__main__":
    main()
