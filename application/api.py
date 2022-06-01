from bs4 import BeautifulSoup
from flask import Blueprint

from application.utils import get_url


api = Blueprint('api', __name__)


@api.route('/summary/<ticker>')
def get_summary(ticker):

    # Get the response from the url
    ticker = ticker.upper()
    url = 'https://finance.yahoo.com/quote/{}/'.format(ticker)
    response = get_url(url)
    
    # Create the soup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Return an error and a list of similar tickers if Yahoo Finance redirects to the lookup page
    if "lookup" in str(response.url):
        similar_tickers = []
        lookup_table = soup.find('table', {'class': 'lookup-table W(100%) Pos(r) BdB Bdc($seperatorColor) smartphone_Mx(20px)'})
        if lookup_table is not None:
            for row in lookup_table.tbody.find_all('tr'):
                items = row.findChildren('td')
                similar_tickers.append(
                    {
                        'symbol': items[0].text,
                        'name': items[1].text,
                        'last-price': items[2].text,
                        'industry/category': items[3].text,
                        'type': items[4].text,
                        'exchange': items[5].text
                    }
                )
        return {
            "error": f"Invalid ticker: {ticker}",
            "error_code": 404,
            "similar_tickers": similar_tickers
        }
    
    # Return an error if Yahoot Finance says that the ticker couldn't be found
    if soup.find("h1", {"class": "D(ib) Fz(18px)"}).text.strip() == f"({ticker})":
        return {
            "error": f"Invalid ticker: {ticker}",
            "error_code": 404,
            "similar_tickers": []
        }
    
    # Return an error if the quote is an ETF
    if soup.find("li", {"data-test": "HOLDINGS"}) is not None:
        return {
            "error": "ETFs are not supported",
            "error_code": 403
        }

    # Store the quote data in a dict which will be returned later
    data = {}
    data["ticker"] = ticker

    # Get the standard data about the ticker
    data["name"] = soup.find("h1", {"class": "D(ib) Fz(18px)"}).text
    data["price"] = soup.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketPrice"}).text
    data["change-percent"] = soup.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketChangePercent"}).findChild("span").text
    data["change-dollar"] = soup.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketChange"}).findChild("span").text

    # Determine what type of quote it is
    if "-" in url: # crypto
        data["_type"] = "crypto"
        data["previous-close"] = soup.find("td", {"data-test": "PREV_CLOSE-value"}).text
        data["open"] = soup.find("td", {"data-test": "OPEN-value"}).text
        data["days-range"] = soup.find("td", {"data-test": "DAYS_RANGE-value"}).text
        data["52-week-range"] = soup.find("td", {"data-test": "FIFTY_TWO_WK_RANGE-value"}).text
        data["start-date"] = soup.find("td", {"data-test": "START_DATE-value"}).text
        data["algorithm"] = soup.find("td", {"data-test": "ALGORITHM-value"}).text
        data["market-cap"] = soup.find("td", {"data-test": "MARKET_CAP-value"}).text
        data["circulating-supply"] = soup.find("td", {"data-test": "CIRCULATING_SUPPLY-value"}).text
        data["max-supply"] = soup.find("td", {"data-test": "MAX_SUPPLY-value"}).text
        data["volume"] = soup.find("fin-streamer", {"data-field": "regularMarketVolume"}).text
        data["volume-24-hour"] = soup.find("td", {"data-test": "TD_VOLUME_24HR-value"}).text
        data["volume-24-hour-all-currencies"] = soup.find("td", {"data-test": "TD_VOLUME_24HR_ALLCURRENCY-value"}).text
    else: # stock
        data["_type"] = "stock"
        data["previous-close"] = soup.find("td", {"data-test": "PREV_CLOSE-value"}).text
        data["open"] = soup.find("td", {"data-test": "OPEN-value"}).text
        data["bid"] = soup.find("td", {"data-test": "BID-value"}).text
        data["ask"] = soup.find("td", {"data-test": "ASK-value"}).text
        data["days-range"] = soup.find("td", {"data-test": "DAYS_RANGE-value"}).text
        data["52-week-range"] = soup.find("td", {"data-test": "FIFTY_TWO_WK_RANGE-value"}).text
        data["volume"] = soup.find("fin-streamer", {"data-field": "regularMarketVolume"}).text
        data["avg-volume"] = soup.find("td", {"data-test": "AVERAGE_VOLUME_3MONTH-value"}).text
        data["market-cap"] = soup.find("td", {"data-test": "MARKET_CAP-value"}).text
        data["beta"] = soup.find("td", {"data-test": "BETA_5Y-value"}).text
        data["pe-ratio"] = soup.find("td", {"data-test": "PE_RATIO-value"}).text
        data["eps"] = soup.find("td", {"data-test": "EPS_RATIO-value"}).text
        data["earnings-date"] = soup.find("td", {"data-test": "EARNINGS_DATE-value"}).text
        data["forward-dividend-and-yield"] = soup.find("td", {"data-test": "DIVIDEND_AND_YIELD-value"}).text
        data["ex-dividend-date"] = soup.find("td", {"data-test": "EX_DIVIDEND_DATE-value"}).text
        data["1-year-target-est"] = soup.find("td", {"data-test": "ONE_YEAR_TARGET_PRICE-value"}).text

    # Convert any numbers from strings to floats
    for key in data:
        val_without_commas = data[key].replace(",", "") # Handle numbers with commas
        try:
            data[key] = float(val_without_commas)
        except ValueError:
            pass

    return data