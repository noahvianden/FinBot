import yfinance as yf
from datetime import datetime, timedelta
import holidays

def get_open_price(ticker_symbol, date):
    try:
        input_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Ungültiges Datum. Bitte verwenden Sie das Format 'YYYY-MM-DD'.")

    if not is_valid_trading_day(ticker_symbol, input_date):
        trading_day = get_next_trading_day(ticker_symbol, input_date)
    else:
        trading_day = input_date

    # Lade die historischen Kursdaten
    end_date = (trading_day + timedelta(days=1)).strftime('%Y-%m-%d')
    data = yf.download(ticker_symbol, start=date, end=end_date, interval='1d')

    # Überprüfe, ob die Daten erfolgreich geladen wurden und die Spalte "Open" vorhanden ist
    if data.empty or "Open" not in data.columns:
        raise ValueError("Keine Daten für das angegebene Datum gefunden oder 'Open'-Spalte nicht vorhanden.")

    # Gib den Eröffnungspreis zurück
    return data["Open"].iloc[0].item()


def is_valid_trading_day(ticker_symbol, date):
    # Setze das Start- und Enddatum für den Download auf den gleichen Tag
    start_date = date
    end_date = (start_date + timedelta(days=1)).strftime('%Y-%m-%d')

    # Lade die Daten für den Tag und überprüfe, ob sie leer sind
    data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
    return not data.empty  # Gültiger Handelstag, wenn Daten verfügbar sind


def get_next_trading_day(ticker_symbol, start_date):
    current_date = start_date

    # Schleife bis zum nächsten Handelstag
    while True:
        if is_valid_trading_day(ticker_symbol, current_date):
            return current_date

        current_date += timedelta(days=1)


# Testen der Funktion
if __name__ == "__main__":
    ticker = 'AAPL'
    date = '2022-01-01'  # Beispiel-Datum
    try:
        open_price = get_open_price(ticker, date)
        print(f"Eröffnungspreis von {ticker} am {date} ist {open_price:.2f} USD")
    except ValueError as e:
        print(f"Fehler beim Abrufen des Eröffnungspreises: {e}")
