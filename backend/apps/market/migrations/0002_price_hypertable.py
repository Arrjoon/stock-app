from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE EXTENSION IF NOT EXISTS timescaledb;
            SELECT create_hypertable(
                'market_price',
                'date',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
