from django.db import models
from django.utils import timezone

from django.db import models
from numpy import power


class OrderBook(models.Model):
    broker = models.CharField(max_length=100, default='coinex')
    market = models.CharField(max_length=100)
    side = models.CharField(max_length=100, choices=[('seller', 'seller'), ('buyer', 'buyer')])
    price = models.FloatField()
    volume = models.FloatField()
    volume_24h = models.FloatField()
    cum_volume_24h = models.FloatField()
    log_cum_volume_24h = models.FloatField()
    weight = models.FloatField()
    distance = models.FloatField()
    timestamp = models.IntegerField()
    create_at = models.DateTimeField(auto_now_add=True)

class AnalizeDepth(models.Model):
    # --- اطلاعات کلی ---
    broker = models.CharField(
        max_length=100, 
        default="coinex",
        verbose_name="کارگزار",
        help_text="نام صرافی یا بروکر"
    )
    market = models.CharField(
        max_length=100,
        verbose_name="مارکت",
        help_text="مثلاً BTC/USDT"
    )
    fee = models.FloatField(
        verbose_name="کارمزد",
        help_text="کارمزد کل معامله به درصد"
    )
    create_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ ایجاد"
    )
    update_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ بروزسانی"
    )

    # --- تحلیل تکنیکال ---
    support_main = models.FloatField(verbose_name="حمایت اصلی")
    support_second = models.FloatField(verbose_name="حمایت دوم")
    resistance_main = models.FloatField(verbose_name="مقاومت اصلی")
    resistance_second = models.FloatField(verbose_name="مقاومت دوم")
    last_price = models.FloatField(verbose_name="آخرین قیمت")
    sel_power_shock = models.FloatField(verbose_name="قدرت شوک فروش")
    sel_power_cum_shock = models.FloatField(verbose_name="قدرت تجمیعی شوک فروش")
    buy_power_shock = models.FloatField(verbose_name="قدرت شوک خرید")
    buy_power_cum_shock = models.FloatField(verbose_name="قدرت تجمیعی شوک خرید")

    # --- خرید ---

    buy = models.BooleanField(verbose_name="خرید",default=False)
    open_buy = models.BooleanField(verbose_name="سیگنال خرید فعال؟")
    buy_price = models.FloatField(verbose_name="قیمت خرید")
    min_buy_target = models.FloatField(verbose_name="حداقل تارگت خرید")
    buy_target = models.FloatField(verbose_name="تارگت اصلی خرید")
    buy_stop_loss = models.FloatField(verbose_name="حد ضرر خرید")
    buy_rate_profit = models.FloatField(verbose_name="نرخ سود احتمالی خرید")
    buy_rr = models.FloatField(verbose_name="نسب سود به ریسک خرید")

    # --- فروش ---
    sell = models.BooleanField(verbose_name="فروش",default=False)
    open_sell = models.BooleanField(verbose_name="سیگنال فروش فعال؟")
    sell_price = models.FloatField(verbose_name="قیمت فروش")
    min_sell_target = models.FloatField(verbose_name="حداقل تارگت فروش")
    sell_target = models.FloatField(verbose_name="تارگت اصلی فروش")
    sell_stop_loss = models.FloatField(verbose_name="حد ضرر فروش")
    sell_rate_profit = models.FloatField(verbose_name="نرخ سود احتمالی فروش")
    sell_rr = models.FloatField(verbose_name="نسب سود به ریسک فروش")
    class Meta:
        verbose_name = "تحلیل عمق بازار"
        verbose_name_plural = "تحلیل‌های عمق بازار"
        ordering = ("-create_at",)

    def __str__(self):
        return f"{self.market} | {self.broker} | {self.create_at.strftime('%Y-%m-%d %H:%M')}"



class MarketTicker(models.Model):
    broker = models.CharField(max_length=100, default='coinex')
    market = models.CharField(max_length=100)
    close = models.FloatField()
    high = models.FloatField()
    index_price = models.FloatField()
    last = models.FloatField() 
    low = models.FloatField() 
    mark_price = models.FloatField() 
    open = models.FloatField() 
    period = models.IntegerField(default=86400) 
    value = models.FloatField() 
    volume = models.FloatField() 
    create_at = models.DateTimeField(auto_now_add=True)

class MarketStatus(models.Model):
    broker = models.CharField(max_length=100, default='coinex')
    market = models.CharField(max_length=100)
    is_market_available = models.BooleanField(default=True)
    maker_fee_rate = models.FloatField()
    taker_fee_rate = models.FloatField()
    min_amount = models.FloatField()
    create_at = models.DateTimeField(auto_now_add=True)

    

class FundingRate(models.Model):
    broker = models.CharField(max_length=100, default='coinex')
    market = models.CharField(max_length=100)
    mark_price = models.FloatField()
    latest_funding_rate = models.FloatField()
    latest_funding_time = models.IntegerField()
    next_funding_rate = models.FloatField()
    max_funding_rate = models.FloatField()
    min_funding_rate = models.FloatField()
    next_funding_time = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.broker} {self.market} {self.created_at}"


class Order(models.Model):
    broker = models.CharField(max_length=100, default='coinex')
    market = models.CharField(max_length=100)
    price = models.FloatField()
    stop_loss = models.FloatField()
    target = models.FloatField()
    amount = models.FloatField()
    side = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    client_id = models.CharField(max_length=100)
    order_id = models.IntegerField(default=0)
    fee = models.FloatField()
    realized_pnl = models.FloatField()
    status = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.broker} {self.market} {self.created_at} {self.side}"