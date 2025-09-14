import time
from turtle import position
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from autotrade.settings import MARKETS
from .coinex import CoinExHTTPClient
import pandas as pd
import random
import math
markets = settings.MARKETS
http_client = CoinExHTTPClient()


LEVERAGE = 3
STD_X_LINE_1 = 2
STD_X_LINE_2 = 3


SHOCK_THRESHOLD_1 = 0.8 / 100
SHOCK_THRESHOLD_2 = 1.0 / 100
CUM_SHOCK_THRESHOLD_1 = 0.15 / 100
CUM_SHOCK_THRESHOLD_2 = 0.25 / 100
LIMIT = 50
MIN_PROFIT = 1 / 100
MAX_PROFIT = 3/100
MAX_LOSS = 0.8 / 100
BORDER_OFFSET = 0.05 / 100
MAX_TRY_SHOCK = 10


delay_by_record = 1/10
def update_funding_rate():
    sleep = 1 * 60 * 60
    delay = 0

    time.sleep(delay)
    from .models import FundingRate
    while True:

        for market in markets:
            funding_rate = http_client.get_funding_rate(market)
            funding_rate = funding_rate['data'][0]
            FundingRate.objects.create(
                market = market,
                mark_price = funding_rate['mark_price'],
                latest_funding_rate = funding_rate['latest_funding_rate'],
                latest_funding_time = funding_rate['latest_funding_time'],
                next_funding_rate = funding_rate['next_funding_rate'],
                max_funding_rate = funding_rate['max_funding_rate'],
                min_funding_rate = funding_rate['min_funding_rate'],
                next_funding_time = funding_rate['next_funding_time'],
            )
            time.sleep(delay_by_record)

        time.sleep(sleep)

def update_market_status():
    sleep = 60 * 60 
    delay = 14
    time.sleep(delay)
    from .models import MarketStatus
    while True:
        for i in markets:
            status = http_client.get_market_status(i)

            status = status['data'][0]

            MarketStatus.objects.create(
                market = i,
                maker_fee_rate = status['maker_fee_rate'],
                taker_fee_rate = status['taker_fee_rate'],
                min_amount = status['min_amount'],
            )
            time.sleep(delay_by_record)

        time.sleep(sleep)

def update_market_ticker():
    sleep = 60 * 5
    delay = 20
    time.sleep(delay)
    from .models import MarketTicker
    while True:
        for i in markets:
            market_ticker = http_client.get_market_ticker(i)
            market_ticker = market_ticker['data'][0]
            MarketTicker.objects.create(
                market = i,
                close = market_ticker['close'],
                high = market_ticker['high'],
                index_price = market_ticker['index_price'],
                last = market_ticker['last'],
                low = market_ticker['low'],
                mark_price = market_ticker['mark_price'],
                open = market_ticker['open'],
                value = market_ticker['value'],
                volume = market_ticker['volume'],
            )
            time.sleep(delay_by_record)
        time.sleep(sleep)



def update_futures_depth():
    sleep = 30
    delay = 5
    time.sleep(delay)
    from .models import MarketTicker, OrderBook
    
    def set_INTERVAL(last_price):
        scale = last_price * (1 / 10000)
        scale_list = [100, 10, 1, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001]

        for s in scale_list:
            clc = s / scale
            if clc <= 1:
                return format(s, "f").rstrip("0").rstrip(".")
        return format(scale_list[-1], "f").rstrip("0").rstrip(".")
    


    while True:
        for i in markets:
            last_price = MarketTicker.objects.filter(market=i).order_by('-create_at').values_list('last', flat=True).first()
            last_price = float(last_price)
            INTERVAL = set_INTERVAL(last_price)
            futures_depth = http_client.get_futures_depth(i, LIMIT, INTERVAL)
            volume_last_24h = MarketTicker.objects.order_by('-create_at').values_list('volume', flat=True).first()

            futures_depth = futures_depth['data']
            seller = pd.DataFrame(futures_depth['depth']['asks'],columns=['price', 'volume'])
            seller['side'] = 'seller'
            buyer = pd.DataFrame(futures_depth['depth']['bids'],columns=['price', 'volume'])
            buyer['side'] = 'buyer'
            for j in [seller, buyer]:
                j['price'] = j['price'].apply(float)
                j['volume'] = j['volume'].apply(float)
                j['volume/24h'] = j['volume'] / volume_last_24h
                j['cum-volume/24h'] = j['volume/24h'].cumsum()
                j['log_cum-volume/24h'] = j['volume/24h'].cumsum().apply(lambda x: math.log(1+x))
                j['distance'] = (j['price'] - last_price) / last_price
                j['distance'] = j['distance'].apply(abs)
                j['weight'] = 1/ (j['distance'] + 1) 
            df = pd.concat([seller, buyer])

            df = df.to_dict(orient='records')
            object_list = []
            datetime = timezone.now()
            for k in df:
                object_list.append(OrderBook(
                    market=i,
                    side=k['side'],
                    price=k['price'],
                    volume=k['volume'],
                    volume_24h=k['volume/24h'],
                    cum_volume_24h=k['cum-volume/24h'],
                    log_cum_volume_24h=k['log_cum-volume/24h'],
                    weight=k['weight'],
                    distance=k['distance'],
                    datetime=datetime,
                ))
            OrderBook.objects.bulk_create(object_list)


        time.sleep(sleep)

def analize():
    from .models import MarketStatus, FundingRate, OrderBook

    def get_lines(df:pd.DataFrame, last_price:float):
        std_volume = df['volume/24h'].std()
        mean_volume = df['volume/24h'].mean()
        std_cum_volume = df['log_cum-volume/24h'].std()
        mean_cum_volume = df['log_cum-volume/24h'].mean()
        shock_volume_1 = std_volume * STD_X_LINE_1
        shock_cum_volume_1 = std_cum_volume * STD_X_LINE_1
        shock_volume_2 = std_volume * STD_X_LINE_2
        shock_cum_volume_2 = std_cum_volume * STD_X_LINE_2
        

        dic = {'line_1':0, 'line_2':0, 'shock_1':0, "shock_2":0, "shock_cum_1":0, "shock_cum_2":0, "weight_1":0, "weight_2":0}

        df = df[df['volume/24h']>shock_volume_1]
        df = df[df['log_cum-volume/24h']>shock_cum_volume_1]
        if len(df) > 0:
            df_line_1 = df[df['weight']==df['weight'].max()].to_dict(orient='records')[0]
            dic['line_1'] = float(df_line_1['price'])
            dic['shock_1'] = float(df_line_1['volume/24h'])
            dic['shock_cum_1'] = float(df_line_1['log_cum-volume/24h'])
            dic['weight_1'] = float(df_line_1['weight'])


        df = df[df['volume/24h']>shock_volume_2]
        df = df[df['log_cum-volume/24h']>shock_cum_volume_2]
        if len(df) > 0:
            df_line_2 = df[df['weight']==df['weight'].max()].to_dict(orient='records')[0]
            dic['line_2'] = float(df_line_2['price'])
            dic['shock_2'] = float(df_line_2['volume/24h'])
            dic['shock_cum_2'] = float(df_line_2['log_cum-volume/24h'])
            dic['weight_2'] = float(df_line_2['weight'])
        return dic

    while True:
        for i in markets:
            maker_fee_rate = MarketStatus.objects.filter(market=i).order_by('-create_at').values_list('maker_fee_rate', flat=True).first()
            latest_funding_rate = FundingRate.objects.filter(market=i).order_by('-created_at').values_list('max_funding_rate', flat=True).first()
            fee = (maker_fee_rate + abs(latest_funding_rate)) * 2

    return 0

def update_order():
    sleep = 60
    delay = 5
    from .models import MarketTicker, MarketStatus, FundingRate, AnalizeDepth, Order

    time.sleep(delay)

    while True:
        for i in markets:
            try:
                pending_orders = http_client.cancel_all_orders(market=i)
            except Exception as e:
                time.sleep(delay_by_record)
                continue

        analize = AnalizeDepth.objects.filter(Q(buy=True) | Q(sell=True)).order_by('-create_at')

        if not analize.exists():
            print("no analize")
            continue

        count = analize.count()
        analize = analize.order_by('-buy_power_shock','-sel_power_shock')
        balance = http_client.get_futures_balance()['data'][0]['available']
        balance = float(balance)
        balance_per_order = balance / count
        balance_per_order = balance_per_order


        

        for i in analize:
            time.sleep(random.randint(50, 100)/10)
            min_amount = MarketStatus.objects.filter(market=i.market).order_by('-create_at').values_list('min_amount', flat=True).first()
            price = i.buy_price if i.buy else i.sell_price
            amount = (balance_per_order / price)*0.98
            side = "buy" if i.buy else "sell"

            amount = min_amount
            if amount < min_amount:
                continue
            amount = min_amount
            get_futures_pending_orders = http_client.get_futures_pending_orders(market=i.market,side=side,limit=10)
            position = http_client.get_futures_position(market=i.market)
            if len(position['data'])>0:
                continue

            if len(get_futures_pending_orders['data'])>0:
                continue
            order = http_client.place_futures_order(market=i.market,side=side,type_="limit",amount=str(amount),price=str(price))
            if order['code']!= 0:
                print('-'*10,'error order','-'*10)
                print(order)
                print(i,side,price,amount)
                continue

            print('new order',i.market)

            Order.objects.update_or_create(
                market=i.market,
                defaults={
                "price":price,
                "stop_loss":i.buy_stop_loss if side == "buy" else i.sell_stop_loss,
                "target":i.buy_target if side == "buy" else i.sell_target,
                "amount":amount,
                "side":side,
                "client_id":"",
                "order_id":order['data']['order_id'],
                "fee":order['data']['fee'],
                "realized_pnl":order['data']['realized_pnl'],
                "status":'pending',
                }
            )


        time.sleep(sleep)
    


def modify_position():
    sleep = 20
    delay = 10
    from .models import Order, AnalizeDepth
    time.sleep(delay)
    while True:
        time.sleep(sleep)
        position = http_client.get_futures_position()
        position = position['data']
        if len(position) == 0:
            print('no position')
            continue
        for i in position:
            order = Order.objects.filter(market=i['market']).order_by('-created_at').first()
            analize = AnalizeDepth.objects.filter(market=i['market']).order_by('-create_at').first()
            if order is None:
                http_client.close_futures_position(i['market'])
                print('close position',i)
                continue

            unrealized_pnl = float(i['unrealized_pnl'])
            unrealized_pnl_rate  = unrealized_pnl / float(i['cml_position_value'])
            if analize is None:
                if unrealized_pnl > 0:
                    http_client.close_futures_position(i['market'])
                    print('close position',i)
                    continue

            if unrealized_pnl_rate >1:
                http_client.set_stop_loss_futures_position(i['market'],order.price)
            elif unrealized_pnl_rate >2:
                http_client.set_stop_loss_futures_position(i['market'],(order.price*1.01))



            if i['side']=='long' and order.side=='sell':
                http_client.close_futures_position(i['market'])
                print('close position',i)
                continue
            if i['side']=='short' and order.side=='buy':
                http_client.close_futures_position(i['market'])
                print('close position',i)
                continue
            if i['stop_loss_price']=='0':
                http_client.set_stop_loss_futures_position(i['market'],order.stop_loss)
                print('set stop loss',i)
            if i['take_profit_price']=='0':
                http_client.set_take_profit_futures_position(i['market'],order.target)
                print('set take profit',i)
            if i['leverage'] != str(LEVERAGE):
                http_client.set_leverage_futures_position(i['market'],str(LEVERAGE))
                print('set leverage',i)
            if i['margin_mode'] == 'cross':
                http_client.set_leverage_futures_position(i['market'],str(LEVERAGE))
                print('set margin mode',i)



        
    
