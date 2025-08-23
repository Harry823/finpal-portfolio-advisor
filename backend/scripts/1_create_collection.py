import weaviate
import weaviate.classes as wvc
import os
from dotenv import load_dotenv

load_dotenv()

def create_weaviate_client():
    """Create and return Weaviate client"""
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
            auth_credentials=wvc.init.Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
        )
        return client
    except Exception as e:
        print(f"Could not connect to Weaviate: {e}")
        return None

def create_stock_collection(client):
    """Create the stock data collection with proper schema"""
    
    # Delete collection if it exists
    if client.collections.exists("StockData"):
        client.collections.delete("StockData")
        print("Deleted existing StockData collection")
    
    # Create the collection with schema
    collection = client.collections.create(
        name="StockData",
        vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_weaviate(model="Snowflake/snowflake-arctic-embed-l-v2.0"),
        generative_config=wvc.config.Configure.Generative.friendliai(model="meta-llama-3.3-70b-instruct"),
        properties=[
            wvc.config.Property(
                name="ticker",
                data_type=wvc.config.DataType.TEXT,
                description="Stock ticker symbol"
            ),
            wvc.config.Property(
                name="date",
                data_type=wvc.config.DataType.DATE,
                description="Trading date"
            ),
            wvc.config.Property(
                name="open_price",
                data_type=wvc.config.DataType.NUMBER,
                description="Opening price for the trading day"
            ),
            wvc.config.Property(
                name="close_price",
                data_type=wvc.config.DataType.NUMBER,
                description="Closing price for the trading day"
            ),
            wvc.config.Property(
                name="high_price",
                data_type=wvc.config.DataType.NUMBER,
                description="Highest price during the trading day"
            ),
            wvc.config.Property(
                name="low_price",
                data_type=wvc.config.DataType.NUMBER,
                description="Lowest price during the trading day"
            ),
            wvc.config.Property(
                name="volume_traded",
                data_type=wvc.config.DataType.INT,
                description="Number of shares traded"
            ),
            wvc.config.Property(
                name="market_cap",
                data_type=wvc.config.DataType.NUMBER,
                description="Market capitalization"
            ),
            wvc.config.Property(
                name="pe_ratio",
                data_type=wvc.config.DataType.NUMBER,
                description="Price-to-earnings ratio"
            ),
            wvc.config.Property(
                name="dividend_yield",
                data_type=wvc.config.DataType.NUMBER,
                description="Dividend yield percentage"
            ),
            wvc.config.Property(
                name="eps",
                data_type=wvc.config.DataType.NUMBER,
                description="Earnings per share"
            ),
            wvc.config.Property(
                name="week_52_high",
                data_type=wvc.config.DataType.NUMBER,
                description="52-week high price"
            ),
            wvc.config.Property(
                name="week_52_low",
                data_type=wvc.config.DataType.NUMBER,
                description="52-week low price"
            ),
            wvc.config.Property(
                name="sector",
                data_type=wvc.config.DataType.TEXT,
                description="Industry sector of the company"
            ),
            wvc.config.Property(
                name="content",
                data_type=wvc.config.DataType.TEXT,
                description="Rich text content for semantic search and embeddings"
            ),
        ]
    )
    
    print("✅ Created StockData collection successfully")
    return collection

def main():
    
    try:
        # Create client
        client = create_weaviate_client()
        
        if client is None:
            print("❌ Failed to connect to Weaviate")
            return
        
        print(client.is_connected())
        print("✅ Connected to Weaviate cluster")
        
        # Create collection
        collection = create_stock_collection(client)
        
        # Verify collection exists
        if client.collections.exists("StockData"):
            print("✅ StockData collection created and verified")
        else:
            print("❌ Failed to create StockData collection")
        
        # Print schema information
        schema = client.collections.get("StockData").config.get()
        print(f"\nCollection Schema:")
        print(f"- Name: {schema.name}")
        print(f"- Vectorizer: {schema.vectorizer_config}")
        print(f"- Properties: {len(schema.properties)} properties")
        
    except Exception as e:
        print(f"Error: {e}")
    

if __name__ == "__main__":
    main()