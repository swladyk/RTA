"""
Shared data models for the arbitrage betting project
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class SportType(Enum):
    """Enumeration of supported sports"""
    SOCCER_EPL = "soccer_epl"
    SOCCER_CHAMPIONS_LEAGUE = "soccer_uefa_champs_league"
    BASKETBALL_NBA = "basketball_nba"
    AMERICAN_FOOTBALL_NFL = "americanfootball_nfl"
    TENNIS_ATP = "tennis_atp"
    BASEBALL_MLB = "baseball_mlb"

class MarketType(Enum):
    """Enumeration of betting markets"""
    HEAD_TO_HEAD = "h2h"
    SPREADS = "spreads"
    TOTALS = "totals"

@dataclass
class OddsData:
    """Data structure for odds information"""
    sport: str
    event_id: str
    event_name: str
    commence_time: str
    bookmaker: str
    market: str
    home_team: str
    away_team: str
    home_odds: Optional[float]
    away_odds: Optional[float]
    draw_odds: Optional[float]
    timestamp: str
    api_source: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_message_key(self) -> str:
        """Generate Kafka message key"""
        return f"{self.sport}_{self.event_id}_{self.bookmaker}"

@dataclass
class ArbitrageOpportunity:
    """Data structure for arbitrage opportunities"""
    event_id: str
    event_name: str
    sport: str
    commence_time: str
    
    # Best odds for each outcome
    best_home_odds: float
    best_away_odds: float
    best_draw_odds: Optional[float]
    
    # Bookmakers offering best odds
    home_bookmaker: str
    away_bookmaker: str
    draw_bookmaker: Optional[str]
    
    # Arbitrage calculations
    arbitrage_percentage: float
    total_stake: float
    home_stake: float
    away_stake: float
    draw_stake: Optional[float]
    expected_profit: float
    
    # Metadata
    timestamp: str
    calculation_id: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_profitable(self, min_percentage: float = 2.0) -> bool:
        """Check if arbitrage opportunity is profitable"""
        return self.arbitrage_percentage >= min_percentage

@dataclass
class BookmakerOdds:
    """Odds from a specific bookmaker for an event"""
    bookmaker: str
    home_odds: Optional[float]
    away_odds: Optional[float]
    draw_odds: Optional[float]
    timestamp: str

@dataclass
class EventOdds:
    """All odds for a specific event"""
    event_id: str
    event_name: str
    sport: str
    commence_time: str
    home_team: str
    away_team: str
    bookmaker_odds: List[BookmakerOdds]
    last_updated: str
    
    def get_best_odds(self) -> Dict[str, Dict]:
        """Get best odds for each outcome"""
        best_odds = {
            'home': {'odds': 0, 'bookmaker': None},
            'away': {'odds': 0, 'bookmaker': None},
            'draw': {'odds': 0, 'bookmaker': None}
        }
        
        for bm_odds in self.bookmaker_odds:
            if bm_odds.home_odds and bm_odds.home_odds > best_odds['home']['odds']:
                best_odds['home'] = {'odds': bm_odds.home_odds, 'bookmaker': bm_odds.bookmaker}
            
            if bm_odds.away_odds and bm_odds.away_odds > best_odds['away']['odds']:
                best_odds['away'] = {'odds': bm_odds.away_odds, 'bookmaker': bm_odds.bookmaker}
            
            if bm_odds.draw_odds and bm_odds.draw_odds > best_odds['draw']['odds']:
                best_odds['draw'] = {'odds': bm_odds.draw_odds, 'bookmaker': bm_odds.bookmaker}
        
        return best_odds

def calculate_implied_probability(odds: float) -> float:
    """Calculate implied probability from decimal odds"""
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds

def calculate_arbitrage_percentage(home_odds: float, away_odds: float, 
                                 draw_odds: Optional[float] = None) -> float:
    """Calculate arbitrage percentage for given odds"""
    total_probability = calculate_implied_probability(home_odds) + \
                       calculate_implied_probability(away_odds)
    
    if draw_odds:
        total_probability += calculate_implied_probability(draw_odds)
    
    if total_probability >= 1.0:
        return 0.0  # No arbitrage opportunity
    
    return (1.0 - total_probability) * 100

def calculate_stakes(total_stake: float, home_odds: float, away_odds: float,
                    draw_odds: Optional[float] = None) -> Dict[str, float]:
    """Calculate optimal stakes for arbitrage betting"""
    home_prob = calculate_implied_probability(home_odds)
    away_prob = calculate_implied_probability(away_odds)
    
    if draw_odds:
        draw_prob = calculate_implied_probability(draw_odds)
        total_prob = home_prob + away_prob + draw_prob
        
        return {
            'home': total_stake * (home_prob / total_prob),
            'away': total_stake * (away_prob / total_prob),
            'draw': total_stake * (draw_prob / total_prob)
        }
    else:
        total_prob = home_prob + away_prob
        
        return {
            'home': total_stake * (home_prob / total_prob),
            'away': total_stake * (away_prob / total_prob),
            'draw': 0.0
        }