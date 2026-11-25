from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_notificationsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(choices=[('UGX', 'UGX — Ugandan Shilling'), ('USD', 'USD — US Dollar'), ('KES', 'KES — Kenyan Shilling'), ('TZS', 'TZS — Tanzanian Shilling'), ('RWF', 'RWF — Rwandan Franc'), ('EUR', 'EUR — Euro'), ('GBP', 'GBP — British Pound')], default='UGX', max_length=3)),
                ('date_format', models.CharField(choices=[('d/m/Y', 'DD/MM/YYYY'), ('Y-m-d', 'YYYY-MM-DD'), ('m/d/Y', 'MM/DD/YYYY')], default='d/m/Y', max_length=10)),
                ('time_zone', models.CharField(choices=[('Africa/Kampala', 'Africa/Kampala — East Africa Time'), ('Africa/Nairobi', 'Africa/Nairobi — East Africa Time'), ('Africa/Dar_es_Salaam', 'Africa/Dar es Salaam — East Africa Time'), ('Africa/Kigali', 'Africa/Kigali — Central Africa Time'), ('UTC', 'UTC — Coordinated Universal Time')], default='Africa/Kampala', max_length=50)),
                ('time_format', models.CharField(choices=[('24', '24-hour clock'), ('12', '12-hour clock')], default='24', max_length=2)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
