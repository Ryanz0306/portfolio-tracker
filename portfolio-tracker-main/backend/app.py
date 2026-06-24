from flask import Flask, jsonify, request, render_template 
import json
import os 
from datetime import datetime
from threading import Lock
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np


app = Flask(__name__, 
            template_folder= '../frontend',
            static_folder = '../frontend/static')

# Simple file-backed portfolio storage
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), 'portfolio.json')
portfolio_lock = Lock()

def _read_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def _write_portfolio(data):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/test')
def test():
    return jsonify({
        'message': 'backend is working',
        'status' : 'success',
        'timestamp': datetime.now().isoformat()
    })
@app.route('/find-ticker', methods = ['POST'])
def handle_find_ticker():
    data = request.json
    stock_ticker = data.get('stocktick', '').upper()
    print(f"Received: {stock_ticker}")
    
    try:
        stock = yf.Ticker(stock_ticker)
        info = stock.info

        if not info or (info.get('currentPrice') is None and info.get('regularMarketPrice') is None):
            return jsonify({
                'success': False,
                'error': 'Invalid stock ticker. Please check the symbol and try again.'
            })

        stock_data = {
            'symbol': stock_ticker,
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('currentPrice', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'previous_close': info.get('previousClose', 'N/A'),
            'day_high': info.get('dayHigh', 'N/A'),
            'day_low': info.get('dayLow', 'N/A')
        }
        chart_data = get_stockchart(stock_ticker)

        return jsonify({
            'success': True,
            'stock': stock_data,
            'chart_data': chart_data
        })
    
    except Exception as e:
        
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}" 
        })
    
@app.route('/api/stock-news/<symbol>')
def get_stock_news(symbol):
    try:
        stock = yf.Ticker(symbol)
        news = stock.news

        if not news:  # Check if news is empty
            return jsonify({
                'success': False,
                'error': 'No news available for this stock'
            })
        
        formatted_news = []
        for article in news[:5]:
            try:

                content = article.get('content', 'No content available') 
                description = content.get('summary', content.get('description','No summary available'))

                provider = content.get('provider', {})
                canonical_url = content.get('canonicalUrl', {})

                pub_date = content.get('pubDate', 0)
                publisher = (
                    content.get('provider', {}).get('displayName') or 
                    article.get('publisher') or 
                    'Unknown publisher'
                )
                pub_date_str = content.get('pubDate', '')
                if pub_date_str:
                    try:
                        date_obj = datetime.fromisoformat(pub_date_str.replace('Z', ''))
                        date = date_obj.strftime('%B %d, %Y')
                    except:
                        date = pub_date_str[:10]  
                else:
                    date = "Recent"
                
                formatted_news.append({
                    'title': content.get('title', 'No title available'),
                    'publisher': publisher,
                    'link': canonical_url.get('url') or content.get('previewUrl') or article.get('link', '#'),
                    'published': date,
                    'content': description[:200] + '...' if len(description) > 200 else description,
                })
            except Exception as article_error:
                print(article_error)
                continue
        
        if not formatted_news:
            return jsonify({
                'success': False,
                'error': 'Failed to process news articles'
            })
        
        return jsonify({
            'success': True,
            'news': formatted_news[::-1]
        })      

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        })


@app.route('/portfolio')
def portfolio_page():
    return render_template('portfolio.html')


@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    data = _read_portfolio()
    return jsonify({ 'success': True, 'portfolio': data })


@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    try:
        payload = request.json or {}
        symbol = (payload.get('symbol') or '').upper()
        name = payload.get('name') or ''
        price = payload.get('price')

        if not symbol:
            return jsonify({ 'success': False, 'error': 'Missing symbol' }), 400

        # Basic server-side validation: ensure ticker exists via yfinance
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if not info or (info.get('currentPrice') is None and info.get('regularMarketPrice') is None and not info.get('longName')):
                return jsonify({ 'success': False, 'error': 'Invalid stock ticker. Please check the symbol and try again.' }), 400
        except Exception:
            return jsonify({ 'success': False, 'error': 'Invalid stock ticker. Please check the symbol and try again.' }), 400

        with portfolio_lock:
            portfolio = _read_portfolio()
            # normalize existing symbols to avoid false negatives/positives
            existing = { (p.get('symbol') or '').upper().strip() for p in portfolio }
            if symbol.upper().strip() in existing:
                return jsonify({ 'success': False, 'error': 'Symbol already in portfolio' }), 400

            entry = {
                'symbol': symbol.upper().strip(),
                'name': name,
                'price': price,
                'added_at': datetime.now().isoformat()
            }
            portfolio.append(entry)
            _write_portfolio(portfolio)

        return jsonify({ 'success': True, 'entry': entry })
    except Exception as e:
        return jsonify({ 'success': False, 'error': str(e) }), 500


@app.route('/api/portfolio/remove', methods=['POST'])
def remove_from_portfolio():
    try:
        payload = request.json or {}
        symbol = (payload.get('symbol') or '').upper()
        if not symbol:
            return jsonify({ 'success': False, 'error': 'Missing symbol' }), 400

        with portfolio_lock:
            portfolio = _read_portfolio()
            new_port = [p for p in portfolio if p.get('symbol') != symbol]
            if len(new_port) == len(portfolio):
                return jsonify({ 'success': False, 'error': 'Symbol not found' }), 404
            _write_portfolio(new_port)

        return jsonify({ 'success': True })
    except Exception as e:
        return jsonify({ 'success': False, 'error': str(e) }), 500


@app.route('/api/portfolio/reorder', methods=['POST'])
def reorder_portfolio():
    try:
        payload = request.json or {}
        order = payload.get('order') or []
        if not isinstance(order, list):
            return jsonify({ 'success': False, 'error': 'Order must be a list of symbols' }), 400

        with portfolio_lock:
            portfolio = _read_portfolio()
            symbols = [p.get('symbol') for p in portfolio]
            # Validate same set
            if set(symbols) != set([s.upper() for s in order]):
                return jsonify({ 'success': False, 'error': 'Order symbols do not match portfolio' }), 400

            symbol_to_entry = { p.get('symbol'): p for p in portfolio }
            new_port = [ symbol_to_entry[s.upper()] for s in order ]
            _write_portfolio(new_port)

        return jsonify({ 'success': True })
    except Exception as e:
        return jsonify({ 'success': False, 'error': str(e) }), 500

def get_stockchart(symbol):
    stock = yf.Ticker(symbol)
    history = stock.history(period='20y')

    if history.empty:
        raise ValueError(f'No historical price data available for {symbol}')

    Dates = history.index.strftime('%Y-%m-%d').tolist()
    Prices = history['Close'].tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Dates,
        y=Prices,
        mode='lines',
        name=symbol,
        line=dict(color='#1f77b4', width=2)
    ))
    fig.update_layout(
        title = f'{symbol} Stock Price - 20 Year History',
        xaxis_title = 'Date',
        yaxis_title = 'Price ($)',
        hovermode = 'x unified',
        margin=dict(l=60, r=40, t=60, b=60),
        height=500,
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        ),
        plot_bgcolor='rgba(240,240,240,0.5)'
    ) 
    return json.loads(fig.to_json())


@app.route('/api/analytics', methods=['GET'])
def portfolio_analytics():
    try:
        portfolio = _read_portfolio()
        results = []
        for entry in portfolio:
            symbol = (entry.get('symbol') or '').upper()
            if not symbol:
                continue
            try:
                stock = yf.Ticker(symbol)
                # use 1y history for analytics
                history = stock.history(period='1y')
                if history.empty:
                    results.append({'symbol': symbol, 'error': 'No historical data'})
                    continue
                closes = history['Close'].dropna()
                pts = len(closes)
                mean = float(closes.mean()) if pts else None
                std = float(closes.std()) if pts else None
                var = float(closes.var()) if pts else None
                med = float(closes.median()) if pts else None
                minimum = float(closes.min()) if pts else None
                maximum = float(closes.max()) if pts else None
                latest = float(closes.iloc[-1]) if pts else None
                pct_change = float((closes.iloc[-1] / closes.iloc[0] - 1) * 100) if pts and closes.iloc[0] else None

                results.append({
                    'symbol': symbol,
                    'mean': mean,
                    'std': std,
                    'var': var,
                    'median': med,
                    'min': minimum,
                    'max': maximum,
                    'latest': latest,
                    'pct_change_percent': pct_change,
                    'points': pts
                })
            except Exception as e:
                results.append({'symbol': symbol, 'error': str(e)})

        return jsonify({'success': True, 'analytics': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/portfolio_cov', methods=['GET'])
def portfolio_covariance():
    try:
        portfolio = _read_portfolio()
        symbols = [ (p.get('symbol') or '').upper() for p in portfolio if p.get('symbol') ]
        symbols = [s for s in symbols if s]
        if not symbols:
            return jsonify({'success': False, 'error': 'No symbols in portfolio'}), 400

        # fetch close prices and build returns DataFrame
        close_frames = []
        for s in symbols:
            try:
                hist = yf.Ticker(s).history(period='1y')
                if hist.empty:
                    continue
                close = hist['Close'].rename(s)
                close_frames.append(close)
            except Exception:
                continue

        if not close_frames:
            return jsonify({'success': False, 'error': 'No historical data available for portfolio symbols'}), 400

        prices = pd.concat(close_frames, axis=1).dropna()
        if prices.empty:
            return jsonify({'success': False, 'error': 'Not enough overlapping historical data'}), 400

        returns = prices.pct_change().dropna()
        cov_daily = returns.cov()
        cov_annual = cov_daily * 252

        # compute portfolio returns (equal-weighted) and market returns for beta
        prices = pd.concat(close_frames, axis=1).dropna()
        returns = prices.pct_change().dropna()

        # equal weights
        n = len(symbols)
        weights = np.array([1.0 / n] * n)
        # get market returns (S&P 500) as benchmark and align if possible
        mkt_returns = None
        try:
            mkt = yf.Ticker('^GSPC').history(period='1y')
            mkt_prices = mkt['Close']
            mkt_returns = mkt_prices.pct_change()
            # align market and asset returns to common index
            aligned_idx = returns.index.intersection(mkt_returns.index)
            returns_aligned = returns.reindex(aligned_idx).dropna()
            mkt_returns = mkt_returns.reindex(returns_aligned.index).dropna()
            # if alignment produced no rows, fall back
            if returns_aligned.empty or mkt_returns.empty:
                returns_aligned = returns
                mkt_returns = None
        except Exception:
            returns_aligned = returns
            mkt_returns = None

        # parse weights from query param if provided, normalize to sum=1
        weights_q = request.args.get('weights', None)
        n = len(symbols)
        if weights_q:
            try:
                parts = [float(x) for x in weights_q.split(',')]
                if len(parts) != n:
                    weights = np.array([1.0 / n] * n)
                else:
                    s = sum(parts)
                    if s == 0:
                        weights = np.array([1.0 / n] * n)
                    else:
                        # if input looks like percents (sum around 100), convert to decimals
                        if s > 1.001:
                            parts = [p / 100.0 for p in parts]
                        arr = np.array(parts, dtype=float)
                        weights = arr / arr.sum()
            except Exception:
                weights = np.array([1.0 / n] * n)
        else:
            weights = np.array([1.0 / n] * n)

        # compute asset mean daily and covariance using aligned returns
        asset_mean_daily = returns_aligned.mean()
        cov_daily_aligned = returns_aligned.cov()
        cov_annual = cov_daily_aligned * 252

        # portfolio expected return (annualized) using weights
        try:
            mean_annual = float(np.dot(weights, asset_mean_daily.values) * 252)
        except Exception:
            mean_annual = float((asset_mean_daily.mean() * 252) if not asset_mean_daily.empty else 0.0)

        # portfolio variance and std (annualized) using covariance matrix
        try:
            port_var_annual = float(np.dot(weights, np.dot(cov_annual.values, weights)))
            std_annual = float(np.sqrt(max(0.0, port_var_annual)))
        except Exception:
            # fallback: compute from weighted daily returns
            port_returns = (returns * weights).sum(axis=1)
            mean_daily = port_returns.mean()
            std_daily = port_returns.std()
            mean_annual = float(mean_daily * 252)
            std_annual = float(std_daily * (252 ** 0.5))

        # compute beta relative to market using weights
        portfolio_beta = None
        treynor = None
        if mkt_returns is not None and not returns_aligned.empty and len(mkt_returns) > 10:
            # covariance between each asset and market (daily)
            asset_mkt_cov_daily = returns_aligned.apply(lambda col: col.cov(mkt_returns))
            cov_pm_daily = float(np.dot(weights, asset_mkt_cov_daily.values))
            var_m_daily = float(np.var(mkt_returns.values, ddof=1))
            if var_m_daily > 0:
                portfolio_beta = cov_pm_daily / var_m_daily

        # risk-free rate (annual) — read from query param 'rf' as percent (e.g., 1.5 -> 1.5%)
        try:
            rf_percent = float(request.args.get('rf', 0.0))
        except Exception:
            rf_percent = 0.0
        rf = rf_percent / 100.0

        sharpe = None
        treynor = None
        if std_annual > 0:
            sharpe = (mean_annual - rf) / std_annual
        if portfolio_beta is not None and portfolio_beta != 0:
            treynor = (mean_annual - rf) / portfolio_beta

        return jsonify({
            'success': True,
            'symbols': symbols,
            'portfolio_beta': portfolio_beta,
            'sharpe_annual': sharpe,
            'treynor_annual': treynor,
            'portfolio_mean_annual': mean_annual,
            'portfolio_std_annual': std_annual
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/optimize', methods=['GET'])
def portfolio_optimize():
    try:
        portfolio = _read_portfolio()
        symbols = [ (p.get('symbol') or '').upper() for p in portfolio if p.get('symbol') ]
        symbols = [s for s in symbols if s]
        if not symbols:
            return jsonify({'success': False, 'error': 'No symbols in portfolio'}), 400

        # fetch close prices
        close_frames = []
        for s in symbols:
            try:
                hist = yf.Ticker(s).history(period='1y')
                if hist.empty:
                    continue
                close = hist['Close'].rename(s)
                close_frames.append(close)
            except Exception:
                continue

        if not close_frames:
            return jsonify({'success': False, 'error': 'No historical data available for portfolio symbols'}), 400

        prices = pd.concat(close_frames, axis=1).dropna()
        if prices.empty:
            return jsonify({'success': False, 'error': 'Not enough overlapping historical data'}), 400

        returns = prices.pct_change().dropna()

        # annualized expected returns and covariance
        asset_mean_daily = returns.mean()
        mu_annual = asset_mean_daily.values * 252
        cov_annual = returns.cov().values * 252

        # risk-free (annual percent)
        try:
            rf_percent = float(request.args.get('rf', 0.0))
        except Exception:
            rf_percent = 0.0
        rf = rf_percent / 100.0

        method = (request.args.get('method') or 'markowitz').lower()

        if method == 'markowitz' or method == 'markowitz_max_sharpe' or method == 'max_sharpe':
            # tangency portfolio (max Sharpe): w ∝ Σ^{-1} (μ - rf)
            try:
                excess = mu_annual - rf
                inv = np.linalg.pinv(cov_annual)
                raw = inv.dot(excess)
                if np.all(np.isfinite(raw)) and np.abs(raw.sum()) > 1e-12:
                    w = raw / raw.sum()
                else:
                    w = np.ones(len(mu_annual)) / len(mu_annual)
            except Exception:
                w = np.ones(len(mu_annual)) / len(mu_annual)
        else:
            # fallback equal weights for unimplemented methods
            w = np.ones(len(mu_annual)) / len(mu_annual)

        weights_pct = (w * 100.0).tolist()

        return jsonify({'success': True, 'method': method, 'symbols': symbols, 'weights': weights_pct})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)


