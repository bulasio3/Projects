from datetime import time
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_hospitalsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_duration', models.PositiveSmallIntegerField(choices=[(15, '15 minutes'), (30, '30 minutes'), (45, '45 minutes'), (60, '60 minutes')], default=30)),
                ('monday', models.BooleanField(default=True)),
                ('tuesday', models.BooleanField(default=True)),
                ('wednesday', models.BooleanField(default=True)),
                ('thursday', models.BooleanField(default=True)),
                ('friday', models.BooleanField(default=True)),
                ('saturday', models.BooleanField(default=False)),
                ('sunday', models.BooleanField(default=False)),
                ('opening_time', models.TimeField(default=time(8, 0))),
                ('closing_time', models.TimeField(default=time(17, 0))),
                ('max_appointments_per_doctor', models.PositiveSmallIntegerField(default=12)),
                ('online_booking_enabled', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
