"""
Simple runner for the complete arbitrage betting pipeline
Runs producer, calculator, and optionally dashboard and alerts
"""
import asyncio
import threading
import time
import logging
import subprocess
import sys
from config import *
import time
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class ArbitragePipeline:
    """Complete arbitrage betting pipeline"""
    
    def __init__(self):
        self.running = False
        self.threads = []
    
    def run_producer_worker(self):
        """Run the data producer in a thread"""
        logger.info("Starting data producer...")
        try:
            from producer import SimpleProducer
            producer = SimpleProducer()
            asyncio.run(producer.run())
        except Exception as e:
            logger.error(f"Producer error: {e}")

    def run_calculator_worker(self):
        """Run the arbitrage calculator in a thread"""
        logger.info("Starting arbitrage calculator...")
        try:
            from arbitrage import SimpleArbitrageCalculator
            calculator = SimpleArbitrageCalculator()
            
            while self.running:
                opportunities = calculator.run_once()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities!")
                else:                    logger.info("No arbitrage opportunities found")
                
                time.sleep(60)  # Run every minute
                
        except Exception as e:
            logger.error(f"Calculator error: {e}")
    
    def run_alerts_worker(self):
        """Run the alert system in a thread"""
        logger.info("Starting alert system...")
        try:
            from alerts import SimpleAlertSystem
            alert_system = SimpleAlertSystem()
            
            while self.running:
                alert_count = alert_system.check_and_alert()
                time.sleep(30)  # Check for alerts every 30 seconds
                
        except Exception as e:
            logger.error(f"Alert system error: {e}")
    
    def start_dashboard(self):
        """Start the web dashboard in a separate process"""
        logger.info("Starting web dashboard...")
        try:
            subprocess.Popen([sys.executable, "dashboard.py"])
            logger.info("Dashboard started at http://localhost:5000")
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
    
    def start_pipeline(self, include_dashboard=True, include_alerts=True):
        """Start the complete pipeline"""
        print("Starting Arbitrage Betting Pipeline")
        print("="*50)
        print(f"Sports monitored: {SPORTS_TO_MONITOR}")
        print(f"Fetch interval: {FETCH_INTERVAL} seconds")
        print(f"Min profit threshold: {MIN_PROFIT_PERCENTAGE}%")
        print(f"Stake amount: ${STAKE_AMOUNT}")
        print("="*50)
        
        self.running = True
        
        # Start web dashboard
        if include_dashboard:
            self.start_dashboard()
            time.sleep(2)  # Give dashboard time to start
        
        # Start producer thread
        producer_thread = threading.Thread(target=self.run_producer_worker)
        producer_thread.daemon = True
        producer_thread.start()
        self.threads.append(producer_thread)
        
        # Give producer time to start fetching data
        time.sleep(10)
        
        # Start calculator thread
        calculator_thread = threading.Thread(target=self.run_calculator_worker)
        calculator_thread.daemon = True
        calculator_thread.start()
        self.threads.append(calculator_thread)
        
        # Start alerts thread
        if include_alerts:
            alerts_thread = threading.Thread(target=self.run_alerts_worker)
            alerts_thread.daemon = True
            alerts_thread.start()
            self.threads.append(alerts_thread)
        print("\nPipeline Components Started:")
        print("   - Data Producer (fetching odds)")
        print("   - Arbitrage Calculator")
        if include_alerts:
            print("   - Alert System")
        if include_dashboard:
            print("   - Web Dashboard (http://localhost:5000)")
        
        print("\nMonitoring for arbitrage opportunities...")
        print("Press Ctrl+C to stop\n")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop the pipeline"""
        logger.info("Stopping arbitrage pipeline...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        print("Pipeline stopped successfully!", flush=True)

class ArbitragePipelineTennis:
    def __init__(self, producer_script='tp.py', arbitrage_script='arbt2.py'):
        self.producer_script = producer_script
        self.arbitrage_script = arbitrage_script
        self.producer_process = None
        self.arbitrage_process = None
        self.stop_event = threading.Event()

    def _run_script(self, script_path, label):
        """Run a Python script with unbuffered output and stream its output in a thread."""
        time.sleep(2)  # Allow time for imports to settle
        try:
            process = subprocess.Popen(
                [sys.executable, "-u", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )

            thread = threading.Thread(target=self._stream_output, args=(process, label), daemon=True)
            thread.start()

            return process
        except Exception as e:
            print(f"[{label} ERROR] Failed to start {script_path}: {e}", flush=True)
            return None

    def _stream_output(self, process, label):
        """Stream subprocess output with prefix"""
        time.sleep(2)  # Allow time for process to start
        try:
            for line in iter(process.stdout.readline, ''):
                if line and not self.stop_event.is_set():
                    print(f"[{label}] {line.strip()}", flush=True)
        except Exception as e:
            print(f"[{label} ERROR] Streaming error: {e}", flush=True)

    def start_pipeline(self):
        print("🚀 Starting Arbitrage Pipeline for Tennis Betting", flush=True)

        print("🧠 Launching arbitrage detection engine...", flush=True)
        self.arbitrage_process = self._run_script(self.arbitrage_script, "ARBT")

        time.sleep(8)  # Allow time for consumer to connect

        print("🎰 Launching tennis betting data producer...", flush=True)
        self.producer_process = self._run_script(self.producer_script, "TP")

        print("\n✅ Pipeline components started.\nPress Ctrl+C to stop.\n", flush=True)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_pipeline()

    def stop_pipeline(self):
        print("🛑 Stopping pipeline...", flush=True)
        self.stop_event.set()

        for label, process in [("TP", self.producer_process), ("ARBT", self.arbitrage_process)]:
            if process and process.poll() is None:
                print(f"🔚 Terminating {label} process...", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚠️ {label} did not exit gracefully. Killing...", flush=True)
                    process.kill()

        print("✅ All processes terminated cleanly.", flush=True)



def main():
    """Main function"""
    print("Arbitrage Betting Pipeline", flush=True)
    print("="*40, flush=True)
    print("This will start the complete arbitrage betting system:", flush=True)
    print("1. Data Producer (fetches odds from API)", flush=True)
    print("2. Arbitrage Calculator (finds opportunities)", flush=True)
    if SPORTS_TO_MONITOR == ["tennis"]:
        print( flush=True)
    else:
        print("3. Alert System (notifies about opportunities)")
        print("4. Web Dashboard (monitoring interface)")
    print("="*40)
    
    # Check if user wants to start all components
    response = input("Start complete pipeline? (y/n): ").lower()
    
    if response != 'y':
        print("Pipeline not started. You can run components individually:")
        print("  python producer.py        # Data producer only")
        print("  python arbitrage.py       # Calculator only")
        print("  python dashboard.py       # Dashboard only")
        print("  python alerts.py          # Alerts only")
        return
    
    # Start pipeline
    if SPORTS_TO_MONITOR == ["tennis"]:
        pipeline = ArbitragePipelineTennis()
    else:
        pipeline = ArbitragePipeline()

    pipeline.start_pipeline()

if __name__ == "__main__":
    main()