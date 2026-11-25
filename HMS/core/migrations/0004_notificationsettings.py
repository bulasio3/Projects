from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_appointmentconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_reminders', models.BooleanField(default=True)),
                ('payment_alerts', models.BooleanField(default=True)),
                ('lab_result_alerts', models.BooleanField(default=True)),
                ('low_stock_alerts', models.BooleanField(default=True)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=False)),
                ('reminder_hours_before', models.PositiveSmallIntegerField(choices=[(1, '1 hour before'), (2, '2 hours before'), (24, '24 hours before'), (48, '48 hours before')], default=24)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
