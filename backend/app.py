from flask import Flask, jsonify, request, render_template 
import json
import os 
from datetime import datetime
import yfinance as yf
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


app = Flask(__name__, 
            template_folder= '../frontend',
            static_folder = '../frontend/static')

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

        stock_data = {
            'symbol' : stock_ticker,
            'name' : info.get('longName', 'N/A'),
            'current_price' : info.get('currentPrice', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'volume': info.get('volume', 'N/A')
        } 
        chart_html = get_stockchart(stock_ticker)

        return jsonify({
            'success': True,
            'stock': stock_data,
            'chart_html': chart_html
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

def get_stockchart(symbol):
    stock = yf.Ticker(symbol)
    history = stock.history(period = '20y')
    Dates = history.index.strftime('%Y-%m-%d').tolist()
    Prices = history['Close'].tolist()  
    
    structured = pd.DataFrame({
    'Date': Dates,
    'Price': Prices
})

    structured['Date'] = pd.to_datetime(structured['Date'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = structured['Date'],
        y = structured['Price'],
        mode = 'lines',
        name = symbol
     )) 
    fig.update_layout(
        xaxis_title = 'Date'
    ) 
    return pio.to_html(fig, include_plotlyjs='cdn', full_html=False)

if __name__ == '__main__':
    app.run(debug=True)


