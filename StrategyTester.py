import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px

class NQPatternAnalyzer:
    def __init__(self):
        self.data = None
        self.patterns = None
        
    def fetch_data(self, start_date=None, end_date=None):
        """
        Fetch minute-level NQ futures data
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Note: For minute-level data, you might need to use a different data source
        self.data = yf.download("NQ=F", start=start_date, end=end_date, interval="60m")
        print(self.data.head())
        return self.data
       
    
    def analyze_time_window(self, start_time="09:40", end_time="09:50"):
        """
        Analyze patterns in specific time window
        """
        if self.data is None:
            raise ValueError("Please fetch data first")
            
        # Convert index to datetime if needed
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)
            
        # Filter for time window
        mask = (self.data.index.time >= pd.to_datetime(start_time).time()) & \
               (self.data.index.time <= pd.to_datetime(end_time).time())
        window_data = self.data[mask].copy()
        
        # Calculate statistics
        window_data['prev_close'] = window_data['Close'].shift(1)
        window_data['return'] = (window_data['Close'] - window_data['prev_close']) / window_data['prev_close'] * 100
        
        # Calculate morning range (6:00-9:00)
        def get_morning_range(date):
            day_data = self.data[self.data.index.date == date.date()]
            morning_data = day_data[day_data.index.time <= pd.to_datetime('09:00').time()]
            if len(morning_data) == 0:
                return 0
            return morning_data['High'].max() - morning_data['Low'].min()
            
        window_data['morning_range'] = window_data.index.map(get_morning_range)
        window_data['range_stddev'] = window_data['morning_range'].rolling(20).std()
        
        # Identify reversals
        window_data['reversal'] = np.where(
            (window_data['return'] < -0.5) & 
            (window_data['Close'].shift(-1) > window_data['Close']),
            1, 0
        )
        
        self.patterns = window_data
        return window_data
    
    def plot_analysis(self):
        """
        Create statistical plots of the patterns
        """
        if self.patterns is None:
            raise ValueError("Please run analysis first")
            
        # Create subplots
        fig = make_subplots(rows=2, cols=1,
                           subplot_titles=('Histogram of Reversal Times',
                                         'Reversal Success Rate by Range'),
                           vertical_spacing=0.15,
                           row_heights=[0.5, 0.5])
        
        # Histogram of reversal times
        reversal_times = self.patterns[self.patterns['reversal'] == 1].index.time
        fig.add_trace(
            go.Histogram(x=reversal_times, name="Reversal Times"),
            row=1, col=1
        )
        
        # Success rate by range
        success_by_range = self.patterns.groupby('morning_range')['reversal'].mean() * 100
        fig.add_trace(
            go.Bar(x=success_by_range.index, y=success_by_range.values,
                  name="Success Rate by Range"),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title='NQ Futures Reversal Analysis',
            height=800,
            showlegend=True
        )
        
        return fig
    
    def print_statistics(self):
        """
        Print key statistics about the patterns
        """
        if self.patterns is None:
            raise ValueError("Please run analysis first")
            
        stats = {
            'Total_Reversals': self.patterns['reversal'].sum(),
            'Reversal_Rate': (self.patterns['reversal'].mean() * 100),
            'Average_Return': self.patterns[self.patterns['reversal'] == 1]['return'].mean(),
            'Success_Rate': (self.patterns['reversal'] & 
                           (self.patterns['return'].shift(-1) > 0)).mean() * 100
        }
        
        return stats
#test case
analyzer = NQPatternAnalyzer()
data = analyzer.fetch_data()
patterns = analyzer.analyze_time_window()
stats = analyzer.print_statistics()
fig = analyzer.plot_analysis()
fig.show()
