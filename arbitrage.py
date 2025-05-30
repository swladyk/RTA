"""
Simple arbitrage calculator
Reads from database and finds arbitrage opportunities
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleArbitrageCalculator:
    """Simple arbitrage calculator"""
    
    def __init__(self):
        self.db_file = DATABASE_FILE
    
    def get_recent_odds(self, minutes=30):
        """Get odds from last few minutes"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Get odds from last X minutes
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)-timedelta(120)).isoformat()
        
        cursor.execute('''
            SELECT sport, event_name, bookmaker, home_odds, away_odds, draw_odds, created_at
            FROM odds 
            WHERE created_at > ?
            ORDER BY event_name, bookmaker
        ''', (cutoff_time,))
        
        odds = cursor.fetchall()
        conn.close()
        
        return odds
    
    def calculate_arbitrage_percentage(self, home_odds, away_odds, draw_odds=None):
        """Calculate arbitrage percentage"""
        if home_odds <= 1 or away_odds <= 1:
            return 0
        
        # Calculate implied probabilities
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds
        draw_prob = 1 / draw_odds if draw_odds and draw_odds > 1 else 0
        
        total_prob = home_prob + away_prob + draw_prob
        
        if total_prob >= 1.0:
            return 0  # No arbitrage
        
        # Return arbitrage percentage
        return (1 - total_prob) * 100
    
    def calculate_stakes(self, home_odds, away_odds, draw_odds=None):
        """Calculate how much to bet on each outcome"""
        if draw_odds and draw_odds > 1:
            # Three-way arbitrage (with draw)
            home_prob = 1 / home_odds
            away_prob = 1 / away_odds
            draw_prob = 1 / draw_odds
            total_prob = home_prob + away_prob + draw_prob
            
            home_stake = STAKE_AMOUNT * (home_prob / total_prob)
            away_stake = STAKE_AMOUNT * (away_prob / total_prob)
            draw_stake = STAKE_AMOUNT * (draw_prob / total_prob)
            
            return {
                'home': round(home_stake, 2),
                'away': round(away_stake, 2),
                'draw': round(draw_stake, 2)
            }
        else:
            # Two-way arbitrage (no draw)
            home_prob = 1 / home_odds
            away_prob = 1 / away_odds
            total_prob = home_prob + away_prob
            
            home_stake = STAKE_AMOUNT * (home_prob / total_prob)
            away_stake = STAKE_AMOUNT * (away_prob / total_prob)
            
            return {
                'home': round(home_stake, 2),
                'away': round(away_stake, 2),
                'draw': 0
            }
    
    def find_arbitrage_opportunities(self):
        """Find arbitrage opportunities in recent data"""
        odds_data = self.get_recent_odds()
        
        if not odds_data:
            logger.info("No recent odds data found")
            return []
        
        # Group odds by event
        events = {}
        for row in odds_data:
            sport, event_name, bookmaker, home_odds, away_odds, draw_odds, timestamp = row
            
            if event_name not in events:
                events[event_name] = []
            
            events[event_name].append({
                'sport': sport,
                'bookmaker': bookmaker,
                'home_odds': home_odds,
                'away_odds': away_odds,
                'draw_odds': draw_odds,
                'timestamp': timestamp
            })
        
        opportunities = []
        
        for event_name, bookmaker_odds in events.items():
            if len(bookmaker_odds) < 2:
                continue  # Need at least 2 bookmakers
            
            # Find best odds for each outcome
            best_home = max(bookmaker_odds, key=lambda x: x['home_odds'] or 0)
            best_away = max(bookmaker_odds, key=lambda x: x['away_odds'] or 0)
            best_draw = max(bookmaker_odds, key=lambda x: x['draw_odds'] or 0)
            
            home_odds = best_home['home_odds']
            away_odds = best_away['away_odds']
            draw_odds = best_draw['draw_odds'] if best_draw['draw_odds'] > 1 else None
            
            # Calculate arbitrage
            arb_pct = self.calculate_arbitrage_percentage(home_odds, away_odds, draw_odds)
            
            if arb_pct >= MIN_PROFIT_PERCENTAGE:
                stakes = self.calculate_stakes(home_odds, away_odds, draw_odds)
                profit = STAKE_AMOUNT * (arb_pct / 100)
                
                opportunity = {
                    'event_name': event_name,
                    'sport': best_home['sport'],
                    'arbitrage_percentage': round(arb_pct, 2),
                    'expected_profit': round(profit, 2),
                    'home_bookmaker': best_home['bookmaker'],
                    'home_odds': home_odds,
                    'home_stake': stakes['home'],
                    'away_bookmaker': best_away['bookmaker'],
                    'away_odds': away_odds,
                    'away_stake': stakes['away'],
                    'draw_bookmaker': best_draw['bookmaker'] if draw_odds else None,
                    'draw_odds': draw_odds,
                    'draw_stake': stakes['draw'] if draw_odds else 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                opportunities.append(opportunity)
        
        return opportunities
    
    def save_opportunities(self, opportunities):
        """Save arbitrage opportunities to database"""
        if not opportunities:
            return
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create opportunities table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                sport TEXT,
                arbitrage_percentage REAL,
                expected_profit REAL,
                home_bookmaker TEXT,
                home_odds REAL,
                home_stake REAL,
                away_bookmaker TEXT,
                away_odds REAL,
                away_stake REAL,
                draw_bookmaker TEXT,
                draw_odds REAL,
                draw_stake REAL,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        for opp in opportunities:
            cursor.execute('''
                INSERT INTO arbitrage_opportunities 
                (event_name, sport, arbitrage_percentage, expected_profit,
                 home_bookmaker, home_odds, home_stake,
                 away_bookmaker, away_odds, away_stake,
                 draw_bookmaker, draw_odds, draw_stake, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opp['event_name'], opp['sport'], opp['arbitrage_percentage'], opp['expected_profit'],
                opp['home_bookmaker'], opp['home_odds'], opp['home_stake'],
                opp['away_bookmaker'], opp['away_odds'], opp['away_stake'],
                opp['draw_bookmaker'], opp['draw_odds'], opp['draw_stake'], opp['timestamp']
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(opportunities)} arbitrage opportunities")
    
    def run_once(self):
        """Run arbitrage calculation once"""
        logger.info("Looking for arbitrage opportunities...")
        
        opportunities = self.find_arbitrage_opportunities()
        
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities!")
            
            for opp in opportunities:
                logger.info(f"")
                logger.info(f"EVENT: {opp['event_name']}")
                logger.info(f"PROFIT: {opp['arbitrage_percentage']}% (${opp['expected_profit']})")
                logger.info(f"HOME: Bet ${opp['home_stake']} @ {opp['home_odds']} ({opp['home_bookmaker']})")
                logger.info(f"AWAY: Bet ${opp['away_stake']} @ {opp['away_odds']} ({opp['away_bookmaker']})")
                if opp['draw_stake'] > 0:
                    logger.info(f"DRAW: Bet ${opp['draw_stake']} @ {opp['draw_odds']} ({opp['draw_bookmaker']})")
                logger.info("-" * 50)
            
            self.save_opportunities(opportunities)
        else:
            logger.info("No arbitrage opportunities found")
        
        return opportunities

def main():
    calculator = SimpleArbitrageCalculator()
    while True:
        calculator.run_once()
        from time import sleep
        sleep(5)

if __name__ == "__main__":
    main()
