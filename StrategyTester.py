import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class NQPatternAnalyzer:
    def __init__(self):
        self.data = None
        self.patterns = None

    def fetch_data(self, interval):
        """
        Fetch NQ futures data using a valid date range (within last 60 days).
        """
        # Get today's date
        end_date = ('2024-12-30')
        start_date = ('2024-12-15')

        print(f"[ Data: {start_date} to {end_date} interval:  {interval}]")

        self.data = yf.download("NQ=F", start=start_date, end=end_date, interval=interval)

        if self.data.empty:
            print("Warning: No data fetched. Check symbol and interval.")
        
        return self.data



    def analyze_reversals(self, start_time="09:40", end_time="09:50", threshold=-0.5):
        """
        Analyze reversals and compute win percentage.
        """
        if self.data is None or self.data.empty:
            raise ValueError("Please fetch data first")
        
        # Ensure datetime index
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)

        # Filter for the time window
        window_data = self.data.between_time(start_time, end_time).copy()

        if window_data.empty:
            print("No data available for the given time window.")
            return {}

        # Compute returns
        window_data['prev_close'] = window_data['Close'].shift(1)
        window_data['return'] = (window_data['Close'] - window_data['prev_close']) / window_data['prev_close'] * 100

        # Identify reversals
        window_data['reversal'] = np.where(
            (window_data['return'] < threshold) &
            (window_data['Close'].shift(-1) > window_data['Close']), 1, 0
        )

        # Compute reversal statistics
        total_reversals = window_data['reversal'].sum()
        reversal_percentage = (total_reversals / len(window_data)) * 100 if len(window_data) > 0 else 0

        # Compute average reversal time
        if total_reversals > 0:
            avg_reversal_time = window_data[window_data['reversal'] == 1].index.time
            avg_reversal_time = np.mean([t.hour * 3600 + t.minute * 60 + t.second for t in avg_reversal_time])
            avg_reversal_time_str = str(timedelta(seconds=int(avg_reversal_time)))
        else:
            avg_reversal_time_str = "N/A"

        # Return statistics
        stats = {
            "Total Reversals": total_reversals,
            "Reversal Percentage": f"{reversal_percentage:.2f}%",
            "Average Reversal Time": avg_reversal_time_str
        }

        # Print results in a readable format
        print("\n--- Reversal Analysis Results ---")
        print(f"Average Reversal Time = {avg_reversal_time_str} (HH:MM:SS)")
        print(f"Reversal Percentage = {reversal_percentage:.2f}%")
        print(f"Total Reversals Detected: {total_reversals}\n")

        return stats

# Example usage
analyzer = NQPatternAnalyzer()
analyzer.fetch_data(interval="5m")  # Fetching data with 15-minute intervals
stats = analyzer.analyze_reversals()
