from flask import Flask, request, jsonify
from flask_cors import CORS
import weaviate
import weaviate.classes as wvc
import os
from dotenv import load_dotenv
from weaviate.classes.init import Auth

load_dotenv()

app = Flask(__name__)
CORS(app)

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

def investment_advisor(client, user_query, limit=10):
    """
    AI Investment Advisor - analyzes stocks based on user queries and provides investment recommendations
    """
    collection = client.collections.get("StockData")
    
    # Investment advisor prompt template
    advisor_prompt = f"""
    You are an expert investment advisor. Based on the user's question: "{user_query}"
    
    Analyze the provided stock market data and give a comprehensive investment recommendation including:
    
    1. **Company Names** : The names of the companies the user should invest in. 
    2. **Investment Recommendation**: Should the user invest? (BUY/HOLD/SELL/AVOID)
    3. **Key Reasons**: 3-5 bullet points explaining your recommendation
    4. **Risk Assessment**: What are the main risks?
    5. **Financial Metrics Analysis**: Comment on P/E ratios, market cap, dividend yields
    6. **Sector Context**: How does this perform within its sector?
    7. **Timeline**: Short-term vs long-term outlook
    9. **Portfolio Allocation**: What percentage of portfolio (if any) should this represent?
    
    Be specific, data-driven, and provide actionable advice. Use the actual numbers from the data.Limit each point to 1 line maximum
    
    Stock Market Data:
    {{context}}
    """
    
    # Perform generative search with investment focus
    response = collection.generate.near_text(
        query=user_query,
        limit=limit,
        grouped_task=advisor_prompt
    )
    
    return response.generated

@app.route('/api/stock-recommendation', methods=['POST'])
def stock_recommendation():
    """API endpoint to get stock investment recommendation"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text field. Please provide a text query in the request body.'
            }), 400
        
        query_text = data['text'].strip()
        
        if not query_text:
            return jsonify({
                'error': 'Query text cannot be empty.'
            }), 400
        
        # Create Weaviate client
        client = create_weaviate_client()
        
        # Check if collection exists and has data
        if not client.collections.exists("StockData"):
            return jsonify({
                'error': 'Stock data not available. Please contact support.'
            }), 503
        
        # Get investment recommendation
        recommendation = investment_advisor(client, query_text)
        
        return jsonify({
            'query': query_text,
            'recommendation': recommendation,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred while processing your request: {str(e)}'
        }), 500
        
    finally:
        if 'client' in locals() and client is not None:
            client.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        client = create_weaviate_client()
        
        if not client.collections.exists("StockData"):
            return jsonify({
                'status': 'unhealthy',
                'message': 'Stock data collection not found'
            }), 503
        
        collection = client.collections.get("StockData")
        total_count = collection.aggregate.over_all().total_count
        
        return jsonify({
            'status': 'healthy',
            'stock_records': total_count,
            'message': 'API is running and stock data is available'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Service unavailable: {str(e)}'
        }), 503
        
    finally:
        if 'client' in locals() and client is not None:
            client.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)