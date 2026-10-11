from django.contrib import admin

from apps.market.models import Floorsheet


@admin.register(Floorsheet)
class FloorsheetAdmin(admin.ModelAdmin):
    list_display = ("company", "date", "contract_no", "buyer_broker", "seller_broker", "qty", "rate")
    list_filter = ("date",)
    search_fields = ("contract_no", "buyer_broker", "seller_broker")
