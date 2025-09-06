from django import forms
from .models import AnalizeDepth
from decimal import Decimal

class FloatTextInput(forms.TextInput):
    def format_value(self, value):
        if value is None:
            return ""
        try:
            # تبدیل به Decimal برای نمایش کامل و دقیق
            return str(Decimal(str(value)))
        except (ValueError, TypeError):
            return str(value)



class AnalizeDepthForm(forms.ModelForm):
    class Meta:
        model = AnalizeDepth
        fields = "__all__"
        widgets = {
            "buy_price": FloatTextInput(),
            "buy_target": FloatTextInput(),
            "buy_stop_loss": FloatTextInput(),
            "min_buy_target": FloatTextInput(),
            "sell_price": FloatTextInput(),
            "sell_target": FloatTextInput(),
            "sell_stop_loss": FloatTextInput(),
            "min_sell_target": FloatTextInput(),
            "last_price": FloatTextInput(),
            "fee": FloatTextInput(),
            "support_main": FloatTextInput(),
            "support_second": FloatTextInput(),
            "resistance_main": FloatTextInput(),
            "resistance_second": FloatTextInput(),
        }