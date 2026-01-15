import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol: str, period: str = "6mo"):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval="1d")

        if df.empty:
            return None

        df.reset_index(inplace=True)
        df["Date"] = df["Date"].astype(str)

        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]

        df.ffill(inplace=True)

        df["Daily Return"] = (df["Close"] - df["Open"]) / df["Open"]
        df["7 Day MA"] = df["Close"].rolling(window=7).mean()
        
        df = df.replace({pd.NA: None, float('nan'): None, float('inf'): None, float('-inf'): None})

        return df

    except Exception as e:
        print("Error fetching stock data:", e)
        return None
