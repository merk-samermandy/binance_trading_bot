from binance.spot import Spot
import pandas as pd
import talib
import datetime
import time

def get_asset_balance(client, asset):
    account_info = client.account()
    balances = account_info.get('balances')
    for item in balances:
        if item['asset'] == asset:
            my_item = item
            break
    else:
        my_item = None

    return my_item

def get_candles(client, symbol, interval, limit):
    # Get the candles data for the specified symbol, period, and interval
    candles = client.klines(
        symbol=symbol,
        interval=interval,
        limit=limit
    )

    # Create a Pandas DataFrame from the candles data
    df = pd.DataFrame(candles, columns=[
        'open_time',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'close_time',
        'quote_asset_volume',
        'number_of_trades',
        'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume',
        'ignore'
    ])

    # Convert the column values to numerical values
    df = df.apply(pd.to_numeric)

    # Return the Pandas DataFrame
    return df

def main():

    status = 0

    # API key/secret are required for user data endpoints
    client = Spot(api_key=''
                ,api_secret='')

    while True:

        ticker_price = client.ticker_price("BTCUSDT")
        price = round(float(ticker_price['price']),8)

        # Get the candles data
        df = get_candles(client, "BTCUSDT", "1m", limit=50)

        df["EMA_9"] = talib.EMA(df["close"], timeperiod=9)
        df["EMA_20"] = talib.EMA(df["close"], timeperiod=20)
        df["RSI"] = talib.RSI(df['close'], timeperiod=14)
        df["SAR"] = talib.SAR(df['high'],df['low'], acceleration=0.02, maximum=0.2)
        df["time"] = pd.to_datetime(df['open_time'], unit='ms').dt.tz_localize('utc').dt.tz_convert('Europe/Madrid')

        rsi = df['RSI'].iloc[-1]
        ema_nine = df['EMA_9'].iloc[-1]
        ema_twenty = df['EMA_20'].iloc[-1]
        sar = df['SAR'].iloc[-1]
        date = df['time'].iloc[-1]

        print("\n")
        print(f"Time: {date}")
        print("\n")
        print(f"RSI: {rsi}")
        print(f"EMA_9: {ema_nine}")
        print(f"EMA_20: {ema_twenty}")
        print(f"SAR: {sar}")
        print(f"PRICE: {price}")

        print("\n")

        if status == 0:
            if rsi < 40:
                print("* Atención, RSI < 40 !")
                status = 1
            else:
                print("esperando un RSI < 40")

        if status == 1:
            if (df['EMA_9'].iloc[-2] < df['EMA_9'].iloc[-2]) and  (df['EMA_9'].iloc[-1] >= df['EMA_9'].iloc[-1]):
                print("* Atención, cruce de EMAs !")
                if 50 < rsi < 60:
                    status = 2
                    print("***COMPRAR***")

                    balance_usdt = get_asset_balance(client,"USDT")
                    usdt_qty = float(balance_usdt.get('free'))
                    ticker_price = client.ticker_price("BTCUSDT")
                    price = round(float(ticker_price['price']),8)
                    btc_quantity_buy = round((float(usdt_qty)) / price ,8)

                    print(f"You will buy {btc_quantity_buy:.8f} BTC with {usdt_qty} USDT at the current price of {price:.8f} USDT/BTC")


                    #Post a new order
                    params = {
                        'symbol': 'BTCUSDT',
                        'side': "BUY",
                        'type': 'MARKET',
                        'quoteOrderQty': usdt_qty
                        }

                    response = client.new_order(**params)
                    print(response)
                else:
                    status = 0
            else:
                print("Esperando a cruce de EMAs")

        if status == 2:
            if (df['SAR'].iloc[-2] < df['close'].iloc[-2]) and (df['SAR'].iloc[-1] >= df['close'].iloc[-1]):
                print("* Atención, cruce de SAR con Close Price !")
                status == 0
                print("***VENDER***")

                balance_btc = get_asset_balance(client,"BTC")
                btc_qty = float(balance_btc.get('free'))
                ticker_price = client.ticker_price("BTCUSDT")
                price = round(float(ticker_price['price']),8)
                usdt_quantity_sell = round((float(btc_qty)) * price ,8)

                print(f"You will sell {btc_qty:.8f} BTC for {usdt_quantity_sell} USDT at the current price of {price:.8f} USDT/BTC")

                #Post a new order
                params = {
                    'symbol': 'BTCUSDT',
                    'side': "SELL",
                    'type': 'MARKET',
                    'quoteOrderQty': usdt_quantity_sell
                    }

                response = client.new_order(**params)
                print(response)
            else:
                print("Esperando a cruce de SAR con precio")

        print(f"STATUS: {status}")

        time.sleep(60)    

if __name__ == "__main__":
    
    main()