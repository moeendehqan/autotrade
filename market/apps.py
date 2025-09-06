from django.apps import AppConfig
from .utiles import update_funding_rate, update_market_status, update_market_ticker, update_futures_depth, update_order
import threading


class MarketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market'
    def ready(self):
        tasks = [update_funding_rate, update_market_status, update_market_ticker, update_futures_depth, update_order]
        for i in tasks:
            thread = threading.Thread(target=i, daemon=True)
            thread.start()

        return super().ready()
