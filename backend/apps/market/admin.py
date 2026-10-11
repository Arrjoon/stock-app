from django.contrib import admin

from apps.market.models import Floorsheet, PriceRow


@admin.register(PriceRow)
class PriceRowAdmin(admin.ModelAdmin):
    list_display = ("company", "date", "open", "high", "low", "close", "volume", "turnover", "trades")
    list_filter = ("date",)
    search_fields = ("company__symbol", "company__name")
    ordering = ("-date", "company")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Floorsheet)
class FloorsheetAdmin(admin.ModelAdmin):
    list_display = ("company", "date", "contract_no", "buyer_broker", "seller_broker", "qty", "rate")
    list_filter = ("date",)
    search_fields = ("contract_no", "buyer_broker", "seller_broker")
