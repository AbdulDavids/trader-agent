# AI Stock Analysis Frontend

A simple web interface to test the AI Stock Analysis API endpoints.

## 🚀 Quick Start

1. **Start the API server:**
   ```bash
   cd ../
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open the frontend:**
   - Simply open `index.html` in your browser
   - Or serve it with a local server:
     ```bash
     python -m http.server 8080
     # Then visit: http://localhost:8080
     ```

## 📋 Features

- **Real-time API Status** - Shows connection status to your backend
- **Stock Search** - Search for stocks by name or ticker
- **Stock Data** - Get detailed stock information with technical indicators
- **AI Analysis** - Get AI-powered BUY/HOLD/SELL recommendations
- **Stock Comparison** - Compare multiple stocks side-by-side
- **Portfolio Analysis** - Analyze your complete portfolio

## 🎯 API Endpoints Tested

| Feature | Endpoint | Method |
|---------|----------|--------|
| Health Check | `/health` | GET |
| Stock Search | `/api/v1/stocks/search` | GET |
| Stock Data | `/api/v1/stocks/{symbol}` | GET |
| AI Analysis | `/api/v1/analysis/{symbol}` | GET |
| Compare Stocks | `/api/v1/analysis/compare` | POST |
| Portfolio Analysis | `/api/v1/analysis/portfolio` | POST |

## 🎨 UI Features

- **Dark Theme** - Pure black background with green accents
- **Native Placeholders** - Visible initially, disappear when typing
- **Color-coded Results** - Green for success, red for errors
- **Expandable Views** - Click to see full JSON responses
- **Loading Indicators** - Clear feedback during API calls
- **Responsive Design** - Works on different screen sizes

## 📝 Example Usage

1. **Search for a stock:** Enter "AAPL" or "Tesla" in the search section
2. **Get stock data:** Enter "AAPL" to see current price and technical indicators
3. **AI Analysis:** Enter "TSLA" to get AI-powered investment recommendation
4. **Compare stocks:** Enter "AAPL,MSFT,GOOGL" to compare tech giants
5. **Portfolio analysis:** Use the provided JSON template to analyze a portfolio

## 🔧 Configuration

The frontend connects to `http://localhost:8000` by default. To change the API URL, edit the `API_BASE_URL` constant in `index.html`.

## 🐛 Troubleshooting

- **CORS Issues:** If you see CORS errors, serve the frontend from a local server instead of opening directly
- **API Offline:** Check that your FastAPI server is running on port 8000
- **OpenAI Errors:** Ensure your OpenAI API key is configured in the backend 