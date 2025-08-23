import weaviate
import weaviate.classes as wvc
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()

def create_weaviate_client():
    """Create and return Weaviate client"""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
        auth_credentials=wvc.init.Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
    )
    return client

def populate_stock_data(client, batch_size=100):
    """Populate the StockData collection with parsed stock data"""
    
    # Get the collection
    collection = client.collections.get("StockData")
    
    # Load parsed data from JSON
    json_path = "../data/parsed_stock_data.json"  # from scripts/ directory
    if not os.path.exists(json_path):
        json_path = "data/parsed_stock_data.json"  # from backend/ directory
    
    with open(json_path, "r") as f:
        stock_data = json.load(f)
    
    if len(stock_data) == 0:
        print("❌ No data found. Check if parsed_stock_data.json exists in ../data directory")
        return 0
    
    print(f"Loading {len(stock_data)} stock records...")
    
    # Process data in batches
    total_records = len(stock_data)
    successful_imports = 0
    
    for i in range(0, total_records, batch_size):
        batch = stock_data[i:i + batch_size]
        batch_objects = []
        
        for item in batch:
            # Convert date string to datetime object with timezone
            date_obj = item['date']
            if isinstance(date_obj, str):
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
                if date_obj.tzinfo is None:
                    date_obj = date_obj.replace(tzinfo=timezone.utc)
            
            batch_objects.append(
                wvc.data.DataObject(
                    properties={
                        "ticker": item['ticker'],
                        "date": date_obj,
                        "open_price": item['open_price'],
                        "close_price": item['close_price'],
                        "high_price": item['high_price'],
                        "low_price": item['low_price'],
                        "volume_traded": item['volume_traded'],
                        "market_cap": item['market_cap'],
                        "pe_ratio": item['pe_ratio'],
                        "dividend_yield": item['dividend_yield'],
                        "eps": item['eps'],
                        "week_52_high": item['week_52_high'],
                        "week_52_low": item['week_52_low'],
                        "sector": item['sector'],
                        "content": item['content']
                    }
                )
            )
        
        try:
            # Insert batch
            response = collection.data.insert_many(batch_objects)
            
            # Check for errors
            if response.has_errors:
                print(f"Batch {i//batch_size + 1}: {len(response.errors)} errors")
                for error in response.errors:
                    print(f"  Error: {error}")
            else:
                successful_imports += len(batch_objects)
                print(f"✅ Batch {i//batch_size + 1}: Imported {len(batch_objects)} records")
                
        except Exception as e:
            print(f"❌ Error importing batch {i//batch_size + 1}: {e}")
    
    print(f"\n✅ Import complete: {successful_imports}/{total_records} records imported successfully")
    
    # Verify import
    total_count = collection.aggregate.over_all().total_count
    print(f"✅ Total records in collection: {total_count}")
    
    return successful_imports

def verify_data(client):
    """Verify that data was imported correctly"""
    collection = client.collections.get("StockData")
    
    # Get sample records
    response = collection.query.fetch_objects(limit=3)
    
    print("\nSample records:")
    for obj in response.objects:
        properties = obj.properties
        print(f"- {properties['ticker']} ({properties['sector']}) - ${properties['close_price']:.2f} on {properties['date']}")
    
    # Get sector distribution
    sectors_response = collection.aggregate.over_all(
        group_by="sector"
    )
    
    print(f"\nSector distribution:")
    for group in sectors_response.groups:
        print(f"- {group.grouped_by['value']}: {group.total_count} records")

def main():
    try:
        # Create client
        client = create_weaviate_client()
        print("✅ Connected to Weaviate cluster")
        
        # Check if collection exists
        if not client.collections.exists("StockData"):
            print("❌ StockData collection does not exist. Please run 1_create_collection.py first.")
            return
        
        # Populate data
        imported_count = populate_stock_data(client)
        
        if imported_count > 0:
            # Verify data
            verify_data(client)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()