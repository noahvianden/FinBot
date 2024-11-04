import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import holidays

def get_historical_data(ticker_symbol, start_date, end_date=None, columns=None):
    next_trading_day = None
    # Stelle sicher, dass das Startdatum ein Handelstag ist
    us_holidays = holidays.US()
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    try:
        if start_datetime.weekday() >= 5 or start_datetime in us_holidays:  # Samstag = 5, Sonntag = 6 oder Feiertag
            raise ValueError("Das angegebene Startdatum fällt auf ein Wochenende oder einen Feiertag.")
    except ValueError as e:
        # Setze den nächsten Handelstag
        while start_datetime.weekday() >= 5 or start_datetime in us_holidays:
            start_datetime += timedelta(days=1)
        next_trading_day = start_datetime.strftime('%Y-%m-%d')
        return f"Fehler: {e}", next_trading_day

    # Wenn kein Enddatum angegeben ist, setze es auf Startdatum + 1 Handelstag
    if not end_date:
        end_datetime = start_datetime + timedelta(days=1)

        # Füge Tage hinzu, bis Daten vorhanden sind
        data = pd.DataFrame()
        while data.empty:
            end_date = end_datetime.strftime('%Y-%m-%d')
            data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
            end_datetime += timedelta(days=1)
    else:
        # Lade die historischen Kursdaten
        data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')

    # Filtere die gewünschten Spalten, falls angegeben
    if columns:
        data = data[columns]

    # Wenn nur ein Wert vorhanden ist, gib diesen als einfache Variable zurück
    if len(data) == 1 and len(data.columns) == 1:
        return float(data.iloc[0, 0]), next_trading_day

    # Gib die Daten und ggf. den nächsten Handelstag zurück
    return data, next_trading_day


def is_valid_trading_day(ticker_symbol, date):
    # Setze das Start- und Enddatum für den Download auf den gleichen Tag
    start_date = date
    end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

    # Lade die Daten für den Tag und überprüfe, ob sie leer sind
    data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
    return not data.empty  # Gültiger Handelstag, wenn Daten verfügbar sind


def get_next_trading_day(ticker_symbol, start_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')

    # Schleife bis zum nächsten Handelstag
    while True:
        if is_valid_trading_day(ticker_symbol, current_date):
            return current_date

        current_date += timedelta(days=1)


# Beispielaufruf der Methode
ticker = 'AAPL'
start = '2022-01-03'  # Beispielhaftes Startdatum, das auf einen Nicht-Handelstag fallen kann
end = None  # Optionales Enddatum, kann angepasst werden
columns = ['Adj Close']  # Optional: Liste der gewünschten Spalten

historical_data, next_trading_day = get_historical_data(ticker, start, end, columns)

# Setze die Pandas-Option, um alle Spalten anzuzeigen
pd.set_option('display.max_columns', None)

# Zeige die Ergebnisse an
if isinstance(historical_data, pd.DataFrame):
    print(historical_data.head())
elif isinstance(historical_data, (int, float, str)):
    print(f"Wert: {historical_data}")

if next_trading_day:
    print(f"Nächster Handelstag: {next_trading_day}")
