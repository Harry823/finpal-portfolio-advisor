import weaviate
import weaviate.classes as wvc
import os
from dotenv import load_dotenv

load_dotenv()

def create_weaviate_client():
    """Create and return Weaviate client"""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
        auth_credentials=wvc.init.Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
        
    )
    return client

def semantic_search(client, query, limit=5):
    """Perform semantic search on stock data"""
    collection = client.collections.get("StockData")
    
    print(f"🔍 Searching for: '{query}'")
    print("-" * 50)
    
    # Perform vector search
    response = collection.query.near_text(
        query=query,
        limit=limit,
        return_metadata=wvc.query.MetadataQuery(score=True)
    )
    
    results = []
    for i, obj in enumerate(response.objects, 1):
        properties = obj.properties
        score = obj.metadata.score if obj.metadata else "N/A"
        
        result = {
            "rank": i,
            "ticker": properties['ticker'],
            "sector": properties['sector'],
            "close_price": properties['close_price'],
            "date": properties['date'],
            "market_cap": properties['market_cap'],
            "pe_ratio": properties['pe_ratio'],
            "dividend_yield": properties['dividend_yield'],
            "content": properties['content'][:200] + "...",
            "score": score
        }
        results.append(result)
        
        print(f"{i}. {properties['ticker']} ({properties['sector']})")
        print(f"   Price: ${properties['close_price']:.2f}")
        print(f"   Date: {properties['date']}")
        print(f"   Market Cap: ${properties['market_cap']:,.2f}")
        print(f"   P/E Ratio: {properties['pe_ratio']}")
        print(f"   Score: {score}")
        print(f"   Content: {properties['content'][:150]}...")
        print()
    
    return results

def test_semantic_searches(client):
    """Test various semantic search queries"""
    
    test_queries = [
        "technology companies with high growth potential",
        "dividend paying stocks with stable returns",
        "healthcare companies with strong earnings",
        "energy sector stocks trading below market average",
        "financial companies with low PE ratios",
        "consumer discretionary stocks with high market cap"
    ]
    
    for query in test_queries:
        results = semantic_search(client, query, limit=3)
        print("=" * 70)
        print()

def interactive_search(client):
    """Interactive semantic search interface"""
    print("🔍 Interactive Semantic Search")
    print("Enter search queries (type 'quit' to exit):")
    print("-" * 50)
    
    while True:
        query = input("\nEnter your search query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        try:
            results = semantic_search(client, query, limit=5)
            print(f"\nFound {len(results)} results")
        except Exception as e:
            print(f"Error performing search: {e}")

def search_by_sector(client, sector_name, limit=5):
    """Search for stocks in a specific sector"""
    collection = client.collections.get("StockData")
    
    print(f"🏢 Searching for stocks in {sector_name} sector")
    print("-" * 50)
    
    # Use where filter for exact sector match
    response = collection.query.fetch_objects(
        where=wvc.query.Filter.by_property("sector").equal(sector_name),
        limit=limit
    )
    
    results = []
    for i, obj in enumerate(response.objects, 1):
        properties = obj.properties
        
        result = {
            "rank": i,
            "ticker": properties['ticker'],
            "close_price": properties['close_price'],
            "date": properties['date'],
            "market_cap": properties['market_cap'],
            "pe_ratio": properties['pe_ratio']
        }
        results.append(result)
        
        print(f"{i}. {properties['ticker']}")
        print(f"   Price: ${properties['close_price']:.2f}")
        print(f"   Date: {properties['date']}")
        print(f"   Market Cap: ${properties['market_cap']:,.2f}")
        print(f"   P/E Ratio: {properties['pe_ratio']}")
        print()
    
    return results

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
        
        # Test different search types
        print("🧪 Testing semantic searches...")
        test_semantic_searches(client)
        
        # Interactive search
        interactive_search(client)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()