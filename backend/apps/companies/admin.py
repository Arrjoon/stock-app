from django.contrib import admin

from apps.companies.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "sector", "active")
    list_filter = ("active", "sector")
    search_fields = ("symbol", "name")
