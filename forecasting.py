"""
Time Series Forecasting with ARIMA and LSTM
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# ARIMA
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

# LSTM
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

class DelayForecaster:
    """Forecast transport delays using ARIMA and LSTM"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.scaler = MinMaxScaler()
        self.arima_model = None
        self.lstm_model = None
        
    def prepare_time_series(self, target_col: str = 'delay_minutes', 
                           freq: str = 'H') -> pd.Series:
        """
        Prepare time series data with specified frequency
        """
        # Ensure datetime index
        if 'timestamp' in self.data.columns:
            ts_data = self.data.set_index('timestamp')[target_col]
        else:
            # Create synthetic timestamp
            dates = pd.date_range(start='2024-01-01', periods=len(self.data), freq=freq)
            ts_data = pd.Series(self.data[target_col].values, index=dates)
        
        # Resample to specified frequency
        ts_data = ts_data.resample(freq).mean().fillna(method='ffill')
        
        return ts_data
    
    def check_stationarity(self, ts_data: pd.Series) -> bool:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test
        """
        result = adfuller(ts_data.dropna())
        print(f'ADF Statistic: {result[0]:.4f}')
        print(f'p-value: {result[1]:.4f}')
        print(f'Critical Values:')
        for key, value in result[4].items():
            print(f'\t{key}: {value:.4f}')
        
        is_stationary = result[1] < 0.05
        print(f'Series is {"stationary" if is_stationary else "non-stationary"}')
        return is_stationary
    
    def fit_arima(self, ts_data: pd.Series, order: tuple = (5,1,0)):
        """
        Fit ARIMA model
        """
        print("\n" + "="*50)
        print("TRAINING ARIMA MODEL")
        print("="*50)
        
        self.arima_model = ARIMA(ts_data, order=order)
        self.arima_fitted = self.arima_model.fit()
        
        print(self.arima_fitted.summary())
        return self.arima_fitted
    
    def forecast_arima(self, steps: int = 24) -> pd.Series:
        """
        Generate ARIMA forecasts
        """
        forecast = self.arima_fitted.forecast(steps=steps)
        return forecast
    
    def prepare_lstm_data(self, ts_data: pd.Series, lookback: int = 24):
        """
        Prepare data for LSTM (lookback windows)
        """
        values = ts_data.values.reshape(-1, 1)
        scaled_values = self.scaler.fit_transform(values)
        
        X, y = [], []
        for i in range(lookback, len(scaled_values)):
            X.append(scaled_values[i-lookback:i, 0])
            y.append(scaled_values[i, 0])
        
        X, y = np.array(X), np.array(y)
        
        # Reshape X for LSTM [samples, time steps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Split into train/test (80-20)
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        return X_train, X_test, y_train, y_test, self.scaler
    
    def build_lstm_model(self, input_shape: tuple) -> Sequential:
        """
        Build LSTM neural network architecture
        """
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), 
                     loss='mse', 
                     metrics=['mae'])
        
        return model
    
    def train_lstm(self, ts_data: pd.Series, lookback: int = 24, 
                   epochs: int = 50, batch_size: int = 32):
        """
        Train LSTM model
        """
        print("\n" + "="*50)
        print("TRAINING LSTM MODEL")
        print("="*50)
        
        X_train, X_test, y_train, y_test, scaler = self.prepare_lstm_data(ts_data, lookback)
        
        self.lstm_model = self.build_lstm_model((lookback, 1))
        
        history = self.lstm_model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        # Evaluate
        train_loss = self.lstm_model.evaluate(X_train, y_train, verbose=0)
        test_loss = self.lstm_model.evaluate(X_test, y_test, verbose=0)
        
        print(f"\nTraining Loss (MSE): {train_loss[0]:.4f}")
        print(f"Training MAE: {train_loss[1]:.4f}")
        print(f"Test Loss (MSE): {test_loss[0]:.4f}")
        print(f"Test MAE: {test_loss[1]:.4f}")
        
        return history
    
    def forecast_lstm(self, ts_data: pd.Series, lookback: int = 24, 
                      steps: int = 24) -> np.ndarray:
        """
        Generate LSTM forecasts recursively
        """
        values = ts_data.values.reshape(-1, 1)
        scaled_values = self.scaler.transform(values)
        
        # Use last 'lookback' values as seed
        last_window = scaled_values[-lookback:].reshape(1, lookback, 1)
        
        forecasts = []
        current_window = last_window.copy()
        
        for _ in range(steps):
            next_pred = self.lstm_model.predict(current_window, verbose=0)
            forecasts.append(next_pred[0, 0])
            
            # Update window
            current_window = np.roll(current_window, -1, axis=1)
            current_window[0, -1, 0] = next_pred[0, 0]
        
        # Inverse transform
        forecasts = np.array(forecasts).reshape(-1, 1)
        forecasts = self.scaler.inverse_transform(forecasts)
        
        return forecasts.flatten()
    
    def compare_forecasts(self, ts_data: pd.Series, forecast_steps: int = 24):
        """
        Compare ARIMA and LSTM forecasts
        """
        print("\n" + "="*50)
        print("FORECAST COMPARISON")
        print("="*50)
        
        # ARIMA forecast
        arima_forecast = self.forecast_arima(steps=forecast_steps)
        
        # LSTM forecast
        lstm_forecast = self.forecast_lstm(ts_data, steps=forecast_steps)
        
        # Create comparison dataframe
        comparison = pd.DataFrame({
            'Hour_Ahead': range(1, forecast_steps + 1),
            'ARIMA_Forecast': arima_forecast.values,
            'LSTM_Forecast': lstm_forecast
        })
        
        print("\nForecast Comparison (next 12 hours):")
        print(comparison.head(12).to_string(index=False))
        
        return comparison

if __name__ == "__main__":
  
    from data_collection import TransportDataCollector
    collector = TransportDataCollector()
    df = collector.collect_batch_data(1000)
    
    
    forecaster = DelayForecaster(df)
    
   
    ts_data = forecaster.prepare_time_series(freq='H')
    
    
    forecaster.check_stationarity(ts_data)
    
   
    forecaster.fit_arima(ts_data, order=(7,1,2))
    
   
    forecaster.train_lstm(ts_data, epochs=20)
    
    
    comparison = forecaster.compare_forecasts(ts_data, forecast_steps=24)
    
    
    comparison.to_csv('data/forecast_comparison.csv', index=False)
    print("\nForecast results saved to 'data/forecast_comparison.csv'")