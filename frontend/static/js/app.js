

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
                document.getElementById('textplaceholder').textContent = ''
            }
            else {
                document.getElementById('textplaceholder').textContent = `Error: ${data.error}`
                document.getElementById('stockInfo').style.display = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('textplaceholder').textContent = 'An error occured while fetching stock data'
            document.getElementById('stockinfo').style.display = '';
        })
}

document.getElementById("myReset").onclick = function () {
    document.getElementById('stocktick').value = '';
    // clear displayed stock info 
    document.getElementById('stockInfo').style.display = 'none';
    document.getElementById('textplaceholder').textContent = '';
    //Reset all stock information fields
    document.getElementById('stockName').textContent = '';
    document.getElementById('stockPrice').textContent = '';
    document.getElementById('marketCap').textContent = '';
    document.getElementById('peRatio').textContent = '';
    document.getElementById('volume').textContent = '';

}