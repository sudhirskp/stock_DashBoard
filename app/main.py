from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.data import fetch_stock_data
import os

app = FastAPI(
    title="Stock Data Intelligence API",
    description="A mini financial data platform to fetch, analyze, and compare stock market data using Python and FastAPI.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static frontend files
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    # Serve the frontend HTML if it exists
    html_path = "frontend/index.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Stock Data API is running. Visit /docs for API documentation."}

#----------------------------------------------

COMPANIES = [
    {"symbol": "RELIANCE", "name": "Reliance Industries"},
    {"symbol": "TCS", "name": "Tata Consultancy Services"},
    {"symbol": "INFY", "name": "Infosys"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank"},
    {"symbol": "SBIN", "name": "State Bank of India"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors"},
    {"symbol": "TATASTEEL", "name": "Tata Steel"},
    {"symbol": "TATAPOWER", "name": "Tata Power"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products"},
    {"symbol": "WIPRO", "name": "Wipro"},
    {"symbol": "ITC", "name": "ITC Limited"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki"},
    {"symbol": "TITAN", "name": "Titan Company"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises"},
    {"symbol": "AXISBANK", "name": "Axis Bank"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance"},
    {"symbol": "LT", "name": "Larsen & Toubro"}
]


def find_similar_stocks(query: str, limit: int = 5):
    """Find similar stock symbols based on partial match"""
    query = query.upper()
    matches = []
    
    for company in COMPANIES:
        symbol = company["symbol"]
        name = company["name"].upper()
        
        # Check if query is substring of symbol or name
        if query in symbol or query in name:
            matches.append(company)
    
    return matches[:limit]


@app.get( "/companies",
    tags=["Companies"],
    summary="List available companies",
    description="Returns a predefined list of supported NSE companies.")

def get_companies():
    return COMPANIES

#----------------------------------------------

@app.get( "/data/{symbol}",
    tags=["Stock Data"],
    summary="Get last 30 days stock data",
    description="Fetches last 30 days of OHLCV stock data along with daily returns and moving averages.")

def get_stock_data(symbol: str):
    nse_symbol = symbol.upper() + ".NS"
    df = fetch_stock_data(nse_symbol, period="1mo")

    if df is None:
        # Find similar stocks
        suggestions = find_similar_stocks(symbol)
        
        if suggestions:
            suggestion_list = ", ".join([f"{s['symbol']} ({s['name']})" for s in suggestions])
            error_msg = f"Stock symbol '{symbol.upper()}' not found. Did you mean: {suggestion_list}?"
        else:
            error_msg = f"Stock symbol '{symbol.upper()}' not found. Try: TCS, INFY, RELIANCE, TATAMOTORS, etc."
        
        raise HTTPException(status_code=404, detail=error_msg)

    # 🔑 CRITICAL: Convert DataFrame → pure Python
    records = df.tail(30).to_dict(orient="records")

    return {
        "symbol": symbol.upper(),
        "records": records
    }
    
    #--------------------------------------------------------------
@app.get("/summary/{symbol}",
    tags=["Stock Summary"],
    summary="Get 52-week stock summary",
    description="Returns 52-week high, low, and average closing price for a stock.")

def get_stock_summary(symbol: str):
    nse_symbol = symbol.upper() + ".NS"
    df = fetch_stock_data(nse_symbol, period="1y")

    if df is None:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    summary = {
        "symbol": symbol.upper(),
        "52_week_high": df["High"].max(),
        "52_week_low": df["Low"].min(),
        "average_close": round(df["Close"].mean(), 2)
    }

    return summary
    
#--------------------------------------------------------------

@app.get( "/compare",
    tags=["Stock Comparison"],
    summary="Compare two stocks",
    description="Compares two stocks based on average price, volatility, and 30-day return.")

def compare_stocks(symbol1: str, symbol2: str):
    sym1 = symbol1.upper() + ".NS"
    sym2 = symbol2.upper() + ".NS"

    df1 = fetch_stock_data(sym1, period="1mo")
    df2 = fetch_stock_data(sym2, period="1mo")

    if df1 is None or df2 is None:
        raise HTTPException(status_code=404, detail="One or both stock symbols not found")

    comparison = {
        "stock_1": symbol1.upper(),
        "stock_2": symbol2.upper(),

        "average_close": {
            symbol1.upper(): round(df1["Close"].mean(), 2),
            symbol2.upper(): round(df2["Close"].mean(), 2)
        },

        "volatility": {
            symbol1.upper(): round(df1["Daily Return"].std(), 4),
            symbol2.upper(): round(df2["Daily Return"].std(), 4)
        },

        "30_day_return": {
            symbol1.upper(): round(
                (df1.iloc[-1]["Close"] - df1.iloc[0]["Close"]) / df1.iloc[0]["Close"], 4
            ),
            symbol2.upper(): round(
                (df2.iloc[-1]["Close"] - df2.iloc[0]["Close"]) / df2.iloc[0]["Close"], 4
            )
        }
    }

    return comparison
    
    
    
