import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

class StockDataParser:
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.parsed_data = []
    
    def parse_csv_files(self) -> List[Dict[str, Any]]:
        """Parse all CSV files in the data directory and return structured data for Weaviate"""
        csv_files = list(self.data_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            print(f"Processing {csv_file.name}...")
            df = pd.read_csv(csv_file)
            
            # Standardize date format if needed
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
            
            # Convert each row to a structured format for Weaviate
            for _, row in df.iterrows():
                stock_data = self._create_stock_object(row)
                self.parsed_data.append(stock_data)
        
        return self.parsed_data
    
    def _create_stock_object(self, row: pd.Series) -> Dict[str, Any]:
        """Create a structured stock object for Weaviate ingestion"""
        return {
            "ticker": str(row.get('Ticker', '')),
            "date": row.get('Date').isoformat() if pd.notna(row.get('Date')) else '',
            "open_price": float(row.get('Open Price', 0)) if pd.notna(row.get('Open Price')) else 0.0,
            "close_price": float(row.get('Close Price', 0)) if pd.notna(row.get('Close Price')) else 0.0,
            "high_price": float(row.get('High Price', 0)) if pd.notna(row.get('High Price')) else 0.0,
            "low_price": float(row.get('Low Price', 0)) if pd.notna(row.get('Low Price')) else 0.0,
            "volume_traded": int(row.get('Volume Traded', 0)) if pd.notna(row.get('Volume Traded')) else 0,
            "market_cap": float(row.get('Market Cap', 0)) if pd.notna(row.get('Market Cap')) else 0.0,
            "pe_ratio": float(row.get('PE Ratio', 0)) if pd.notna(row.get('PE Ratio')) else 0.0,
            "dividend_yield": float(row.get('Dividend Yield', 0)) if pd.notna(row.get('Dividend Yield')) else 0.0,
            "eps": float(row.get('EPS', 0)) if pd.notna(row.get('EPS')) else 0.0,
            "week_52_high": float(row.get('52 Week High', 0)) if pd.notna(row.get('52 Week High')) else 0.0,
            "week_52_low": float(row.get('52 Week Low', 0)) if pd.notna(row.get('52 Week Low')) else 0.0,
            "sector": str(row.get('Sector', '')),
            # Create searchable text content for embeddings
            "content": self._create_searchable_content(row)
        }
    
    def _create_searchable_content(self, row: pd.Series) -> str:
        """Create rich text content for semantic search"""
        ticker = row.get('Ticker', 'Unknown')
        sector = row.get('Sector', 'Unknown')
        date = row.get('Date', 'Unknown')
        close_price = row.get('Close Price', 0)
        market_cap = row.get('Market Cap', 0)
        pe_ratio = row.get('PE Ratio', 0)
        dividend_yield = row.get('Dividend Yield', 0)
        
        content = f"""
        Stock: {ticker} in {sector} sector.
        Trading date: {date}
        Closing price: ${close_price:.2f}
        Market capitalization: ${market_cap:,.2f}
        Price-to-earnings ratio: {pe_ratio}
        Dividend yield: {dividend_yield}%
        
        This is a {sector} company with ticker symbol {ticker} that closed at ${close_price:.2f}.
        The company has a market cap of ${market_cap:,.2f} and trades with a P/E ratio of {pe_ratio}.
        """
        
        return content.strip()
    
    def export_to_json(self, output_file: str = "parsed_stock_data.json") -> str:
        """Export parsed data to JSON file"""
        output_path = self.data_dir / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.parsed_data, f, indent=2, default=str)
        
        print(f"Exported {len(self.parsed_data)} records to {output_path}")
        return str(output_path)
    
    def get_sample_data(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get sample data for testing"""
        return self.parsed_data[:n]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about parsed data"""
        if not self.parsed_data:
            return {"total_records": 0}
        
        sectors = set(item['sector'] for item in self.parsed_data)
        tickers = set(item['ticker'] for item in self.parsed_data)
        
        return {
            "total_records": len(self.parsed_data),
            "unique_sectors": len(sectors),
            "unique_tickers": len(tickers),
            "sectors": list(sectors),
            "date_range": {
                "start": min(item['date'] for item in self.parsed_data if item['date']),
                "end": max(item['date'] for item in self.parsed_data if item['date'])
            }
        }

def main():
    parser = StockDataParser()
    data = parser.parse_csv_files()
    
    print(f"\nParsed {len(data)} stock records")
    print("\nSample data:")
    for item in parser.get_sample_data(3):
        print(f"- {item['ticker']} ({item['sector']}) - ${item['close_price']:.2f}")
    
    print("\nDataset statistics:")
    stats = parser.get_stats()
    for key, value in stats.items():
        print(f"- {key}: {value}")
    
    # Export to JSON
    output_file = parser.export_to_json()
    print(f"\nData exported to: {output_file}")

if __name__ == "__main__":
    main()