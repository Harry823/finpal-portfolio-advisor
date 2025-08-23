"""
Enhanced AI Engine with Web Search + FriendliAI Integration
Refactored with hardcoded API keys + correct Friendli chat-completions usage.
Adds:
- Debug mode to print raw prompt and raw model output
- Final conclusion field in strict JSON
- LLM-based company name extraction
"""
import re
import json
import time
import logging
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# -------- Configuration --------
DEBUG_RAW = True  # Set to False to silence raw prompt/response
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("finpal")

FRIENDLI_API_KEY = "flp_ZAWxFW8oJQv5eeEB6Z7XdotbyLUnAQNP1Sc7xuvfoY3049"
FRIENDLI_MODEL_ID = "depjr7ycw7u9mq1"  # Your dedicated endpoint ID
FRIENDLI_CHAT_URL = "https://api.friendli.ai/dedicated/v1/chat/completions"
TAVILY_API_KEY = "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"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

# # -------- API Keys (replace if you rotate) --------

# -------- Data Models --------
@dataclass
class WebDoc:
    """Web document from search results"""
    id: str
    title: str
    url: str
    snippet: str

@dataclass
class EnhancedInsightResponse:
    """Enhanced insight response with web sources and conclusion"""
    ticker: Optional[str]
    company: str
    positives: List[str]
    negatives: List[str]
    summary: str
    explanations: List[Dict[str, Any]]
    conclusion: Dict[str, Any]
    search_timestamp: datetime
    sources_analyzed: int

# Add these models after your existing dataclasses
class AnalysisRequest(BaseModel):
    query: str
    company: Optional[str] = None

class AnalysisResponse(BaseModel):
    rationale: str
    company: str
    timestamp: str

# -------- Enhanced AI Engine --------
class EnhancedFriendliAIEngine:
    """Enhanced AI engine with Tavily web search + Friendli dedicated endpoint."""

    def __init__(self):
        """Initialize the AI engine with prompts and schemas"""
        # System directive for consistent AI responses
        self.system_directive = (
            "You are FinPal, a rigorous finance research assistant.\n"
            "You MUST output STRICT JSON ONLY, matching the schema below. Do not add commentary.\n"
            "Ground every claim in the supplied sources and include the source_id used.\n"
            "Any numeric claim must be supported by a cited source_id. If unsure, write 'Insufficient recent evidence [S#]'.\n"
            "Never fabricate numbers.\n"
        )

        # JSON schema for structured output
        self.json_schema = """{
  "ticker": "<optional-ticker-or-null>",
  "company": "<company name>",
  "positives": ["<bullet 1>", "<bullet 2>", "<bullet 3>", "<bullet 4>", "<bullet 5>"],
  "negatives": ["<bullet 1>", "<bullet 2>", "<bullet 3>", "<bullet 4>", "<bullet 5>"],
  "summary": "<3-5 sentences, balanced, with trade-offs and [S#] citations>",
  "explanations": [
    {"claim": "<short claim>", "source_id": "S3", "confidence": 0.0}
  ],
  "conclusion": {
    "stance": "buy|hold|avoid",
    "confidence": 0.0,
    "rationale": "<1-2 sentences tying positives/negatives to stance; include [S#] if factual>"
  }
}"""

    # -------- Company Name Extraction --------
    def extract_company_name(self, user_text: str) -> str:
        """Use LLM to intelligently extract company name from user text"""
        company_extraction_prompt = f"""
Extract the company name from this user query. Return ONLY the company name, nothing else.

User query: "{user_text}"

Company name:"""

        try:
            headers = {
                "Authorization": f"Bearer {FRIENDLI_API_KEY}",
                "Content-Type": "application/json",
            }
            
            body = {
                "model": FRIENDLI_MODEL_ID,
                "messages": [
                    {"role": "system", "content": "You are a company name extractor. Return only the company name, no other text."},
                    {"role": "user", "content": company_extraction_prompt}
                ],
                "max_tokens": 50,
                "temperature": 0.1,
                "stream": False,
            }

            response = requests.post(FRIENDLI_CHAT_URL, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            
            company_name = response.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"LLM extracted company: {company_name}")
            return company_name

        except Exception as e:
            logger.warning(f"LLM company extraction failed: {e}, falling back to simple extraction")
            return self._fallback_company_extraction(user_text)

    def _fallback_company_extraction(self, text: str) -> str:
        """Fallback company extraction using regex patterns"""
        if not text:
            return "Unknown Company"
        
        # Look for common company patterns
        text = text.replace("\n", " ")
        
        # Pattern 1: Look for capitalized company names
        candidates = re.findall(r"(?:[A-Z][a-zA-Z&\.\-]+(?:\s|,|\.|&|-)){1,4}", text)
        candidates = [re.sub(r"[^\w\s\.\-&]", "", c).strip(" ,.-") for c in candidates]
        
        if candidates:
            return sorted(candidates, key=len, reverse=True)[0][:80]
        
        # Pattern 2: Look for common company indicators
        company_indicators = ["Tesla", "Apple", "Microsoft", "Google", "Amazon", "Meta", "Netflix"]
        for indicator in company_indicators:
            if indicator.lower() in text.lower():
                return indicator
        
        return "Unknown Company"

    # -------- JSON Processing --------
    def _extract_first_json_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse the first JSON block from text"""
        if not text:
            return None
        
        # Look for JSON content between backticks if present
        if "```json" in text:
            start_marker = "```json"
            end_marker = "```"
            start_idx = text.find(start_marker) + len(start_marker)
            end_idx = text.find(end_marker, start_idx)
            if start_idx > 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx].strip()
            else:
                # Fallback to regular JSON extraction
                start_idx = text.find("{")
                end_idx = text.rfind("}")
                if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                    return None
                json_str = text[start_idx:end_idx + 1]
        else:
            # Regular JSON extraction
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                return None
            json_str = text[start_idx:end_idx + 1]
        
        try:
            # Clean up common JSON issues
            json_str = json_str.replace("[S#1]", "[S1]")
            json_str = json_str.replace("[S#2]", "[S2]")
            json_str = json_str.replace("[S#3]", "[S3]")
            json_str = json_str.replace("[S#4]", "[S4]")
            json_str = json_str.replace("[S#5]", "[S5]")
            json_str = json_str.replace("[S#6]", "[S6]")
            json_str = json_str.replace("[S#7]", "[S7]")
            json_str = json_str.replace("[S#8]", "[S8]")
            json_str = json_str.replace("[S#9]", "[S9]")
            json_str = json_str.replace("[S#10]", "[S10]")
            
            # Also fix any remaining [S# pattern
            json_str = re.sub(r'\[S#(\d+)\]', r'[S\1]', json_str)
            
            parsed = json.loads(json_str)
            logger.info("Successfully parsed JSON response")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw JSON string: {json_str}")
            return None

    # -------- Web Search --------
    def tavily_search(self, query: str, max_results: int = 10) -> List[WebDoc]:
        """Search for latest company information using Tavily API"""
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_images": False,
        }
        
        try:
            response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            docs: List[WebDoc] = []
            
            for i, item in enumerate(data.get("results", []), start=1):
                docs.append(WebDoc(
                    id=f"S{i}",
                    title=(item.get("title") or "")[:160],
                    url=item.get("url") or "",
                    snippet=((item.get("content") or item.get("snippet") or "")[:650]),
                ))
            
            logger.info(f"Tavily search: '{query}' -> {len(docs)} results")
            return docs
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    def _build_sources_block(self, docs: List[WebDoc]) -> str:
        """Build formatted sources block for the prompt"""
        lines = []
        for doc in docs:
            lines.append(f"[{doc.id}] {doc.title}\nURL: {doc.url}\nSnippet: {doc.snippet}\n")
        return "\n".join(lines)

    # -------- AI Generation --------
    def friendli_generate(self, prompt: str, max_tokens: int = 900, temperature: float = 0.2) -> str:
        """Generate insights using FriendliAI dedicated endpoint"""
        headers = {
            "Authorization": f"Bearer {FRIENDLI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        body = {
            "model": FRIENDLI_MODEL_ID,
            "messages": [
                {"role": "system", "content": self.system_directive},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        # Debug output
        if DEBUG_RAW:
            print("\n===== PROMPT SENT TO FRIENDLI =====\n")
            print(self.system_directive)
            print(prompt)
            print("\n===================================\n")

        logger.info(f"Friendli chat call (model={FRIENDLI_MODEL_ID})")
        
        try:
            response = requests.post(FRIENDLI_CHAT_URL, headers=headers, json=body, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = (data["choices"][0]["message"].get("content") or "").strip()

            # Debug output
            if DEBUG_RAW:
                print("\n===== RAW MODEL OUTPUT (BEFORE JSON EXTRACT) =====\n")
                print(content)
                print("\n===================================================\n")

            return content
            
        except Exception as e:
            logger.error(f"FriendliAI generation failed: {e}")
            raise

    def build_enhanced_prompt(self, user_text: str, company_guess: str, sources: List[WebDoc]) -> str:
        """Build comprehensive prompt for AI analysis"""
        return f"""User input: "{user_text}"

Company (guess): {company_guess}

SOURCES
-------
{self._build_sources_block(sources)}

TASK
----
1) Produce exactly 5 positives and 5 negatives about {company_guess}, grounded in the sources, each concise with [S1], [S2], [S3] etc. citations.
2) Write a balanced 3–5 sentence summary with [S1], [S2], [S3] etc. citations where factual.
3) Provide 'explanations' array mapping claims to source_id (e.g., "S1", "S2") and confidence (0.0 to 1.0).
4) Provide a final 'conclusion' object:
   - stance: one of buy|hold|avoid
   - confidence: float 0..1
   - rationale: 1–2 sentences that reference the most decisive factors (include [S1], [S2] etc. if factual)
5) Output STRICT JSON matching this schema exactly:
{self.json_schema}

IMPORTANT: Use [S1], [S2], [S3] etc. for source citations, NOT [S#1] or [S#2].
You MUST output valid JSON that matches the schema exactly.
"""

    # -------- Main Analysis API --------
    def analyze_company_from_text(self, user_text: str, k_search: int = 10):
        """Analyze company from user text using web search + FriendliAI. Returns (analysis, sources)."""
        try:
            logger.info(f"Starting analysis for: {user_text[:120]}...")
            
            # Extract company name using LLM
            company = self.extract_company_name(user_text)
            logger.info(f"Company identified: {company}")

            # Perform web search
            search_query = f"{company} latest news earnings outlook risks opportunities"
            docs = self.tavily_search(search_query, max_results=k_search)
            
            if not docs:
                logger.warning("No web results found; returning fallback response")
                return self._create_fallback_response(company), []

            # Generate AI insights
            prompt = self.build_enhanced_prompt(user_text, company, docs)
            
            try:
                raw_response = self.friendli_generate(prompt)
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                return self._create_fallback_response(company), docs

            # Parse and return results
            parsed_data = self._extract_first_json_block(raw_response) or {}
            
            analysis = EnhancedInsightResponse(
                ticker=parsed_data.get("ticker"),
                company=parsed_data.get("company", company),
                positives=parsed_data.get("positives", []),
                negatives=parsed_data.get("negatives", []),
                summary=parsed_data.get("summary", ""),
                explanations=parsed_data.get("explanations", []),
                conclusion=parsed_data.get("conclusion", {
                    "stance": "hold", 
                    "confidence": 0.0, 
                    "rationale": "No conclusion available"
                }),
                search_timestamp=datetime.utcnow(),
                sources_analyzed=len(docs)
            )
            
            return analysis, docs
            
        except Exception as e:
            logger.error(f"Unexpected analysis failure: {e}")
            return self._create_fallback_response("Unknown Company"), []

    def _create_fallback_response(self, company: str) -> EnhancedInsightResponse:
        """Create fallback response when analysis fails"""
        return EnhancedInsightResponse(
            ticker=None,
            company=company,
            positives=[],
            negatives=[],
            summary=f"Unable to complete analysis for {company} at this time.",
            explanations=[],
            conclusion={
                "stance": "hold", 
                "confidence": 0.0, 
                "rationale": "Insufficient data for analysis"
            },
            search_timestamp=datetime.utcnow(),
            sources_analyzed=0
        )

# -------- Helper Functions --------
def analyze_to_json(sentence: str) -> dict:
    """Programmatic helper that returns analysis as JSON dict"""
    engine = EnhancedFriendliAIEngine()
    result = engine.analyze_company_from_text(sentence)
    
    return {
        "ticker": result.ticker,
        "company": result.company,
        "positives": result.positives,
        "negatives": result.negatives,
        "summary": result.summary,
        "explanations": result.explanations,
        "conclusion": result.conclusion,
        "sources_analyzed": result.sources_analyzed,
        "timestamp_utc": result.search_timestamp.isoformat()
    }

# -------- Export Functions --------
def export_analysis_to_json(analysis: EnhancedInsightResponse, sources: List[WebDoc], filename: str = None):
    """Export just the rationale with stance to a simple JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tesla_rationale_{timestamp}.json"
    
    # Get the stance and rationale
    stance = analysis.conclusion.get("stance", "unknown")
    rationale = analysis.conclusion.get("rationale", "No rationale available")
    
    # Combine them with stance at the end
    full_rationale = f"{rationale} Final recommendation: {stance.upper()}."
    
    # Just the rationale with stance
    export_data = {
        "rationale": full_rationale
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Rationale with stance exported to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to export: {e}")
        return None

# Initialize the engine BEFORE the FastAPI app
engine = EnhancedFriendliAIEngine()

# Create the FastAPI app
app = FastAPI(title="FinPal Sentiment API", version="1.0.0")

# Configure CORS to allow requests from localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(request: AnalysisRequest):
    """Analyze a stock based on user query"""
    try:
        # Get the raw LLM response directly
        company = engine.extract_company_name(request.query)
        
        # Simple search and prompt
        search_query = f"{company} latest news earnings outlook risks opportunities"
        docs = engine.tavily_search(search_query, max_results=8)
        
        if not docs:
            return AnalysisResponse(
                rationale="Unable to find recent data for analysis. Consider a different approach.",
                company=company,
                timestamp=datetime.now().isoformat()
            )
        
        # Build simple prompt
        prompt = f"""Based on these sources about {company}, give me a simple investment recommendation in 1-2 sentences. Should I buy, hold, or avoid this stock and why?

Sources:
{engine._build_sources_block(docs)}

Recommendation:"""
        
        # Get raw LLM response
        raw_response = engine.friendli_generate(prompt)
        
        # Clean up the response (remove markdown if present)
        if "```" in raw_response:
            raw_response = raw_response.replace("```", "").strip()
        
        return AnalysisResponse(
            rationale=raw_response,
            company=company,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return AnalysisResponse(
            rationale=f"Analysis failed: {str(e)}",
            company="Unknown",
            timestamp=datetime.now().isoformat()
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FinPal Sentiment API"}

if __name__ == "__main__":
    print("🚀 Starting FinPal Sentiment API...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
