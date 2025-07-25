# CLAUDE.md - AI Stock Analysis Microservice

## Project Overview
This microservice provides a RESTful API for fetching stock data and AI-powered analysis for both South African (JSE) and US stock markets using yfinance and CrewAI.

## Architecture

### Core Components
1. **FastAPI** - Web framework for building the API
2. **yfinance** - Stock data fetching library
3. **CrewAI** - Agent framework for AI-powered analysis
4. **Pydantic** - Data validation and settings management
5. **Redis** (optional) - Caching for API responses

### Directory Structure
```
stock-analysis-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── stock.py         # Stock data models
│   │   └── analysis.py      # Analysis response models
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── stock_service.py # Stock data fetching
│   │   └── analysis_service.py # AI analysis
│   ├── agents/              # CrewAI agents
│   │   ├── __init__.py
│   │   ├── stock_analyst.py # Stock analysis agent
│   │   ├── market_researcher.py # Market research agent
│   │   └── investment_advisor.py # Investment recommendation agent
│   ├── routers/             # API routes
│   │   ├── __init__.py
│   │   ├── stocks.py        # Stock data endpoints
│   │   └── analysis.py      # Analysis endpoints
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── validators.py    # Input validation
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-container setup
├── .env.example            # Environment variables template
└── README.md               # Project documentation
```

## API Endpoints

### Stock Data Endpoints

#### 1. Get Stock Information
```
GET /api/v1/stocks/{symbol}
Query Parameters:
  - market: "US" | "ZA" (default: "US")
  - period: "1d" | "5d" | "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y" | "10y" | "ytd" | "max"
  - interval: "1m" | "2m" | "5m" | "15m" | "30m" | "60m" | "90m" | "1h" | "1d" | "5d" | "1wk" | "1mo" | "3mo"

Response:
{
  "symbol": "AAPL",
  "market": "US",
  "company_name": "Apple Inc.",
  "current_price": 150.25,
  "currency": "USD",
  "historical_data": [...],
  "volume": 75000000,
  "market_cap": 2500000000000,
  "pe_ratio": 25.5,
  "dividend_yield": 0.5
}
```

#### 2. Search Stocks
```
GET /api/v1/stocks/search
Query Parameters:
  - query: string (company name or ticker)
  - market: "US" | "ZA" | "ALL"
  - limit: integer (default: 10)

Response:
{
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "market": "US",
      "sector": "Technology"
    }
  ]
}
```

#### 3. Get Multiple Stocks
```
POST /api/v1/stocks/batch
Body:
{
  "symbols": ["AAPL", "GOOGL", "NPN.JO"],
  "period": "1mo",
  "interval": "1d"
}

Response:
{
  "stocks": [...]
}
```

### Analysis Endpoints

#### 1. Get Stock Analysis
```
GET /api/v1/analysis/{symbol}
Query Parameters:
  - market: "US" | "ZA"
  - analysis_type: "technical" | "fundamental" | "sentiment" | "comprehensive"

Response:
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:30:00Z",
  "recommendation": "BUY" | "HOLD" | "SELL",
  "confidence_score": 0.85,
  "target_price": 165.50,
  "analysis": {
    "technical_indicators": {
      "rsi": 45.2,
      "macd": "bullish",
      "moving_averages": {...}
    },
    "fundamental_analysis": {
      "valuation": "undervalued",
      "growth_prospects": "strong",
      "financial_health": "excellent"
    },
    "reasons": [
      {
        "factor": "Strong earnings growth",
        "impact": "positive",
        "weight": 0.3
      }
    ]
  },
  "risks": [...],
  "opportunities": [...]
}
```

#### 2. Compare Stocks
```
POST /api/v1/analysis/compare
Body:
{
  "symbols": ["AAPL", "MSFT"],
  "metrics": ["performance", "valuation", "growth", "risk"]
}

Response:
{
  "comparison": {...},
  "recommendation": "AAPL",
  "reasoning": [...]
}
```

#### 3. Portfolio Analysis
```
POST /api/v1/analysis/portfolio
Body:
{
  "holdings": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "purchase_price": 140.00
    }
  ]
}

Response:
{
  "total_value": 15025.00,
  "total_gain_loss": 1025.00,
  "recommendations": [...],
  "rebalancing_suggestions": [...]
}
```

## CrewAI Agent Configuration

### Agent Roles

1. **Market Researcher Agent**
   - Gathers market data and trends
   - Analyzes sector performance
   - Identifies market catalysts

2. **Technical Analyst Agent**
   - Calculates technical indicators
   - Identifies chart patterns
   - Provides entry/exit points

3. **Fundamental Analyst Agent**
   - Analyzes financial statements
   - Evaluates company metrics
   - Assesses intrinsic value

4. **Risk Analyst Agent**
   - Identifies potential risks
   - Calculates risk metrics
   - Provides risk mitigation strategies

5. **Investment Advisor Agent**
   - Synthesizes all analyses
   - Provides final recommendations
   - Generates investment rationale

### Agent Workflow
```
1. User requests analysis for symbol
2. Market Researcher gathers current data
3. Technical & Fundamental Analysts process in parallel
4. Risk Analyst evaluates findings
5. Investment Advisor synthesizes and recommends
6. API returns structured response
```

## Data Models

### Stock Model
```python
class StockData(BaseModel):
    symbol: str
    market: Literal["US", "ZA"]
    company_name: str
    current_price: float
    currency: str
    change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    historical_data: List[HistoricalDataPoint]
```

### Analysis Model
```python
class StockAnalysis(BaseModel):
    symbol: str
    timestamp: datetime
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_score: float
    target_price: Optional[float]
    analysis: AnalysisDetails
    risks: List[RiskFactor]
    opportunities: List[Opportunity]
```

## Environment Variables
```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-api-key-here

# CrewAI Configuration
OPENAI_API_KEY=your-openai-key
CREW_AI_MODEL=gpt-4o-mini

# Cache Configuration
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Market Data
YFINANCE_TIMEOUT=30
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "The requested stock symbol was not found",
    "details": {
      "symbol": "INVALID",
      "market": "US"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes
- `STOCK_NOT_FOUND` - Invalid stock symbol
- `MARKET_CLOSED` - Market is currently closed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `ANALYSIS_FAILED` - AI analysis failed
- `INVALID_PARAMETERS` - Invalid request parameters

## Performance Considerations

1. **Caching Strategy**
   - Cache stock data for 1 hour
   - Cache analysis results for 1 day
   - Use Redis for distributed caching

2. **Rate Limiting**
   - 10 requests per minute per API key
   - 500 requests per day per API key

3. **Async Operations**
   - All external API calls should be async
   - Use connection pooling for database

4. **Data Optimization**
   - Paginate large result sets
   - Compress historical data responses
   - Use streaming for real-time data

## Security

1. **Authentication**
   - API key authentication
   - JWT tokens for user sessions

2. **Input Validation**
   - Validate all stock symbols
   - Sanitize user inputs
   - Limit request sizes

3. **Rate Limiting**
   - Per-user rate limits
   - DDoS protection

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
1. Use Gunicorn with Uvicorn workers
2. Set up health check endpoints
3. Configure logging and monitoring
4. Use environment-specific configurations
5. Set up CI/CD pipeline

## Testing Strategy

1. **Unit Tests**
   - Test individual service methods
   - Mock external API calls
   - Test data transformations

2. **Integration Tests**
   - Test API endpoints
   - Test CrewAI agent workflows
   - Test caching behavior

3. **Performance Tests**
   - Load testing with Locust
   - Stress test analysis endpoints
   - Monitor response times

## Monitoring

1. **Application Metrics**
   - API response times
   - Error rates
   - Cache hit rates

2. **Business Metrics**
   - Most analyzed stocks
   - Analysis accuracy
   - User engagement

3. **System Metrics**
   - CPU/Memory usage
   - Database connections
   - External API latency
