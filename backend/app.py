from flask import Flask, jsonify, request, render_template 
import json
import os 
from datetime import datetime
import yfinance as yf


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

        return jsonify({
            'success': True,
            'stock': stock_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Could not find data for {stock_ticker}. Error: {str(e)}" 
        })
    

if __name__ == '__main__':
    app.run(debug=True)


