from django.db import models


class Price(models.Model):
    pk = models.CompositePrimaryKey("company", "date")
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="prices",
    )
    date = models.DateField()
    open = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    close = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.BigIntegerField()
    turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    trades = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "prices"
        indexes = [
            models.Index(fields=["company", "-date"]),
        ]

    def __str__(self):
        return f"{self.company_id} {self.date}"


class Floorsheet(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="trades",
    )
    date = models.DateField()
    contract_no = models.CharField(max_length=64, blank=True)
    buyer_broker = models.CharField(max_length=10)
    seller_broker = models.CharField(max_length=10)
    qty = models.IntegerField()
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name_plural = "floorsheets"
        indexes = [
            models.Index(fields=["company", "date"]),
            models.Index(fields=["company", "date", "buyer_broker"]),
            models.Index(fields=["company", "date", "seller_broker"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "date", "contract_no"],
                condition=~models.Q(contract_no=""),
                name="unique_floorsheet_contract",
            ),
        ]

    def __str__(self):
        label = self.contract_no or "no-contract"
        return f"{self.company_id} {self.date} {label}"
