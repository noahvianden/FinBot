import ccxt
import pandas as pd
import numpy as np


def fetch_full_historical_data(symbol, market, start_date, end_date, timeframe='1d'):
    exchange = ccxt.binance()
    all_data = []
    since = exchange.parse8601(f"{start_date}T00:00:00Z")

    while since < exchange.parse8601(f"{end_date}T00:00:00Z"):
        data = exchange.fetch_ohlcv(f"{symbol}/{market}", timeframe, since, limit=1000)
        if not data:
            break
        all_data += data
        since = data[-1][0] + 1  # Nächster Zeitstempel

    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


def add_price_change(df):
    df['price_change'] = df['close'].diff().shift(-1)

    # Entferne Ausreißer basierend auf dem IQR
    Q1 = df['price_change'].quantile(0.25)
    Q3 = df['price_change'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[~((df['price_change'] < (Q1 - 1.5 * IQR)) | (df['price_change'] > (Q3 + 1.5 * IQR)))]

    # Fehlende oder unrealistische Werte interpolieren
    df.loc[:, 'price_change'] = df['price_change'].interpolate(method='linear')

    return df

def save_resampled_data_with_changes(df, freq, filename):
    resampled = df.resample(freq, on='timestamp').agg({
        'close': 'last'
    }).dropna()

    # Add price change column
    resampled = add_price_change(resampled)

    # Ensure timestamp is kept as a column
    resampled = resampled.reset_index()
    resampled.to_csv(filename, index=False)



# Solana Daten abrufen
symbol = 'SOL'
market = 'USDT'
start = '2020-04-11'
end = '2024-11-08'

daily_data = fetch_full_historical_data(symbol, market, start, end)

# Tägliche Daten speichern
save_resampled_data_with_changes(daily_data, 'D', 'solana_daily_data.csv')

# Wöchentliche Daten speichern
save_resampled_data_with_changes(daily_data, 'W', 'solana_weekly_data.csv')

# Monatliche Daten speichern
save_resampled_data_with_changes(daily_data, 'M', 'solana_monthly_data.csv')
