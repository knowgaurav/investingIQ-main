import streamlit as st
import requests
from api import apiKEY
import yfinance as yf
import pandas as pd
from datetime import date, datetime
from bs4 import BeautifulSoup
from streamlit_option_menu import option_menu
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from PIL import Image

favicon = Image.open("./data/favicon.png")

st.set_page_config(
    page_title="investingIQ - Analyze stocks as easily as buying a coffee.",
    page_icon=favicon,
)

# 1. as sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_icon="list",
        menu_title="Main Menu", #required
        options=["Info", "Analysis", "Predictions"], #required
        icons=["info-circle", "pie-chart", "graph-up-arrow"],
        default_index=0
    )

# Horizontal Menu
stock = option_menu(
    menu_icon="list",
    menu_title=None, #required
    options=["Apple", "Google", "Meta", "Microsoft"], #required
    icons=["apple", "google", "meta", "microsoft"],
    default_index=0,
    orientation="horizontal"
)

def show_news(company):
    url = f"https://newsapi.org/v2/top-headlines?q={company}&apiKey={apiKEY}"
    
    r = requests.get(url)
    r = r.json()
    articles = r['articles']

    for article in articles:
        st.subheader(article['title'])
        if article['author']:
            st.write(article['author'])
        st.write(article['source']['name'])
        st.write(article['description'])
    
def get_balance_sheet_from_yfinance_web(ticker):
    url = f"https://finance.yahoo.com/quote/GOOG/balance-sheet?p={ticker}"
    header = {'Connection': 'keep-alive',
                'Expires': '-1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
                }
        
    r = requests.get(url, headers=header)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    div = soup.find_all('div', attrs={'class': 'D(tbhg)'})
    if len(div) < 1:
        print("Fail to retrieve table column header")
        exit(0)

    col = []
    for h in div[0].find_all('span'):
        text = h.get_text()
        if text != "Breakdown":
            col.append( datetime.strptime(text, "%m/%d/%Y") )
    
    df = pd.DataFrame(columns=col)
    for div in soup.find_all('div', attrs={'data-test': 'fin-row'}):
        i = 0
        idx = ""
        val = []
        for h in div.find_all('span'):
            if i == 0:
                idx = h.get_text()
            else:
                num = int(h.get_text().replace(",", "")) * 1000
                val.append( num )
            i += 1
        row = pd.DataFrame([val], columns=col, index=[idx] )
        df = df.append(row)

    return df

def sentimental_analysis(stock):
    finviz_url = 'https://finviz.com/quote.ashx?t='

    # Scraping Data
    news_tables = {}
    url = finviz_url + stock
    req = Request(url=url, headers={'user-agent':'my-app'})
    response = urlopen(req)
    html = BeautifulSoup(response, 'html')
    news_table = html.find(id='news-table')
    news_tables[stock] = news_table

    parsed_data = []
    for row in news_table.findAll('tr'):
        title = row.a.get_text()
        date_data = row.td.text.split(' ')

        if len(date_data) == 1:
            time = date_data[0]
        else:
            date = date_data[0]
            time = date_data[1]

        parsed_data.append([stock, date, time, title])
    
    # Sentiment Analysis
    df = pd.DataFrame(parsed_data, columns=['stock', 'date', 'time', 'title'])

    vader = SentimentIntensityAnalyzer()

    f = lambda title: vader.polarity_scores(title)['compound']
    df['compound'] = df['title'].apply(f)
    df['date'] = pd.to_datetime(df.date).dt.date

    mean_df = df.groupby(['stock', 'date']).mean()
    mean_df = mean_df.unstack()
    mean_df = mean_df.xs('compound', axis='columns').transpose()
    st.bar_chart(mean_df)

def prediction_using_prophet(stock):
    START = "2015-01-01"
    TODAY = date.today().strftime("%Y-%m-%d")

    st.subheader('Stock Prediction using FB Prophet')
    selected_stock = stock

    n_years = st.slider('Years of prediction:', 1, 4)
    period = n_years * 365

    @st.cache_data
    def load_data(ticker):
        data = yf.download(ticker, START, TODAY)
        data.reset_index(inplace=True)
        return data

    def remove_timezone(dt):
        return dt.replace(tzinfo=None)
        
    data_load_state = st.text("Load data...")
    data = load_data(selected_stock)
    data["Date"] = data["Date"].apply(remove_timezone)
    data_load_state.text('Loading data, done!')

    st.subheader('Raw data')
    st.write(data.tail())

    # Plot raw data
    def plot_raw_data():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="stock_open"))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="stock_close"))
        fig.layout.update(title_text='Time Series data with Rangeslider', xaxis_rangeslider_visible=True)
        st.plotly_chart(fig)
        
    plot_raw_data()

    # Predict forecast with Prophet.
    df_train = data[['Date','Close']]
    df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    forecast = m.predict(future)

    # Show and plot forecast
    st.subheader('Forecast data')
    st.write(forecast.tail())
        
    st.write(f'Forecast plot for {n_years} years')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.write("Forecast components")
    fig2 = m.plot_components(forecast)
    st.write(fig2)

def prediction_using_random_forest(stock):
    start = "2010-01-01"
    end = date.today().strftime("%Y-%m-%d")

    sp500 = yf.Ticker(stock)
    sp500 = sp500.history(start=start, end=end)

    del sp500['Dividends']
    del sp500['Stock Splits']

    sp500["Tomorrow"] = sp500["Close"].shift(-1)
    sp500["Target"] = (sp500["Tomorrow"] > sp500["Close"]).astype(int)

    st.subheader("Stock Prediction using Random Forest")

    def predict(train, test, predictors, model):
        model.fit(train[predictors], train["Target"])
        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index=test.index, name="Predictions")
        combined = pd.concat([test["Target"], preds], axis=1)
        return combined

    def backtest(data, model, predictors, start=2500, step=250):
        all_predictions = []

        for i in range(start, data.shape[0], step):
            train = data.iloc[0:i].copy()
            test = data.iloc[i:(i+step)].copy()
            predictions = predict(train, test, predictors, model)
            all_predictions.append(predictions)
        
        return pd.concat(all_predictions)

    def train_model(df):
        model = RandomForestClassifier(n_estimators=100, min_samples_split=100, random_state=1)

        train = df.iloc[:-100]
        test = df.iloc[-100:]

        predictors = ["Close", "Volume", "Open", "High", "Low"]
        model.fit(train[predictors], train["Target"])

        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index=test.index)
        # print(precision_score(test["Target"], preds))

        combined = pd.concat([test["Target"], preds], axis=1)
        st.line_chart(combined)

        predictions = backtest(df, model, predictors)
        st.write("Precision Score: ")
        st.write(precision_score(predictions["Target"], predictions["Predictions"]))
        st.write("Predicted Buy Percentage: ")
        st.write(predictions["Predictions"].value_counts() / predictions.shape[0])
        # st.write(predictions["Predictions"].value_counts())
        st.write("Actual Buy Percentage: ")
        st.write(predictions["Target"].value_counts() / predictions.shape[0])

    train_model(sp500)

def analyis(stock):
    start = "2010-01-01"
    end = date.today().strftime("%Y-%m-%d")

    comp = yf.Ticker(stock)
    data = comp.history(start=start, end=end)
    del data['Dividends']
    del data['Stock Splits']

    st.subheader("Latest Data: ")
    st.table(data[-10:])

    st.subheader("Stock Price Visualization: ")
    st.line_chart(data[data.columns[1:4]])

    # st.subheader("Balance Sheet: ")
    # balance_sheet = get_balance_sheet_from_yfinance_web(stock)
    # st.table(balance_sheet)

    st.subheader("Sentimental Analysis: ")
    sentimental_analysis(stock)

textJustify = '''
    <style>
        p {
            text-align: justify;
        }
    </style>
    '''

st.markdown(textJustify, unsafe_allow_html=True)

if selected == "Info":
    if stock == "Apple":
        st.image("./data/apple_banner.jpg")
        st.write("# Apple Info")
        c1, c2 = st.columns((2, 1))
        with c1:
            st.write("""Apple is an American technology company founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976. Incorporated in 1977, the company was one of the early manufacturers of personal computing devices with graphical user interface. Over the years, the company also forayed into other consumer electronics segments like mobile communication devices, digital music players, notebooks, and wearables. The company also develops and markets a range of related software and services, accessories, and networking solutions. Currently, the company’s chief executive officer (CEO) is Timothy Donald Cook, commonly known as Tim Cook.
            Apple offers consumer technologies of all kinds. Some of its most popular products include the iPhone, iPad, Macbook, and Apple Watch. Apple has 147,000 employees in numerous departments, including retail, software services, hardware, machine learning and AI, support and service, design, and more. Apple also offers services like Apple Music, which launched in June 2015, and Apple TV, which launched in 2019. Apple also provides products and services specifically curated for education, business, health care, and government. As a top member of the Fortune 500, Apple is one of the world’s largest technology companies and its catalogue of offerings continues to grow. Not only is Apple tech savvy, it's business savvy. """)
        
        with c2:
            st.subheader("2022 Stats: ")
            st.metric(label="Revenue", value="$394.3 billion", delta="2.1")
            st.metric(label="Operating Income", value="$119.44 billion", delta="1.3")
            st.metric(label="Net Income", value="$99.80 billion", delta="1.5")
        
        st.write("# Latest News")
        show_news("apple")
    if stock == "Google":
        st.image("./data/google_banner.jpg")
        st.write("# Google Info")
        c1, c2 = st.columns((2, 1))
        with c1:
            st.write("""Alphabet Inc. is an American multinational technology conglomerate holding company headquartered in Mountain View, California. It was created through a restructuring of Google on October 2, 2015, and became the parent company of Google and several former Google subsidiaries. Alphabet is the world's third-largest technology company by revenue and one of the world's most valuable companies. It is one of the Big Five American information technology companies, alongside Amazon, Apple, Meta, and Microsoft.
            The establishment of Alphabet Inc. was prompted by a desire to make the core Google business "cleaner and more accountable" while allowing greater autonomy to group companies that operate in businesses other than Internet services. Founders Larry Page and Sergey Brin announced their resignation from their executive posts in December 2019, with the CEO role to be filled by Sundar Pichai, also the CEO of Google. Page and Brin remain employees, board members, and controlling shareholders of Alphabet Inc""")
        
        with c2:
            st.subheader("2022 Stats: ")
            st.metric(label="Revenue", value="$282.8 billion", delta="1.5")
            st.metric(label="Operating Income", value="$74.84 billion", delta="-1.2")
            st.metric(label="Net Income", value="$59.97 billion", delta="-1.4")
        
        st.write("# Latest News")
        show_news("Google Company")
    if stock == "Meta":
        st.image("./data/meta_banner.jpg")
        st.write("# Meta Info")
        c1, c2 = st.columns((2, 1))
        with c1:
            st.write("""Meta Platforms, Inc., doing business as Meta and formerly named Facebook, Inc., and TheFacebook, Inc., is an American multinational technology conglomerate based in Menlo Park, California. The company owns Facebook, Instagram, and WhatsApp, among other products and services. Meta was once one of the world's most valuable companies, but as of 2022 is not one of the top twenty biggest companies in the United States. It is considered one of the Big Five American information technology companies, alongside Alphabet (Google), Amazon, Apple, and Microsoft. As of 2022, it is the least profitable of the five.
            Meta's products and services include Facebook, Messenger, Facebook Watch, and Meta Portal. It has also acquired Oculus, Giphy, Mapillary, Kustomer, Presize and has a 9.99% stake in Jio Platforms. In 2021, the company generated 97.5% of its revenue from the sale of advertising. In October 2021, the parent company of Facebook changed its name from Facebook, Inc., to Meta Platforms, Inc., to "reflect its focus on building the metaverse". According to Meta, the "metaverse" refers to the integrated environment that links all of the company's products and services""")
        
        with c2:
            st.subheader("2022 Stats: ")
            st.metric(label="Revenue", value="$116.81 billion", delta="-3.5")
            st.metric(label="Operating Income", value="$28.94 billion", delta="-2.2")
            st.metric(label="Net Income", value="$23.20 billion", delta="-2.4")
        
        st.write("# Latest News")
        show_news("facebook")
    if stock == "Microsoft":
        st.image("./data/microsoft_banner.jpg")
        st.write("# Microsoft Info")
        c1, c2 = st.columns((2, 1))
        with c1:
            st.write("""Microsoft Corporation is an American multinational technology corporation producing computer software, consumer electronics, personal computers, and related services. Headquartered at the Microsoft campus in Redmond, Washington, Microsoft's best-known software products are the Windows line of operating systems, the Microsoft Office suite, and the Internet Explorer and Edge web browsers. Its flagship hardware products are the Xbox video game consoles and the Microsoft Surface lineup of touchscreen personal computers. Microsoft ranked No. 21 in the 2020 Fortune 500 rankings of the largest United States corporations by total revenue; it was the world's largest software maker by revenue as of 2019. It is one of the Big Five American information technology companies, alongside Alphabet (Google), Amazon, Apple, and Meta.
            Microsoft Corporation, leading developer of personal-computer software systems and applications. The company also publishes books and multimedia titles, produces its own line of hybrid tablet computers, offers e-mail services, and sells electronic game systems and computer peripherals (input/output devices). It has sales offices throughout the world. In addition to its main research and development centre at its corporate headquarters in Redmond, Washington, U.S., Microsoft operates research labs in Cambridge, England (1997); Beijing, China (1998); Bengaluru, India (2005); Cambridge, Massachusetts (2008); New York, New York (2012); and Montreal, Canada (2015).""")
        
        with c2:
            st.subheader("2022 Stats: ")
            st.metric(label="Revenue", value="$198.3 billion", delta="2.8")
            st.metric(label="Operating Income", value="$83.4 billion", delta="2.5")
            st.metric(label="Net Income", value="$72.7 billion", delta="2.4")
        
        st.write("# Latest News")
        show_news("microsoft")
if selected == "Analysis":
    if stock == "Apple":
        st.write("# Apple Stock Analysis")
        analyis("AAPL")
    if stock == "Google":
        st.write("# Google Stock Analysis")
        analyis("GOOGL")
    if stock == "Meta":
        st.write("# Meta Stock Analysis")
        analyis("META")
    if stock == "Microsoft":
        st.write("# Microsoft Stock Analysis")
        analyis("MSFT")
if selected == "Predictions":
    if stock == "Apple":
        st.write("# Apple Stock Predictions")
        prediction_using_prophet("AAPL")
        prediction_using_random_forest("AAPL")
    if stock == "Google":
        st.write("# Google Stock Predictions")
        prediction_using_prophet("GOOGL")
        prediction_using_random_forest("GOOGL")
    if stock == "Meta":
        st.write("# Meta Stock Predictions")
        prediction_using_prophet("META")
        prediction_using_random_forest("META")
    if stock == "Microsoft":
        st.write("# Microsoft Stock Predictions")
        prediction_using_prophet("MSFT")
        prediction_using_random_forest("MSFT")