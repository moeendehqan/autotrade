import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode

BASE_URL = "https://api.coinex.com/v2"
WS_SPOT_URL = "wss://socket.coinex.com/v2/spot"
WS_FUTURES_URL = "wss://socket.coinex.com/v2/futures"

ACCESS_ID = "1F3D430A2B024771A4418D782C5A89E2"
SECRET_KEY = "732025850919D7AAAE2D2C403CC338359710AF042FE93EC8"

def get_timestamp() -> str:
    """برگرداندن زمان فعلی به میلی‌ثانیه"""
    return str(int(time.time() * 1000))



def sign_request(method: str, request_path: str, body: str = "", timestamp: str = None) -> str:
    """ساخت signature برای HTTP"""
    if timestamp is None:
        timestamp = get_timestamp()
    prepared_str = method.upper() + request_path + body + timestamp
    signed_str = hmac.new(
        SECRET_KEY.encode("latin-1"),
        msg=prepared_str.encode("latin-1"),
        digestmod=hashlib.sha256
    ).hexdigest().lower()
    return signed_str, timestamp

class CoinExHTTPClient:
    def __init__(self, base_url: str = BASE_URL):
        self.access_id = ACCESS_ID
        self.secret_key = SECRET_KEY
        self.base_url = base_url

    def _request(self, method: str, path: str, params=None, data=None):
        timestamp = get_timestamp()
        query_str = ""
        if params:
            # مرتب سازی پارامترها به ترتیب حروف الفبا
            sorted_params = sorted(params.items())
            query_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            path_for_sign = path + "?" + query_str
        else:
            path_for_sign = path

        body = json.dumps(data) if data else ""

        signature, timestamp = sign_request(method, path_for_sign, body, timestamp)

        headers = {
            "X-COINEX-KEY": self.access_id,
            "X-COINEX-SIGN": signature,
            "X-COINEX-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

        url = self.base_url + path
        if query_str:
            url += "?" + query_str

        response = requests.request(method, url, headers=headers, data=body if body else None)
        return response.json()


    # --- موجود ---
    def get_spot_balance(self):
        return self._request("GET", "/assets/spot/balance")

    def get_pending_orders(self, market="BTCUSDT", side="buy", page=1, limit=10):
        params = {
            "market": market,
            "market_type": "SPOT",
            "side": side,
            "page": page,
            "limit": limit
        }
        return self._request("GET", "/spot/pending-order", params=params)

    # --- جدید: Market Depth ---
    def get_futures_depth(self, market: str, limit: int = 5, interval: str = "0.01"):
        """
        دریافت عمق بازار Futures
        :param market: مثل "BTCUSDT"
        :param limit: تعداد آیتم‌ها (5, 10, 20, 50)
        :param interval: بازه‌ی ادغام ("0", "0.01", "0.1", ...)
        """
        params = {
            "market": market,
            "limit": limit,
            "interval": interval
        }
        return self._request("GET", "/futures/depth", params=params)
    # --- جدید: Funding Rate ---
    def get_funding_rate(self, markets: str = ""):
        """
        دریافت Funding Rate بازارهای Futures
        :param markets: لیست مارکت‌ها مثل "BTCUSDT,ETHUSDT" (حداکثر 10 تا)
                        اگر خالی باشه، همه مارکت‌ها برگردونده میشه
        """
        params = {"market": markets} if markets else {}
        return self._request("GET", "/futures/funding-rate", params=params)
    # --- جدید: Market Status ---
    def get_market_status(self, markets: str = ""):
        """
        دریافت وضعیت مارکت‌های Futures
        :param markets: لیست مارکت‌ها مثل "BTCUSDT,ETHUSDT" (حداکثر 10 تا)
                        اگر خالی باشه، همه مارکت‌ها برگردونده میشه
        """
        params = {"market": markets} if markets else {}
        return self._request("GET", "/futures/market", params=params)
    # --- جدید: Market Information ---
    def get_market_ticker(self, markets: str = ""):
        """
        دریافت اطلاعات مارکت‌های Futures
        :param markets: لیست مارکت‌ها مثل "BTCUSDT,ETHUSDT" (حداکثر 10 تا)
                        اگر خالی باشه، همه مارکت‌ها برگردونده میشه
        """
        params = {"market": markets} if markets else {}
        return self._request("GET", "/futures/ticker", params=params)
    # --- جدید: Market Transactions ---
    def get_market_deals(self, market: str, limit: int = 100, last_id: int = 0):
        """
        دریافت معاملات اخیر (Deals) مارکت‌های Futures
        :param market: نام مارکت مثل "BTCUSDT"
        :param limit: تعداد معاملات برگردانده شده (پیش‌فرض 100، حداکثر 1000)
        :param last_id: شروع از این TxID، 0 = آخرین رکورد
        """
        params = {"market": market, "limit": limit, "last_id": last_id}
        return self._request("GET", "/futures/deals", params=params)

    def place_futures_order(
        self,
        market: str,
        market_type: str,
        side: str,
        type_: str,
        amount: str,
        price: str = None,
        client_id: str = None,
        is_hide: bool = False,
        stp_mode: str = None
    ):
        """
        ثبت سفارش در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell")
        :param type_: نوع سفارش ("limit" یا "market")
        :param amount: مقدار سفارش
        :param price: قیمت سفارش (برای limit الزامی)
        :param client_id: شناسه دلخواه سفارش
        :param is_hide: مخفی کردن سفارش در عمق بازار
        :param stp_mode: حالت محافظت از خود معامله (ct, cm, both)
        """
        data = {
            "market": market,
            "market_type": market_type,
            "side": side,
            "type": type_,
            "amount": amount,
            "is_hide": is_hide
        }
        if price is not None:
            data["price"] = price
        if client_id is not None:
            data["client_id"] = client_id
        if stp_mode is not None:
            data["stp_mode"] = stp_mode

        return self._request("POST", "/futures/order", data=data)


    # --- جدید: Place Futures Stop Order ---
    def place_futures_stop_order(
        self,
        market: str,
        market_type: str,
        side: str,
        type_: str,
        amount: str,
        trigger_price_type: str,
        trigger_price: str,
        price: str = None,
        client_id: str = None,
        is_hide: bool = False,
        stp_mode: str = None
    ):
        """
        ثبت سفارش Stop در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell")
        :param type_: نوع سفارش ("limit" یا "market")
        :param amount: مقدار سفارش
        :param trigger_price_type: نوع قیمت Trigger ("latest_price", "mark_price", "index_price")
        :param trigger_price: قیمت Trigger برای فعال شدن سفارش
        :param price: قیمت سفارش (برای limit الزامی)
        :param client_id: شناسه دلخواه سفارش
        :param is_hide: مخفی کردن سفارش در عمق بازار
        :param stp_mode: حالت محافظت از خود معامله (ct, cm, both)
        """
        data = {
            "market": market,
            "market_type": market_type,
            "side": side,
            "type": type_,
            "amount": amount,
            "trigger_price_type": trigger_price_type,
            "trigger_price": trigger_price,
            "is_hide": is_hide
        }
        if price is not None:
            data["price"] = price
        if client_id is not None:
            data["client_id"] = client_id
        if stp_mode is not None:
            data["stp_mode"] = stp_mode

        return self._request("POST", "/futures/stop-order", data=data)
    # --- جدید: Query Futures Order Status ---
    def get_futures_order_status(self, market: str, order_id: int):
        """
        دریافت وضعیت سفارش در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param order_id: شناسه سفارش
        """
        params = {
            "market": market,
            "order_id": order_id
        }
        return self._request("GET", "/futures/order-status", params=params)

    # --- متد اصلاح شده برای دریافت سفارشات Futures که هنوز پر نشده‌اند ---
    def get_futures_pending_orders(self, market: str = None, side: str = None, page: int = 1, limit: int = 10):
        params = {
            "market": market,
            "market_type": "FUTURES",
            "side": side,
            "page": page,
            "limit": limit
        }
        # حذف پارامترهای None
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", "/futures/pending-order", params=params)



    # --- جدید: Get Filled Futures Orders ---
    def get_futures_finished_orders(
        self,
        market: str = None,
        market_type: str = "FUTURES",
        side: str = None,
        page: int = 1,
        limit: int = 10
    ):
        """
        دریافت سفارشات تکمیل شده (Filled Orders) در Futures
        :param market: نام مارکت مثل "CETUSDT" (اختیاری)
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell") (اختیاری)
        :param page: شماره صفحه برای Pagination
        :param limit: تعداد سفارش در هر صفحه
        """
        params = {"market_type": market_type, "page": page, "limit": limit}
        if market is not None:
            params["market"] = market
        if side is not None:
            params["side"] = side

        return self._request("GET", "/futures/finished-order", params=params)

    # --- جدید: Get Unfilled Futures Stop Orders ---
    def get_futures_pending_stop_orders(
        self,
        market: str = None,
        market_type: str = "FUTURES",
        side: str = None,
        client_id: str = None,
        page: int = 1,
        limit: int = 10
    ):
        """
        دریافت سفارشات Stop تکمیل نشده (Pending Stop Orders) در Futures
        :param market: نام مارکت مثل "CETUSDT" (اختیاری)
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell") (اختیاری)
        :param client_id: شناسه دلخواه سفارش (اختیاری)
        :param page: شماره صفحه برای Pagination
        :param limit: تعداد سفارش در هر صفحه
        """
        params = {"market_type": market_type, "page": page, "limit": limit}
        if market is not None:
            params["market"] = market
        if side is not None:
            params["side"] = side
        if client_id is not None:
            params["client_id"] = client_id

        return self._request("GET", "/futures/pending-stop-order", params=params)

    # --- جدید: Get Filled Futures Stop Orders ---
    def get_futures_finished_stop_orders(
        self,
        market: str = None,
        market_type: str = "FUTURES",
        side: str = None,
        page: int = 1,
        limit: int = 10
    ):
        """
        دریافت سفارشات Stop تکمیل شده (Filled Stop Orders) در Futures
        :param market: نام مارکت مثل "CETUSDT" (اختیاری)
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell") (اختیاری)
        :param page: شماره صفحه برای Pagination
        :param limit: تعداد سفارش در هر صفحه
        """
        params = {"market_type": market_type, "page": page, "limit": limit}
        if market is not None:
            params["market"] = market
        if side is not None:
            params["side"] = side

        return self._request("GET", "/futures/finished-stop-order", params=params)

    # --- جدید: Modify Futures Order ---
    def modify_futures_order(
        self,
        market: str,
        market_type: str,
        order_id: int,
        amount: str = None,
        price: str = None
    ):
        """
        ویرایش سفارش موجود در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param order_id: شناسه سفارش
        :param amount: مقدار جدید سفارش (باید حداقل یکی از amount یا price داده شود)
        :param price: قیمت جدید سفارش (باید حداقل یکی از amount یا price داده شود)
        """
        data = {
            "market": market,
            "market_type": market_type,
            "order_id": order_id
        }
        if amount is not None:
            data["amount"] = amount
        if price is not None:
            data["price"] = price

        return self._request("POST", "/futures/modify-order", data=data)

    # --- جدید: Modify Futures Stop Order ---
    def modify_futures_stop_order(
        self,
        market: str,
        market_type: str,
        stop_id: int,
        amount: str = None,
        price: str = None,
        trigger_price: str = None
    ):
        """
        ویرایش سفارش Stop موجود در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param stop_id: شناسه سفارش Stop
        :param amount: مقدار جدید سفارش (باید حداقل یکی از amount، price یا trigger_price داده شود)
        :param price: قیمت جدید سفارش (باید حداقل یکی از amount، price یا trigger_price داده شود)
        :param trigger_price: قیمت Trigger جدید (باید حداقل یکی از amount، price یا trigger_price داده شود)
        """
        data = {
            "market": market,
            "market_type": market_type,
            "stop_id": stop_id
        }
        if amount is not None:
            data["amount"] = amount
        if price is not None:
            data["price"] = price
        if trigger_price is not None:
            data["trigger_price"] = trigger_price

        return self._request("POST", "/futures/modify-stop-order", data=data)

    # --- جدید: Cancel Futures Order ---
    def cancel_futures_order(self, market: str, market_type: str, order_id: int):
        """
        لغو یک سفارش Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param order_id: شناسه سفارش
        """
        data = {
            "market": market,
            "market_type": market_type,
            "order_id": order_id
        }
        return self._request("POST", "/futures/cancel-order", data=data)

    # --- جدید: Cancel Futures Stop Order ---
    def cancel_futures_stop_order(self, market: str, market_type: str, stop_id: int):
        """
        لغو یک سفارش Stop در Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param stop_id: شناسه سفارش Stop
        """
        data = {
            "market": market,
            "market_type": market_type,
            "stop_id": stop_id
        }
        return self._request("POST", "/futures/cancel-stop-order", data=data)


    # --- جدید: Cancel All Futures Orders ---
    def cancel_all_futures_orders(self, market: str, market_type: str, side: str = None):
        """
        لغو تمام سفارشات در یک مارکت Futures
        :param market: نام مارکت مثل "CETUSDT"
        :param market_type: نوع مارکت ("FUTURES")
        :param side: نوع سفارش ("buy" یا "sell") (اختیاری)
        """
        data = {
            "market": market,
            "market_type": market_type
        }
        if side is not None:
            data["side"] = side

        return self._request("POST", "/futures/cancel-all-order", data=data)
