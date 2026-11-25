from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HospitalSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hospital_name', models.CharField(default='MediCare Hospital', max_length=200)),
                ('logo_url', models.URLField(blank=True)),
                ('address', models.TextField(blank=True)),
                ('telephone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('operating_hours', models.CharField(default='Open 24 hours', max_length=120)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
