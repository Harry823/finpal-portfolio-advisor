import weaviate
import weaviate.classes as wvc
import os
from dotenv import load_dotenv
from weaviate.classes.init import Auth

load_dotenv()


WEAVIATE_CLUSTER_URL = os.getenv('WEAVIATE_CLUSTER_URL') 
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
FRIENDLIAI_API_KEY = os.getenv('FRIENDLIAI_API_KEY')


def create_weaviate_client():
    """Create and return Weaviate client"""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_CLUSTER_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        headers={"X-Friendli-Token": FRIENDLIAI_API_KEY}
    )
    return client

def generative_search(client, query, prompt_template=None, limit=5):
    """Perform generative search with RAG on stock data"""
    collection = client.collections.get("StockData")
    
    if prompt_template is None:
        prompt_template = """
        Based on the following stock market data, {query}
        
        Please provide a comprehensive analysis including:
        1. Key findings from the data
        2. Investment recommendations
        3. Risk considerations
        4. Market trends observed
        
        Stock Data:
        {context}
        """
    
    print(f"🤖 Generative Search: '{query}'")
    print("-" * 60)
    
    # Perform generative search
    response = collection.generate.near_text(
        query=query,
        limit=limit,
        grouped_task=prompt_template.format(query=query, context="{context}")
    )
    
    print("📊 Generated Analysis:")
    print(response.generated)
    print()
    
    print("📄 Source Data Used:")
    print("-" * 30)
    
    results = []
    for i, obj in enumerate(response.objects, 1):
        properties = obj.properties
        
        result = {
            "rank": i,
            "ticker": properties['ticker'],
            "sector": properties['sector'],
            "close_price": properties['close_price'],
            "date": properties['date'],
            "market_cap": properties['market_cap'],
            "pe_ratio": properties['pe_ratio']
        }
        results.append(result)
        
        print(f"{i}. {properties['ticker']} ({properties['sector']})")
        print(f"   Price: ${properties['close_price']:.2f} | P/E: {properties['pe_ratio']} | Market Cap: ${properties['market_cap']:,.0f}")
    
    return response.generated, results

def portfolio_recommendation(client, investment_amount, risk_level="moderate", limit=10):
    """Generate portfolio recommendations based on investment criteria"""
    
    risk_queries = {
        "conservative": "stable dividend paying stocks with low volatility and strong fundamentals",
        "moderate": "balanced mix of growth and value stocks with reasonable PE ratios",
        "aggressive": "high growth technology stocks with strong earnings potential"
    }
    
    query = f"recommend a diversified portfolio for ${investment_amount:,} investment with {risk_level} risk tolerance focusing on {risk_queries.get(risk_level, risk_queries['moderate'])}"
    
    prompt_template = f"""
    You are a financial advisor. Based on the provided stock data, create a portfolio recommendation for an investor with:
    - Investment Amount: ${investment_amount:,}
    - Risk Level: {risk_level.title()}
    
    Please provide:
    1. Recommended stock allocations with specific percentages
    2. Sector diversification strategy  
    3. Expected returns and risks
    4. Rationale for each stock selection
    5. Portfolio rebalancing suggestions
    
    Stock Data:
    {{context}}
    """
    
    return generative_search(client, query, prompt_template, limit)

def market_analysis(client, sector=None, timeframe="recent"):
    """Generate market analysis for specific sectors or overall market"""
    
    if sector:
        query = f"analyze the {sector} sector performance and provide investment insights"
        prompt_template = f"""
        Analyze the {sector} sector based on the provided stock data and give insights on:
        
        1. Sector performance overview
        2. Top performing stocks in the sector
        3. Valuation metrics analysis (P/E ratios, market caps)
        4. Investment opportunities and risks
        5. Sector outlook and trends
        
        {sector} Sector Data:
        {{context}}
        """
    else:
        query = f"provide overall market analysis and investment outlook based on {timeframe} data"
        prompt_template = """
        Provide a comprehensive market analysis based on the stock data including:
        
        1. Overall market sentiment and trends
        2. Sector performance comparison
        3. Valuation levels across different sectors
        4. Market opportunities and risks
        5. Investment strategy recommendations
        
        Market Data:
        {context}
        """
    
    return generative_search(client, query, prompt_template, limit=15)

def investment_advisor(client, user_query, limit=10):
    """
    AI Investment Advisor - analyzes stocks based on user queries and provides investment recommendations
    """
    collection = client.collections.get("StockData")
    
    print(f"🤖 Investment Advisor Query: '{user_query}'")
    print("-" * 60)
    
    # Investment advisor prompt template
    advisor_prompt = f"""
    You are an expert investment advisor. Based on the user's question: "{user_query}"
    
    Analyze the provided stock market data and give a comprehensive investment recommendation including:
    
    1. **Company Name** : The name of the company the user should invest in
    2. **Investment Recommendation**: Should the user invest? (BUY/HOLD/SELL/AVOID)
    3. **Key Reasons**: 3-5 bullet points explaining your recommendation
    4. **Risk Assessment**: What are the main risks?
    5. **Financial Metrics Analysis**: Comment on P/E ratios, market cap, dividend yields
    6. **Sector Context**: How does this perform within its sector?
    7. **Timeline**: Short-term vs long-term outlook
    9. **Portfolio Allocation**: What percentage of portfolio (if any) should this represent?
    
    Be specific, data-driven, and provide actionable advice. Use the actual numbers from the data.
    
    Stock Market Data:
    {{context}}
    """
    
    # Perform generative search with investment focus
    response = collection.generate.near_text(
        query=user_query,
        limit=limit,
        grouped_task=advisor_prompt
    )
    
    print("📊 Investment Recommendation:")
    print(response.generated)
    print()
    
    print("📈 Supporting Data:")
    print("-" * 30)
    
    results = []
    for i, obj in enumerate(response.objects, 1):
        properties = obj.properties
        
        result = {
            "rank": i,
            "ticker": properties['ticker'],
            "sector": properties['sector'],
            "close_price": properties['close_price'],
            "date": properties['date'],
            "market_cap": properties['market_cap'],
            "pe_ratio": properties['pe_ratio'],
            "dividend_yield": properties['dividend_yield'],
            "eps": properties['eps']
        }
        results.append(result)
        
        print(f"{i}. {properties['ticker']} ({properties['sector']})")
        print(f"   Current Price: ${properties['close_price']:.2f}")
        print(f"   P/E Ratio: {properties['pe_ratio']:.2f}")
        print(f"   Market Cap: ${properties['market_cap']:,.0f}")
        print(f"   Dividend Yield: {properties['dividend_yield']:.2f}%")
        print(f"   EPS: ${properties['eps']:.2f}")
        print()
    
    return response.generated, results

def stock_analysis(client, ticker_symbol):
    """
    Analyze a specific stock ticker and provide investment recommendation
    """
    collection = client.collections.get("StockData")
    
    # Get all data for the specific ticker
    response = collection.query.fetch_objects(
        limit=50,
        where=wvc.query.Filter.by_property("ticker").equal(ticker_symbol.upper())
    )
    
    if not response.objects:
        print(f"❌ No data found for ticker: {ticker_symbol}")
        return None, []
    
    print(f"📊 Stock Analysis for {ticker_symbol.upper()}")
    print("=" * 50)
    
    # Calculate some basic metrics from available data
    prices = [obj.properties['close_price'] for obj in response.objects]
    volumes = [obj.properties['volume_traded'] for obj in response.objects]
    dates = [obj.properties['date'] for obj in response.objects]
    
    latest = response.objects[0].properties
    avg_price = sum(prices) / len(prices)
    avg_volume = sum(volumes) / len(volumes)
    
    # Create detailed analysis prompt
    analysis_prompt = f"""
    Analyze {ticker_symbol.upper()} stock and provide a detailed investment recommendation.
    
    Current Stock Information:
    - Ticker: {latest['ticker']}
    - Sector: {latest['sector']}
    - Current Price: ${latest['close_price']:.2f}
    - P/E Ratio: {latest['pe_ratio']:.2f}
    - Market Cap: ${latest['market_cap']:,.0f}
    - Dividend Yield: {latest['dividend_yield']:.2f}%
    - EPS: ${latest['eps']:.2f}
    - 52-Week High: ${latest['week_52_high']:.2f}
    - 52-Week Low: ${latest['week_52_low']:.2f}
    
    Historical Context:
    - Average Price: ${avg_price:.2f}
    - Average Volume: {avg_volume:,.0f}
    - Data Points: {len(response.objects)} trading days
    
    Provide:
    1. **RECOMMENDATION**: BUY/HOLD/SELL/AVOID with confidence level (1-10)
    2. **PRICE TARGET**: Fair value estimate and potential upside/downside
    3. **KEY STRENGTHS**: What makes this stock attractive?
    4. **KEY RISKS**: What are the main concerns?
    5. **VALUATION**: Is it fairly valued, overvalued, or undervalued?
    6. **SECTOR COMPARISON**: How does it compare to sector averages?
    7. **INVESTMENT HORIZON**: Better for short-term or long-term?
    8. **PORTFOLIO WEIGHT**: Suggested allocation (1-5% conservative, 5-10% moderate, 10%+ aggressive)
    
    Be specific with numbers and reasoning. Base your analysis on the provided financial metrics.
    
    Stock Data: {{context}}
    """
    
    # Use generative search for detailed analysis
    gen_response = collection.generate.near_text(
        query=f"detailed investment analysis of {ticker_symbol} stock performance and valuation",
        where=wvc.query.Filter.by_property("ticker").equal(ticker_symbol.upper()),
        limit=10,
        grouped_task=analysis_prompt
    )
    
    print("🤖 AI Investment Analysis:")
    print(gen_response.generated)
    
    return gen_response.generated, response.objects

def stock_comparison(client, ticker1, ticker2):
    """Compare two specific stocks using generative analysis"""
    
    collection = client.collections.get("StockData")
    
    # Get data for both stocks
    response1 = collection.query.fetch_objects(
        where=wvc.query.Filter.by_property("ticker").equal(ticker1),
        limit=5
    )
    
    response2 = collection.query.fetch_objects(
        where=wvc.query.Filter.by_property("ticker").equal(ticker2),
        limit=5
    )
    
    if not response1.objects or not response2.objects:
        print(f"❌ Could not find data for one or both tickers: {ticker1}, {ticker2}")
        return None, []
    
    query = f"compare {ticker1} and {ticker2} stocks for investment decision"
    
    prompt_template = f"""
    Compare {ticker1} and {ticker2} stocks based on the provided data and help make an investment decision:
    
    1. Financial metrics comparison (price, P/E ratio, market cap, etc.)
    2. Sector context and positioning  
    3. Valuation analysis
    4. Risk assessment for each stock
    5. Investment recommendation with reasoning
    
    Stock Data:
    {{context}}
    """
    
    # Combine the objects for generative search
    combined_objects = list(response1.objects) + list(response2.objects)
    
    # Create a manual generative query (since we have specific objects)
    context_text = ""
    for obj in combined_objects:
        props = obj.properties
        context_text += f"{props['ticker']} ({props['sector']}): Price ${props['close_price']:.2f}, P/E {props['pe_ratio']}, Market Cap ${props['market_cap']:,.0f}\n"
    
    # Use the standard generative search but with ticker-specific query
    return generative_search(client, query, prompt_template, limit=10)

def interactive_generative_search(client):
    """Interactive generative search interface"""
    print("🤖 Interactive Investment Advisor")
    print("Available commands:")
    print("- ask: <investment question>")
    print("- stock: <ticker_symbol>")  
    print("- portfolio: <amount> <risk_level>")  
    print("- analyze: <sector_name>")
    print("- compare: <ticker1> <ticker2>")
    print("- quit: exit")
    print("-" * 50)
    
    while True:
        user_input = input("\nEnter command: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        try:
            if user_input.startswith('ask:'):
                query = user_input[4:].strip()
                investment_advisor(client, query)
                
            elif user_input.startswith('stock:'):
                ticker = user_input[6:].strip()
                stock_analysis(client, ticker)
                
            elif user_input.startswith('portfolio:'):
                parts = user_input[10:].strip().split()
                if len(parts) >= 1:
                    amount = int(parts[0].replace('$', '').replace(',', ''))
                    risk = parts[1] if len(parts) > 1 else "moderate"
                    portfolio_recommendation(client, amount, risk)
                else:
                    print("Usage: portfolio: <amount> <risk_level>")
                    
            elif user_input.startswith('analyze:'):
                sector = user_input[8:].strip()
                market_analysis(client, sector)
                
            elif user_input.startswith('compare:'):
                tickers = user_input[8:].strip().split()
                if len(tickers) >= 2:
                    stock_comparison(client, tickers[0].upper(), tickers[1].upper())
                else:
                    print("Usage: compare: <ticker1> <ticker2>")
                    
            else:
                print("Unknown command. Use ask:, stock:, portfolio:, analyze:, compare:, or quit")
                
        except Exception as e:
            print(f"Error: {e}")

def main():
    try:
        # Create client
        client = create_weaviate_client()
        print("✅ Connected to Weaviate cluster")
        
        # Check if collection exists and has data
        if not client.collections.exists("StockData"):
            print("❌ StockData collection does not exist. Please run 1_create_collection.py first.")
            return
        
        collection = client.collections.get("StockData")
        total_count = collection.aggregate.over_all().total_count
        
        if total_count == 0:
            print("❌ StockData collection is empty. Please run 2_populate.py first.")
            return
        
        print(f"📊 Collection contains {total_count} stock records")
        print()
        
        # Demo investment advisor capabilities
        print("🧪 Testing Investment Advisor capabilities...")
        print("=" * 70)
        
        # Example investment queries
        print("Example 1: General investment question")
        investment_advisor(client, "Should I invest in Apple stock?")
        print("\n" + "=" * 70 + "\n")
        
        print("Example 2: Specific stock analysis")
        stock_analysis(client, "AAPL")
        print("\n" + "=" * 70 + "\n")
        
        print("Example 3: Portfolio recommendation")
        portfolio_recommendation(client, 50000, "moderate")
        print("\n" + "=" * 70 + "\n")
        
        # Interactive search
        interactive_generative_search(client)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals() and client is not None:
            client.close()

if __name__ == "__main__":
    main()