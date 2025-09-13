import time
from turtle import position
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from autotrade.settings import MARKETS
from .coinex import CoinExHTTPClient
import pandas as pd
import random
markets = settings.MARKETS
http_client = CoinExHTTPClient()

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
            print('status',status)

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
    sleep = 45
    delay = 48
    time.sleep(delay)
    SHOCK_THRESHOLD_1 = 0.0055
    SHOCK_THRESHOLD_2 = 0.0072
    CUM_SHOCK_THRESHOLD_1 = 0.0010
    CUM_SHOCK_THRESHOLD_2 = 0.0140
    LIMIT = 50
    MIN_PROFIT = 0.3 / 100
    MAX_PROFIT = 0.02
    MAX_LOSS = 1 / 100
    BORDER_OFFSET = 0.05 / 100
    MAX_TRY_SHOCK = 5
    from .models import MarketTicker, MarketStatus, FundingRate, AnalizeDepth
    
    def set_INTERVAL(last_price):
        scale = last_price * (1 / 10000)
        scale_list = [100, 10, 1, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001]

        for s in scale_list:
            clc = s / scale
            if clc <= 1:
                return format(s, "f").rstrip("0").rstrip(".")
        return format(scale_list[-1], "f").rstrip("0").rstrip(".")





    def find_support(df):
        SHOCK_THRESHOLD_1_try = 1
        s1 = df
        while True:
            SHOCK_THRESHOLD_1_EFF =SHOCK_THRESHOLD_1 * (1 - (SHOCK_THRESHOLD_1_try / 50)) if SHOCK_THRESHOLD_1_try > 1 else  SHOCK_THRESHOLD_1
            s1 = df[df['volume/24h'] >SHOCK_THRESHOLD_1_EFF]
            if SHOCK_THRESHOLD_1_try>MAX_TRY_SHOCK or len(s1) == 0:
                s1 = df[df['price'] == df['price'].max()]
                break
            if len(s1)<len(df):
                break
            SHOCK_THRESHOLD_1_try += 1

        CUM_SHOCK_THRESHOLD_1_try = 1
        while len(s1)>0:
            CUM_SHOCK_THRESHOLD_1_EFF = SHOCK_THRESHOLD_1 * (1 - (SHOCK_THRESHOLD_1_try / 50)) if CUM_SHOCK_THRESHOLD_1_try > 1 else CUM_SHOCK_THRESHOLD_1
            s1 = df[df['cum-volume/24h'] >CUM_SHOCK_THRESHOLD_1_EFF]
            if SHOCK_THRESHOLD_1_try>MAX_TRY_SHOCK or len(s1) == 0:
                s1 = df[df['price'] == df['price'].min()]
                break
            if len(s1)<len(df):
                break
            SHOCK_THRESHOLD_1_try += 1

        s2 = df[df['volume/24h'] >SHOCK_THRESHOLD_2]
        s2 = s2[s2['cum-volume/24h'] >CUM_SHOCK_THRESHOLD_2]

        power_shock = 0
        power_cum_shock = 0
        if len(s1) == 0:
            s1 = df[df['price'] == df['price'].min()]
        s1 = float(s1['price'].max())
        if len(s2) == 0:
            return s1 , 0, power_shock, power_cum_shock
        s2_ = s2[s2['price']== s2['price'].max()]
        s2 = float(s2_['price'].max())
        power_shock = float(s2_['volume/24h'].max())
        power_cum_shock = float(s2_['cum-volume/24h'].max())
        return s1 , s2, power_shock, power_cum_shock

    def find_resistance(df):
        SHOCK_THRESHOLD_1_try = 1
        r1 = df
        while len(r1)>0:
            SHOCK_THRESHOLD_1_EFF =SHOCK_THRESHOLD_1 * (1 - (SHOCK_THRESHOLD_1_try / 50)) if SHOCK_THRESHOLD_1_try > 1 else  SHOCK_THRESHOLD_1
            r1 = df[df['volume/24h'] >SHOCK_THRESHOLD_1_EFF]
            if SHOCK_THRESHOLD_1_try>MAX_TRY_SHOCK or len(r1) == 0:
                r1 = df[df['price'] == df['price'].max()]
                break
            if len(r1)<len(df):
                break
            SHOCK_THRESHOLD_1_try += 1

        CUM_SHOCK_THRESHOLD_1_try = 1
        while len(r1)>0:
            CUM_SHOCK_THRESHOLD_1_EFF = SHOCK_THRESHOLD_1 * (1 - (SHOCK_THRESHOLD_1_try / 50)) if CUM_SHOCK_THRESHOLD_1_try > 1 else CUM_SHOCK_THRESHOLD_1
            r1 = df[df['cum-volume/24h'] >CUM_SHOCK_THRESHOLD_1_EFF]
            if SHOCK_THRESHOLD_1_try>MAX_TRY_SHOCK or len(r1) == 0:
                r1 = df[df['price'] == df['price'].max()]
                break
            if len(r1)<len(df):
                break
            SHOCK_THRESHOLD_1_try += 1

        r2 = df[df['volume/24h'] >SHOCK_THRESHOLD_2]
        r2 = r2[r2['cum-volume/24h'] >CUM_SHOCK_THRESHOLD_2]


        power_shock = 0
        power_cum_shock = 0
        if len(r1) == 0:
            r1 = df[df['price'] == df['price'].max()]
        r1 = float(r1['price'].min())
        if len(r2) == 0:
            return r1 , 0, power_shock, power_cum_shock
        
        r2_ = r2[r2['price']== r2['price'].min()]
        r2 = float(r2_['price'].min())
        power_shock = float(r2_['volume/24h'].min())
        power_cum_shock = float(r2_['cum-volume/24h'].min())
        return r1 , r2, power_shock, power_cum_shock



    while True:
        for i in markets:
            last_price = MarketTicker.objects.filter(market=i).order_by('-create_at').values_list('last', flat=True).first()
            INTERVAL = set_INTERVAL(last_price)
            maker_fee_rate = MarketStatus.objects.filter(market=i).order_by('-create_at').values_list('maker_fee_rate', flat=True).first()
            latest_funding_rate = FundingRate.objects.filter(market=i).order_by('-created_at').values_list('max_funding_rate', flat=True).first()
            fee = (maker_fee_rate + abs(latest_funding_rate)) * 2
            futures_depth = http_client.get_futures_depth(i, LIMIT, INTERVAL)

            futures_depth = futures_depth['data']
            seller = pd.DataFrame(futures_depth['depth']['asks'],columns=['price', 'volume'])
            buyer = pd.DataFrame(futures_depth['depth']['bids'],columns=['price', 'volume'])


            seller['side'] = 1
            buyer['side'] = -1

            seller['volume'] = seller['volume'].apply(float)
            buyer['volume'] = buyer['volume'].apply(float)

            buyer = buyer.sort_values(by=['price'],ascending=False)
            seller = seller.sort_values(by=['price'],ascending=True)

            volume_last_24h = MarketTicker.objects.order_by('-create_at').values_list('volume', flat=True).first()
            seller['volume/24h'] = seller['volume'] / volume_last_24h
            buyer['volume/24h'] = buyer['volume'] / volume_last_24h

            seller['cum-volume/24h'] = seller['volume/24h'].cumsum()
            buyer['cum-volume/24h'] = buyer['volume/24h'].cumsum()

            r1, r2, sel_power_shock, sel_power_cum_shock = find_resistance(seller)
            s1, s2, buy_power_shock, buy_power_cum_shock = find_support(buyer)

            buy_price = float(s2 * (1 + BORDER_OFFSET))
            min_buy_target = float(s2 * (1 + MIN_PROFIT + fee))
            max_buy_target = float(buy_price * (1 + MAX_PROFIT + fee))
            buy_target = min(float(r1 * (1 - BORDER_OFFSET)),max_buy_target)
            if buy_price > 0 and buy_target > 0:
                buy_rate_profit = (buy_target / buy_price ) - 1 - fee
            else:
                buy_rate_profit = 0 
            buy_stop_loss = float(buy_price * (1 - min(MAX_LOSS,(buy_rate_profit/3))))
            if (buy_target < min_buy_target) or buy_price ==0:
                open_buy = False
                buy_rate_loss = 0
                buy_rr = 0
            else:
                open_buy = True
                buy_rate_loss = (buy_stop_loss / buy_price) - 1 - fee
                buy_rr = buy_rate_profit / abs(buy_rate_loss)

            sell_price = float(r2 * (1 - BORDER_OFFSET))
            min_sell_target = float(r2 * (1 - MIN_PROFIT - fee))
            max_sel_target = float(buy_price * (1 - MAX_PROFIT - fee))
            sell_target = max(float(s1 * (1 + BORDER_OFFSET)),max_sel_target)
            if sell_price > 0 and sell_target > 0:
                sell_rate_profit = ( sell_price / sell_target ) - 1 - fee
            else:
                sell_rate_profit = 0
            sell_stop_loss = float(sell_price * (1 + min(MAX_LOSS,(sell_rate_profit/3))))
            if (sell_target > min_sell_target) or sell_price == 0:
                open_sell = False
                sell_rate_loss = 0
                sell_rr = 0
            else:
                open_sell = True
                sell_rate_loss = (sell_price / sell_stop_loss) - 1 - fee
                sell_rr = sell_rate_profit / abs(sell_rate_loss)
            
            open_buy = open_buy * (buy_price < (last_price * (1 - buy_rate_profit) ))
            open_sell = open_sell * (sell_price<(last_price * (1 + sell_rate_profit)))
            

            if open_sell and open_buy:
                shock_sel2buy = sel_power_shock / buy_power_shock
                shock_buy2sel = buy_power_shock / sel_power_shock
                cum_shock_sel2buy = sel_power_cum_shock / buy_power_cum_shock
                cum_shock_buy2sel = buy_power_cum_shock / sel_power_cum_shock
                rr_sel2buy = sell_rr / buy_rr
                rr_buy2sel = buy_rr / sell_rr
                sel_esp = (shock_sel2buy * 4.5) + (cum_shock_sel2buy * 3) + (rr_sel2buy * 1)
                buy_esp = (shock_buy2sel * 4.5) + (cum_shock_buy2sel * 3) + (rr_buy2sel * 1)
                sell = sel_esp > (buy_esp * 1.5)
                buy = buy_esp > (sel_esp * 1.5)
            else:
                buy = open_buy
                sell = open_sell
            done = False
            while done == False:
                try:
                    AnalizeDepth.objects.update_or_create(
                        market=i,
                        defaults={
                            "support_main": s2,
                            "support_second": s1,
                            "resistance_main": r2,
                            "resistance_second": r1,
                            "buy_price": buy_price,
                            "buy_target": buy_target,
                            "min_buy_target": min_buy_target,
                            "buy_stop_loss": buy_stop_loss,
                            "open_buy": open_buy,
                            "sell_price": sell_price,
                            "min_sell_target": min_sell_target,
                            "sell_target": sell_target,
                            "sell_stop_loss": sell_stop_loss,
                            "open_sell": open_sell,
                            "last_price": last_price,
                            "fee": fee,
                            "sel_power_shock": sel_power_shock,
                            "sel_power_cum_shock": sel_power_cum_shock,
                            "buy_power_shock": buy_power_shock,
                            "buy_power_cum_shock": buy_power_cum_shock,
                            "buy_rate_profit": buy_rate_profit,
                            "buy_rr": buy_rr,
                            "sell_rate_profit": sell_rate_profit,
                            "sell_rr": sell_rr,
                            "buy": buy,
                            "sell": sell,
                            "update_at":timezone.now()
                        }
                        )
                    done = True
                except Exception as e:
                    time.sleep(delay_by_record)
                    done = False
                    continue


        time.sleep(sleep)


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

        sell_count = analize.filter(sell=True).count()
        buy_count = analize.filter(buy=True).count()
        allow_sell = sell_count>buy_count
        allow_buy = buy_count>sell_count
        if allow_sell:
            analize = analize.filter(sell=True)
            analize = analize.order_by('-sel_power_shock')
            side = "sell"
        else:
            analize = analize.order_by('-buy_power_shock')
            analize = analize.filter(buy=True)
            side = "buy"
        balance = http_client.get_futures_balance()['data'][0]['available']
        balance = float(balance)
        balance_per_order = balance / (buy_count if allow_buy else sell_count)
        balance_per_order = balance_per_order


        

        for i in analize:
            time.sleep(random.randint(50, 100)/10)
            min_amount = MarketStatus.objects.filter(market=i.market).order_by('-create_at').values_list('min_amount', flat=True).first()
            price = i.buy_price if side == "buy" else i.sell_price
            amount = (balance_per_order / price)*0.98

            amount = min_amount
            if amount < min_amount:
                continue
            amount = min_amount
            get_futures_pending_orders = http_client.get_futures_pending_orders(market=i.market,side=side)
            position = http_client.get_futures_position(market=i.market)
            if len(position['data'])>0:
                continue

            if len(get_futures_pending_orders['data'])>0:
                continue
            order = http_client.place_futures_order(market=i.market,side=side,type_="limit",amount=str(amount),price=str(price))
            if order['code']!= 0:
                continue
            

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
    from .models import Order
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
            if order is None:
                http_client.close_futures_position(i['market'])
                print('close position',i)
                print('w'*150)
                continue

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
            if i['leverage'] != '3':
                http_client.set_leverage_futures_position(i['market'],'3')
                print('set leverage',i)
            if i['margin_mode'] == 'cross':
                http_client.set_leverage_futures_position(i['market'],'3')
                print('set margin mode',i)



        
    
