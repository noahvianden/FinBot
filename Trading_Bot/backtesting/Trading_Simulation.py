from Trading_Bot.helper import get_open_price, is_valid_trading_day, get_next_trading_day
import pandas as pd
import numpy as np

class Trading_Simulation:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.portfolio = {}
        self.trading_log = []

    def buy_stock(self, ticker, date, quantity):
        try:
            price = get_open_price(ticker, date)
        except ValueError as e:
            print(f"Kauf fehlgeschlagen: {e}")
            return
        total_cost = price * quantity
        if self.balance >= total_cost:
            self.balance -= total_cost
            if ticker in self.portfolio:
                old_quantity = self.portfolio[ticker]['quantity']
                old_total_cost = self.portfolio[ticker]['avg_price'] * old_quantity
                new_total_cost = old_total_cost + total_cost
                new_quantity = old_quantity + quantity
                new_avg_price = new_total_cost / new_quantity
                self.portfolio[ticker]['quantity'] = new_quantity
                self.portfolio[ticker]['avg_price'] = new_avg_price
            else:
                self.portfolio[ticker] = {'quantity': quantity, 'avg_price': price}
            self.trading_log.append(f"Kauf: {quantity} Aktien von {ticker} am {date} zu je {price:.2f} USD")
        else:
            print("Nicht genug Guthaben, um den Kauf durchzuführen.")

    def sell_stock(self, ticker, date, quantity):
        try:
            price = get_open_price(ticker, date)
        except ValueError as e:
            print(f"Verkauf fehlgeschlagen: {e}")
            return

        if ticker in self.portfolio and self.portfolio[ticker]['quantity'] >= quantity:
            total_value = price * quantity
            self.balance += total_value
            self.portfolio[ticker]['quantity'] -= quantity
            if self.portfolio[ticker]['quantity'] == 0:
                del self.portfolio[ticker]
            self.trading_log.append(f"Verkauf: {quantity} Aktien von {ticker} am {date} zu je {price:.2f} USD")
        else:
            print("Nicht genug Aktien im Depot, um den Verkauf durchzuführen.")

    def get_trading_log(self):
        return self.trading_log

    def get_portfolio_value(self, last_trade_date):
        total_value = 0
        for ticker, details in self.portfolio.items():
            try:
                # Abrufen des Eröffnungspreises für den letzten Simulationshandelstag
                price_on_last_day = get_open_price(ticker, last_trade_date)
                total_value += price_on_last_day * details['quantity']
            except ValueError as e:
                # Verwende den durchschnittlichen Kaufpreis, falls kein Preis abgerufen werden kann
                total_value += details['avg_price'] * details['quantity']
                print(f"Warnung: Verwende durchschnittlichen Kaufpreis für {ticker} aufgrund eines Fehlers: {e}")
        return total_value

    def simulate_trades(self, ticker, trade_dates):
        for date in trade_dates:
            # Konvertiere numpy.datetime64 in Python datetime
            date_dt = pd.Timestamp(date).to_pydatetime()
            date_str = date_dt.strftime('%Y-%m-%d')
            if np.random.rand() > 0.5:  # Zufällig kaufen oder verkaufen
                quantity = np.random.randint(1, 10)  # Zufällige Menge zwischen 1 und 10
                self.buy_stock(ticker, date_str, quantity)
            else:
                if ticker in self.portfolio and self.portfolio[ticker]['quantity'] > 0:
                    quantity = np.random.randint(1, self.portfolio[ticker]['quantity'] + 1)
                    self.sell_stock(ticker, date_str, quantity)
                else:
                    # Keine Aktien zum Verkaufen, versuchen zu kaufen
                    quantity = np.random.randint(1, 10)
                    self.buy_stock(ticker, date_str, quantity)

if __name__ == "__main__":
    # Handelsdaten vorbereiten
    ticker = 'AAPL'
    dates = pd.date_range(start='2010-01-01', end='2023-01-01', freq='B')  # Nur Handelstage
    trade_dates = np.random.choice(dates, size=10, replace=False)
    trade_dates = np.sort(trade_dates)  # Daten sortieren

    # Trading Simulation durchführen
    simulation = Trading_Simulation(initial_balance=10000)
    simulation.simulate_trades(ticker, trade_dates)

    # Berechne das Datum des letzten Handelstags
    last_trade_date = pd.Timestamp(trade_dates[-1]).strftime('%Y-%m-%d')

    # Portfolio-Wert zum letzten Handelstag berechnen
    portfolio_value = simulation.get_portfolio_value(last_trade_date)
    total_balance = simulation.balance + portfolio_value

    # Ergebnisse anzeigen
    print("Trading Log:")
    for log_entry in simulation.get_trading_log():
        print(log_entry)

    print(f"\nEndgültiges Guthaben (inkl. Portfolio-Wert): {total_balance:.2f} USD")
    print(f"Barbestand: {simulation.balance:.2f} USD")
    print(f"Portfolio-Wert am {last_trade_date}: {portfolio_value:.2f} USD")
    print(f"Aktuelles Depot: {simulation.portfolio}")