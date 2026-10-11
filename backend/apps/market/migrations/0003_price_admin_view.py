from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0002_price_hypertable"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW market_price_admin AS
            SELECT
                company_id::text || '-' || to_char(date, 'YYYYMMDD') AS id,
                company_id,
                date,
                open,
                high,
                low,
                close,
                volume,
                turnover,
                trades
            FROM market_price;
            """,
            reverse_sql="DROP VIEW IF EXISTS market_price_admin;",
        ),
    ]
