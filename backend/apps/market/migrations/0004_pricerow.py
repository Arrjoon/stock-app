import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("market", "0003_price_admin_view"),
    ]

    operations = [
        migrations.CreateModel(
            name="PriceRow",
            fields=[
                ("id", models.CharField(max_length=40, primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("open", models.DecimalField(decimal_places=2, max_digits=12)),
                ("high", models.DecimalField(decimal_places=2, max_digits=12)),
                ("low", models.DecimalField(decimal_places=2, max_digits=12)),
                ("close", models.DecimalField(decimal_places=2, max_digits=12)),
                ("volume", models.BigIntegerField()),
                ("turnover", models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ("trades", models.IntegerField(blank=True, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        db_column="company_id",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "price",
                "verbose_name_plural": "prices",
                "db_table": "market_price_admin",
                "ordering": ["-date", "company"],
                "managed": False,
            },
        ),
    ]
