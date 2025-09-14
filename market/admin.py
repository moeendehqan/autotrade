# market/admin.py
from django.contrib import admin
from .models import AnalizeDepth, MarketTicker, MarketStatus, FundingRate, Order, OrderBook
from .forms import AnalizeDepthForm
@admin.register(AnalizeDepth)
class AnalizeDepthAdmin(admin.ModelAdmin):
    form = AnalizeDepthForm
    # نمایش اصلی در لیست
    list_display = (
        "id", "market", 
        "buy", "sell","update_at", "buy_price", "buy_target", "buy_stop_loss",
        "sell_price", "sell_target", "sell_stop_loss",
        "last_price", "fee", 
    )
    
    # قابلیت فیلتر
    list_filter = ("broker", "market", "open_buy", "open_sell")

    # قابلیت سرچ (روی فیلدهای متنی)
    search_fields = ("broker", "market")

    # مرتب‌سازی
    ordering = ("-buy","-sell", "-update_at")

    # گروه‌بندی فیلدها برای فرم admin
    fieldsets = (
        ("اطلاعات کلی", {
            "fields": ("broker", "market", "fee", "update_at", "create_at")
        }),
        ("خرید (Buy)", {
            "fields": (
                "buy","open_buy",
                "buy_price", "buy_target", "buy_stop_loss", 
                "buy_power_shock", "buy_power_cum_shock",
                "buy_rate_profit","buy_rr",
                "min_buy_target", 
            )
        }),
        ("فروش (Sell)", {
            "fields": (
                "sell","open_sell",
                "sell_price", "sell_target", "sell_stop_loss", 
                "sel_power_shock", "sel_power_cum_shock",
                "sell_rate_profit", "sell_rr",
                "min_sell_target", 
            )
        }),
        ("تحلیل تکنیکال", {
            "fields": (
                "support_main", "support_second",
                "resistance_main", "resistance_second",
                "last_price",
            )
        }),
    )
    readonly_fields = ["update_at","create_at"]


    # برای خوانایی بهتر
    list_per_page = 40

    def format_number(self, value):
        if value is None:
            return "-"
        return ('%f' % value).rstrip("0").rstrip(".")

@admin.register(MarketTicker)
class MarketTickerAdmin(admin.ModelAdmin):
    list_display = (
        "broker", "market", "open", "close", "high", "low",
        "last", "mark_price", "index_price", "value", "volume",
        "period", "create_at"
    )
    list_filter = ("broker", "market", "create_at")
    search_fields = ("broker", "market")
    ordering = ("-create_at",)
    readonly_fields = ("create_at",)


@admin.register(MarketStatus)
class MarketStatusAdmin(admin.ModelAdmin):
    list_display = (
        "broker", "market", "is_market_available",
        "maker_fee_rate", "taker_fee_rate", "min_amount", "create_at"
    )
    list_filter = ("broker", "market", "is_market_available", "create_at")
    search_fields = ("broker", "market")
    ordering = ("-create_at",)
    readonly_fields = ("create_at",)


@admin.register(FundingRate)
class FundingRateAdmin(admin.ModelAdmin):
    list_display = (
        "broker", "market", "mark_price",
        "latest_funding_rate", "latest_funding_time",
        "next_funding_rate", "next_funding_time",
        "max_funding_rate", "min_funding_rate", "created_at"
    )
    list_filter = ("broker", "market", "created_at")
    search_fields = ("broker", "market")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

@admin.register(OrderBook)
class OrderBookAdmin(admin.ModelAdmin):
    list_display = (
        "broker", "market", "side", "price", "volume", "volume_24h", "cum_volume_24h", "log_cum_volume_24h", "weight", "distance", "timestamp", "create_at"
    )
    list_filter = ("broker", "market", "side", "timestamp", "create_at")
    search_fields = ("broker", "market", "side", "timestamp", "create_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "broker", "market", "price", "stop_loss", "target", "amount", "side", "created_at", "update_at", "client_id", "order_id", "fee", "realized_pnl", "status"
    )
    list_filter = ("broker", "market", "created_at", "update_at", "status")
    search_fields = ("broker", "market", "client_id", "order_id")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "update_at")