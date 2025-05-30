"""
Simple alert system for arbitrage opportunities
Sends alerts via console, file, and optionally email
"""
import os
import sqlite3
import json
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from config import *

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAlertSystem:
    """Simple alert system for arbitrage opportunities"""
    
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.min_profit = MIN_PROFIT_PERCENTAGE
        
        # Alert settings - can be configured
        self.console_alerts = True
        self.file_alerts = True
        
        # Check if email configuration is available in environment
        smtp_server = os.getenv('SMTP_SERVER')
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        alert_email_to = os.getenv('ALERT_EMAIL_TO')
        
        self.email_alerts = all([smtp_server, email_user, email_password, alert_email_to])
        
        # Email settings from environment variables
        self.email_settings = {
            'smtp_server': smtp_server or 'smtp.gmail.com',
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': email_user,
            'sender_password': email_password,
            'recipient_email': alert_email_to
        }
        
        if self.email_alerts:
            logger.info("Email alerts enabled")
        else:
            logger.info("Email alerts disabled (configure SMTP_SERVER, EMAIL_USER, EMAIL_PASSWORD, ALERT_EMAIL_TO in .env to enable)")
    
    def get_new_opportunities(self, minutes=5):
        """Get opportunities from last few minutes"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        cursor.execute('''
            SELECT * FROM arbitrage_opportunities 
            WHERE timestamp > ? AND arbitrage_percentage >= ?
            ORDER BY arbitrage_percentage DESC
        ''', (cutoff_time, self.min_profit))
        
        columns = [desc[0] for desc in cursor.description]
        opportunities = []
        
        for row in cursor.fetchall():
            opportunity = dict(zip(columns, row))
            opportunities.append(opportunity)
        
        conn.close()
        return opportunities
    
    def send_console_alert(self, opportunity):
        """Send alert to console"""
        print("\n" + "="*60)
        print("ARBITRAGE ALERT!")
        print("="*60)
        print(f"EVENT: {opportunity['event_name']}")
        print(f"SPORT: {opportunity['sport']}")
        print(f"PROFIT: {opportunity['arbitrage_percentage']}% (${opportunity['expected_profit']})")
        print("-"*40)
        print(f"HOME: Bet ${opportunity['home_stake']} @ {opportunity['home_odds']} ({opportunity['home_bookmaker']})")
        print(f"AWAY: Bet ${opportunity['away_stake']} @ {opportunity['away_odds']} ({opportunity['away_bookmaker']})")
        
        if opportunity['draw_stake'] and opportunity['draw_stake'] > 0:
            print(f"DRAW: Bet ${opportunity['draw_stake']} @ {opportunity['draw_odds']} ({opportunity['draw_bookmaker']})")
        
        print(f"TIME: {opportunity['timestamp']}")
        print("="*60)
    
    def send_file_alert(self, opportunity):
        """Send alert to file"""
        alert_file = "arbitrage_alerts.txt"
        
        with open(alert_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"ARBITRAGE ALERT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Event: {opportunity['event_name']}\n")
            f.write(f"Sport: {opportunity['sport']}\n")
            f.write(f"Profit: {opportunity['arbitrage_percentage']}% (${opportunity['expected_profit']})\n")
            f.write(f"Home: Bet ${opportunity['home_stake']} @ {opportunity['home_odds']} ({opportunity['home_bookmaker']})\n")
            f.write(f"Away: Bet ${opportunity['away_stake']} @ {opportunity['away_odds']} ({opportunity['away_bookmaker']})\n")
            
            if opportunity['draw_stake'] and opportunity['draw_stake'] > 0:
                f.write(f"Draw: Bet ${opportunity['draw_stake']} @ {opportunity['draw_odds']} ({opportunity['draw_bookmaker']})\n")
            
            f.write(f"Timestamp: {opportunity['timestamp']}\n")
            f.write(f"{'='*60}\n")
    
    def send_email_alert(self, opportunity):
        """Send alert via email (optional)"""
        if not self.email_alerts:
            return
        
        try:            
            subject = f"Arbitrage Alert: {opportunity['arbitrage_percentage']}% Profit Available!"
            
            body = f"""
            ARBITRAGE OPPORTUNITY DETECTED!
            
            Event: {opportunity['event_name']}
            Sport: {opportunity['sport']}
            
            Profit: {opportunity['arbitrage_percentage']}% (${opportunity['expected_profit']})
            
            Betting Instructions:
            
            HOME: Bet ${opportunity['home_stake']} @ {opportunity['home_odds']}
            Bookmaker: {opportunity['home_bookmaker']}
            
            AWAY: Bet ${opportunity['away_stake']} @ {opportunity['away_odds']}
            Bookmaker: {opportunity['away_bookmaker']}
            """
            
            if opportunity['draw_stake'] and opportunity['draw_stake'] > 0:
                body += f"""
            DRAW: Bet ${opportunity['draw_stake']} @ {opportunity['draw_odds']}
            Bookmaker: {opportunity['draw_bookmaker']}
                """
            body += f"""
            
            Time Found: {opportunity['timestamp']}
            
            Place bets quickly as odds may change!
            
            Happy Arbitraging!
            """
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_settings['sender_email']
            msg['To'] = self.email_settings['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
            server.starttls()
            server.login(self.email_settings['sender_email'], self.email_settings['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_settings['sender_email'], self.email_settings['recipient_email'], text)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def send_alerts(self, opportunity):
        """Send alerts via all configured methods"""
        if self.console_alerts:
            self.send_console_alert(opportunity)
        
        if self.file_alerts:
            self.send_file_alert(opportunity)
        
        if self.email_alerts:
            self.send_email_alert(opportunity)
    
    def check_and_alert(self):
        """Check for new opportunities and send alerts"""
        opportunities = self.get_new_opportunities()
        
        if opportunities:
            logger.info(f"Found {len(opportunities)} new arbitrage opportunities!")
            
            for opportunity in opportunities:
                logger.info(f"Alerting for {opportunity['event_name']} ({opportunity['arbitrage_percentage']}%)")
                self.send_alerts(opportunity)
        
        return len(opportunities)
    
    def run_monitor(self, check_interval=60):
        """Run continuous monitoring for alerts"""
        logger.info("Starting arbitrage alert monitoring")
        logger.info(f"Minimum profit threshold: {self.min_profit}%")
        logger.info(f"Check interval: {check_interval} seconds")
        logger.info(f"Console alerts: {self.console_alerts}")
        logger.info(f"File alerts: {self.file_alerts}")
        logger.info(f"Email alerts: {self.email_alerts}")
        
        import time
        
        while True:
            try:
                alert_count = self.check_and_alert()
                
                if alert_count == 0:
                    logger.info("No new arbitrage opportunities found")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping alert monitoring...")
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                time.sleep(10)  # Wait before retry

def main():
    """Run the alert system"""
    alert_system = SimpleAlertSystem()
    
    # Run once to check for current opportunities
    print("Checking for current arbitrage opportunities...")
    alert_count = alert_system.check_and_alert()
    
    if alert_count == 0:
        print("No current arbitrage opportunities found")
        print("Starting monitoring for new opportunities...")
        
        # Start continuous monitoring
        alert_system.run_monitor(check_interval=30)  # Check every 30 seconds
    else:
        print(f"Found {alert_count} opportunities!")
        
        # Ask user if they want to start monitoring
        response = input("Start continuous monitoring? (y/n): ")
        if response.lower() == 'y':
            alert_system.run_monitor(check_interval=30)

if __name__ == "__main__":
    main()
