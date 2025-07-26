# AI Stock Analysis Microservice

A production-ready Python microservice for AI-powered stock and cryptocurrency analysis using FastAPI, yfinance, and OpenAI's GPT-4o-mini.

## Features

- **Multi-Market Support**: US stocks, South African stocks (JSE), and cryptocurrencies
- **Real-time Data**: Integration with yfinance for live market data
- **Technical Analysis**: RSI, SMA, MACD indicators automatically calculated
- **AI-Powered Analysis**: GPT-4o-mini provides BUY/HOLD/SELL recommendations with structured reasoning
- **Caching**: Redis caching for optimal performance (12h for data, 24h for analysis)
- **Portfolio Analysis**: Analyze holdings and get rebalancing suggestions
- **Stock Comparison**: Compare multiple assets side-by-side
- **Token Usage Tracking**: Monitor OpenAI API usage and costs
- **Test Frontend**: HTML interface for testing API endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for caching)
- OpenAI API key

### Installation

1. **Clone and setup environment:**

```bash
git clone <repository>
cd trader-agent
```

2. **Configure environment variables by creating `.env` file:**

```env
OPENAI_API_KEY=your-openai-api-key-here
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_MODEL=gpt-4o-mini
STOCK_DATA_CACHE_TTL=43200
ANALYSIS_CACHE_TTL=86400
LOG_LEVEL=INFO
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Run with Docker Compose (recommended):**

```bash
docker-compose up -d
```

Or run locally:

```bash
# Start Redis (if not using Docker)
redis-server

# Start the API
uvicorn app.main:app --reload
```

5. **Access the application:**

- **Test Frontend**: http://localhost:8000/ (Interactive HTML interface)
- **API Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## API Endpoints

### Health & Monitoring

#### Application Health
```http
GET /health
```

#### Analysis Service Health
```http
GET /api/v1/analysis/health
```

#### Token Usage Statistics
```http
GET /api/v1/analysis/tokens
```

### Stock Data

#### Get Individual Stock
```http
GET /api/v1/stocks/{symbol}?market=US&period=1mo&interval=1d
```

Examples:
```bash
curl "http://localhost:8000/api/v1/stocks/AAPL?market=US"
curl "http://localhost:8000/api/v1/stocks/NPN.JO?market=ZA"
curl "http://localhost:8000/api/v1/stocks/BTC-USD?market=CRYPTO"
```

#### Search Stocks
```http
GET /api/v1/stocks/search?query=apple&market=ALL&limit=10
```

#### Batch Stock Data
```http
POST /api/v1/stocks/batch
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOGL", "BTC-USD"],
  "period": "1mo",
  "interval": "1d"
}
```

### AI Analysis

#### Get Stock Analysis
```http
GET /api/v1/analysis/{symbol}?market=US
```

Returns comprehensive AI analysis with:
- BUY/HOLD/SELL recommendation
- Confidence score (0-1)
- Target price estimate
- Detailed reasoning and key points
- Risk assessment
- Technical indicators analysis
- Market context

Response format:
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:30:00Z",
  "recommendation": "BUY",
  "confidence_score": 0.85,
  "target_price": 165.50,
  "reasoning": [
    "Strong quarterly earnings growth",
    "Positive technical indicators",
    "Market leadership in AI space"
  ],
  "key_points": [...],
  "risks": [...],
  "technical_analysis": {
    "rsi": 45.2,
    "sma_20": 150.25,
    "sma_50": 148.80,
    "macd_signal": "bullish"
  }
}
```

#### Compare Stocks
```http
POST /api/v1/analysis/compare
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "metrics": ["performance", "valuation"]
}
```

#### Portfolio Analysis
```http
POST /api/v1/analysis/portfolio
Content-Type: application/json

{
  "holdings": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "purchase_price": 140.00
    }
  ]
}
```

## Symbol Formats

- **US Stocks**: Direct symbol (e.g., `AAPL`, `MSFT`, `TSLA`)
- **South African Stocks**: Add `.JO` suffix (e.g., `NPN.JO`, `SHP.JO`, `AGL.JO`)
- **Cryptocurrencies**: Add `-USD` suffix (e.g., `BTC-USD`, `ETH-USD`, `ADA-USD`)

## Test Frontend

The project includes a comprehensive HTML test interface at http://localhost:8000/ that provides:

- **Stock Data Testing**: Search and fetch individual or batch stock data
- **AI Analysis Testing**: Get AI-powered analysis for any stock symbol
- **Stock Comparison**: Compare multiple stocks side-by-side
- **Portfolio Analysis**: Test portfolio analysis functionality
- **Token Usage Monitoring**: View current session token usage and costs
- **Dark Theme**: Modern, professional interface

## Configuration

Key environment variables:

```env
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional (with defaults)
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_MODEL=gpt-4o-mini
STOCK_DATA_CACHE_TTL=43200  # 12 hours
ANALYSIS_CACHE_TTL=86400    # 24 hours
RATE_LIMIT_PER_MINUTE=60
YFINANCE_TIMEOUT=30
LOG_LEVEL=INFO
```

## Performance & Caching

- **Stock Data**: Cached for 12 hours to balance freshness with API efficiency
- **AI Analysis**: Cached for 24 hours as analysis doesn't change frequently
- **Concurrent Operations**: Multiple stocks fetched in parallel
- **Rate Limiting**: Built-in request validation and limiting
- **Token Tracking**: Monitor OpenAI API usage and estimated costs

## Error Handling

The API provides structured error responses:

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

Common error codes:
- `STOCK_NOT_FOUND`: Invalid stock symbol
- `ANALYSIS_FAILED`: AI analysis failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_PARAMETERS`: Invalid request parameters

## Development

### Project Structure

```
app/
├── main.py              # FastAPI application entry
├── config.py            # Configuration settings
├── models/              # Pydantic models
│   ├── stock.py         # Stock data models
│   └── analysis.py      # Analysis models
├── services/            # Business logic
│   ├── stock_service.py     # yfinance integration
│   ├── analysis_service.py  # GPT-4o-mini analysis
│   └── indicator_service.py # Technical indicators
├── routers/             # API endpoints
│   ├── stocks.py        # Stock data routes
│   └── analysis.py      # Analysis routes
└── utils/               # Utilities
    ├── cache.py         # Redis caching
    └── validators.py    # Input validation
frontend/
├── index.html           # Test interface
└── README.md           # Frontend documentation
```

### Dependencies

Key packages used:
- **FastAPI**: Modern web framework
- **OpenAI**: GPT-4o-mini integration with structured outputs
- **yfinance**: Real-time stock data
- **Redis**: Caching layer
- **Pydantic**: Data validation
- **Pandas/NumPy**: Data processing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Local Development

```bash
# Start Redis
redis-server

# Start API with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access test frontend
open http://localhost:8000
```

## Production Deployment

### Docker Production

```bash
# Build image
docker build -t stock-analysis-api .

# Run container
docker run -p 8000:8000 --env-file .env stock-analysis-api
```

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Setup

For production:
- Set `LOG_LEVEL=WARNING` or `ERROR`
- Use managed Redis instance
- Configure proper CORS origins
- Set up monitoring and alerting
- Use environment-specific configurations

## Monitoring

### Health Checks

- `/health` - Overall API health with Redis connectivity
- `/api/v1/analysis/health` - Analysis service health with OpenAI connectivity

### Metrics to Monitor

- **Performance**: API response times, cache hit rates
- **Usage**: Token consumption, cost tracking, request rates
- **Errors**: Failed analyses, stock data failures
- **System**: CPU/Memory usage, Redis performance

### Cost Management

The service includes built-in OpenAI cost tracking:
- Real-time token usage monitoring
- Per-operation cost estimates
- Session totals via `/api/v1/analysis/tokens`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.