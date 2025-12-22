

let sticker;

document.getElementById("mySubmit").onclick = function () {
    sticker = document.getElementById('stocktick').value;

    fetch('/find-ticker', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ stocktick: sticker })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stockInfo = data.stock
                document.getElementById('stockInfo').style.display = 'block';
                document.getElementById('stockName').textContent = stockInfo.name;
                document.getElementById('stockPrice').textContent = stockInfo.current_price;
                document.getElementById('marketCap').textContent = stockInfo.market_cap;
                document.getElementById('peRatio').textContent = stockInfo.pe_ratio;
                document.getElementById('volume').textContent = stockInfo.volume;
                document.getElementById('errormessage').textContent = '';
                document.getElementById('plotgraph').innerHTML = data.chart_html;
                document.getElementById('graphSection').style.display = 'block';
                getStockNews(stockInfo.symbol);
            }
            else {
                document.getElementById('errormessage').textContent = `${data.error}`
                document.getElementById('stockInfo').style.display = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('errormessage').textContent = 'An error occured while fetching stock data'
            document.getElementById('stockinfo').style.display = '';
        })
}

document.getElementById("myReset").onclick = function () {
    document.getElementById('stocktick').value = '';
    document.getElementById('stockInfo').style.display = 'none';
    document.getElementById('errormessage').textContent = '';
    document.getElementById('stockName').textContent = '';
    document.getElementById('stockPrice').textContent = '';
    document.getElementById('marketCap').textContent = '';
    document.getElementById('peRatio').textContent = '';
    document.getElementById('volume').textContent = '';
    document.getElementById('graphSection').style.display = 'none';
    document.getElementById('plotgraph').innerHTML = '';
    document.getElementById('newsSection').style.display = 'none';
    document.getElementById('newsFeed').innerHTML = '';
    document.getElementById('newsSymbol').textContent = '';
}

async function getStockNews(symbol) {
    try {
        const response = await fetch(`/api/stock-news/${symbol}`);
        const data = await response.json();

        if (data.success) {
            displayStockNews(symbol, data.news);
        } else {
            alert('Failed to get news' + data.error);
        }
    }
    catch (error) {
        console.error('News Error')
        alert('Failed to fetch news')
    }
}
function displayStockNews(symbol, news) {
    document.getElementById('newsSection').style.display = 'block';
    document.getElementById('newsSymbol').textContent = symbol;

    const newsFeed = document.getElementById('newsFeed');
    newsFeed.innerHTML = '';

    if (news && news.length > 0) {
        news.forEach(article => {
            const articleDiv = document.createElement('div')
            articleDiv.className = 'news-article';


            articleDiv.innerHTML = `
                <h4>${article.title}</h4>
                <p class="news-publisher">Published by ${article.publisher} on ${article.published}</p>
                <p class = "news-content">${article.content}</p>
                <a href="${article.link}" target="_blank" rel="noopener">Read more</a>
                <hr>
            `;
            newsFeed.appendChild(articleDiv);
        })
    } else {
        newsFeed.innerHTML = '<p>No news available for this stock.<p>'
    }
    const closeButton = document.createElement('button');
    closeButton.className = 'close-btn';
    closeButton.textContent = 'Close News';
    closeButton.onclick = hideNews;
    newsFeed.appendChild(closeButton);
}
function hideNews() {
    document.getElementById('newsSection').style.display = 'none';
}
