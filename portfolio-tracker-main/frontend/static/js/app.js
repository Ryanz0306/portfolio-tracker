
let sticker;

document.getElementById("mySubmit").onclick = function () {
    sticker = document.getElementById('stocktick').value.trim().toUpperCase();

    if (!sticker) {
        showError('Please enter a stock ticker');
        return;
    }

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
                const stockInfo = data.stock;

                // Display stock info section
                document.getElementById('stockInfoSection').style.display = 'block';
                document.getElementById('stockName').textContent = stockInfo.name;
                document.getElementById('stockPrice').textContent = '$' + formatNumber(stockInfo.current_price);
                document.getElementById('marketCap').textContent = formatMarketCap(stockInfo.market_cap);
                document.getElementById('peRatio').textContent = stockInfo.pe_ratio !== 'N/A' ? stockInfo.pe_ratio.toFixed(2) : 'N/A';
                document.getElementById('volume').textContent = formatNumber(stockInfo.volume);
                document.getElementById('previousClose').textContent = stockInfo.previous_close !== 'N/A' ? '$' + formatNumber(stockInfo.previous_close) : 'N/A';
                document.getElementById('dayHigh').textContent = stockInfo.day_high !== 'N/A' ? '$' + formatNumber(stockInfo.day_high) : 'N/A';
                document.getElementById('dayLow').textContent = stockInfo.day_low !== 'N/A' ? '$' + formatNumber(stockInfo.day_low) : 'N/A';
                clearError();

                // Display graph section
                document.getElementById('graphSection').style.display = 'block';

                // Render the chart using Plotly. Compute container width and pass explicit width
                if (window.Plotly && data.chart_data) {
                    try {
                        const container = document.querySelector('.chart-card');
                        const plotDiv = document.getElementById('plotgraph');

                        const chartCard = document.querySelector('.chart-card');
                        const chartContainer = document.querySelector('.chart-container');
                        // compute available inner width (chart card width minus card padding)
                        const cardStyle = window.getComputedStyle(chartCard);
                        const containerStyle = window.getComputedStyle(chartContainer);
                        const cardPaddingLeft = parseFloat(cardStyle.paddingLeft) || 0;
                        const cardPaddingRight = parseFloat(cardStyle.paddingRight) || 0;
                        const availableWidth = Math.floor(chartCard.clientWidth - cardPaddingLeft - cardPaddingRight);

                        // ensure layout exists and adjust margins to match card padding
                        data.chart_data.layout = data.chart_data.layout || {};
                        const existingMargin = data.chart_data.layout.margin || {};
                        const marginLeft = Math.max(12, Math.floor(cardPaddingLeft + 8));
                        const marginRight = Math.max(12, Math.floor(cardPaddingRight + 8));
                        data.chart_data.layout.margin = {
                            l: marginLeft,
                            r: marginRight,
                            t: existingMargin.t || 60,
                            b: existingMargin.b || 60
                        };
                        data.chart_data.layout.width = availableWidth;
                        data.chart_data.layout.height = data.chart_data.layout.height || 650;
                        data.chart_data.layout.autosize = false;

                        Plotly.newPlot('plotgraph', data.chart_data.data, data.chart_data.layout, { responsive: true });

                        // Recalculate on window resize to keep alignment (debounced)
                        let resizeTimer;
                        window.addEventListener('resize', () => {
                            clearTimeout(resizeTimer);
                            resizeTimer = setTimeout(() => {
                                const newCardPaddingLeft = parseFloat(window.getComputedStyle(chartCard).paddingLeft) || 0;
                                const newCardPaddingRight = parseFloat(window.getComputedStyle(chartCard).paddingRight) || 0;
                                const newWidth = Math.floor(chartCard.clientWidth - newCardPaddingLeft - newCardPaddingRight);
                                const newMarginLeft = Math.max(12, Math.floor(newCardPaddingLeft + 8));
                                const newMarginRight = Math.max(12, Math.floor(newCardPaddingRight + 8));
                                Plotly.relayout('plotgraph', {
                                    width: newWidth,
                                    'margin.l': newMarginLeft,
                                    'margin.r': newMarginRight
                                });
                            }, 150);
                        });
                    } catch (plotErr) {
                        console.error('Plot render error', plotErr, data);
                        showError('Chart could not be rendered. See console for details.');
                    }
                } else {
                    console.error('Plotly is not loaded or chart data is missing', data);
                    showError('Chart could not be loaded. Please refresh the page and try again.');
                }

                // Fetch news
                getStockNews(stockInfo.symbol);

                // Scroll to stock info
                setTimeout(() => {
                    document.getElementById('stockInfoSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 300);
            }
            else {
                // Clear sticker so Add doesn't reuse a previous successful search
                sticker = null;
                showError(data.error || 'Unable to find stock information');
                document.getElementById('stockInfoSection').style.display = 'none';
                document.getElementById('graphSection').style.display = 'none';
                document.getElementById('newsSection').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            sticker = null;
            showError('An error occurred while fetching stock data');
            document.getElementById('stockInfoSection').style.display = 'none';
            document.getElementById('graphSection').style.display = 'none';
            document.getElementById('newsSection').style.display = 'none';
        })
}

document.getElementById("myReset").onclick = function () {
    document.getElementById('stocktick').value = '';
    sticker = null;
    document.getElementById('stockInfoSection').style.display = 'none';
    clearError();
    document.getElementById('stockName').textContent = '-';
    document.getElementById('stockPrice').textContent = '-';
    document.getElementById('marketCap').textContent = '-';
    document.getElementById('peRatio').textContent = '-';
    document.getElementById('volume').textContent = '-';
    document.getElementById('previousClose').textContent = '-';
    document.getElementById('dayHigh').textContent = '-';
    document.getElementById('dayLow').textContent = '-';
    document.getElementById('graphSection').style.display = 'none';
    document.getElementById('plotgraph').innerHTML = '';
    hideNews();
    document.getElementById('stocktick').focus();
}

document.getElementById("myAdd").onclick = function () {
    const inputSymbol = document.getElementById('stocktick').value.trim().toUpperCase();
    const symbol = inputSymbol || (sticker || '').toUpperCase();

    if (!symbol) {
        showError('Please search for or enter a stock symbol first');
        return;
    }

    sticker = symbol;

    // Collect basic info to save
    const name = document.getElementById('stockName').textContent || '';
    const priceText = document.getElementById('stockPrice').textContent || '';
    const price = parseFloat(priceText.replace(/[^0-9.-]+/g, '')) || null;

    fetch('/api/portfolio/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, name, price })
    })
        .then(r => r.json())
        .then(resp => {
            if (resp.success) {
                // redirect to portfolio page
                window.location.href = '/portfolio';
            } else {
                showError(resp.error || 'Failed to add to portfolio');
            }
        })
        .catch(err => {
            console.error('Add to portfolio error', err);
            showError('An error occurred while adding to portfolio');
        });
}

// Allow Enter key to search
document.getElementById('stocktick').addEventListener('keypress', function (event) {
    if (event.key === 'Enter') {
        document.getElementById('mySubmit').click();
    }
});

async function getStockNews(symbol) {
    try {
        const response = await fetch(`/api/stock-news/${symbol}`);
        const data = await response.json();

        if (data.success) {
            displayStockNews(symbol, data.news);
        } else {
            console.error('Failed to get news:', data.error);
            hideNews();
        }
    }
    catch (error) {
        console.error('News Error:', error);
        hideNews();
    }
}

function displayStockNews(symbol, news) {
    document.getElementById('newsSection').style.display = 'block';
    document.getElementById('newsSymbol').textContent = symbol;

    const newsFeed = document.getElementById('newsFeed');
    newsFeed.innerHTML = '';

    if (news && news.length > 0) {
        news.forEach((article, index) => {
            const articleDiv = document.createElement('div');
            articleDiv.className = 'news-article';
            articleDiv.style.animationDelay = `${index * 0.1}s`;

            articleDiv.innerHTML = `
                <h4>${article.title}</h4>
                <p class="news-publisher">
                    <strong>${article.publisher}</strong> • ${article.published}
                </p>
                <p class="news-content">${article.content}</p>
                <a href="${article.link}" target="_blank" rel="noopener noreferrer">Read full article →</a>
            `;
            newsFeed.appendChild(articleDiv);
        });
    } else {
        newsFeed.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No news available for this stock</p>';
    }
}

function hideNews() {
    document.getElementById('newsSection').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('errormessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function clearError() {
    const errorDiv = document.getElementById('errormessage');
    errorDiv.textContent = '';
    errorDiv.style.display = 'none';
}

function formatNumber(num) {
    if (num === 'N/A' || num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

function formatMarketCap(cap) {
    if (cap === 'N/A' || cap === null || cap === undefined) return 'N/A';

    if (cap >= 1000000000000) {
        return '$' + (cap / 1000000000000).toFixed(2) + 'T';
    } else if (cap >= 1000000000) {
        return '$' + (cap / 1000000000).toFixed(2) + 'B';
    } else if (cap >= 1000000) {
        return '$' + (cap / 1000000).toFixed(2) + 'M';
    }
    return '$' + formatNumber(cap);
}

