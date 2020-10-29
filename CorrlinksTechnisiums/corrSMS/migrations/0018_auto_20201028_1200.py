# Generated by Django 3.1.1 on 2020-10-28 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corrSMS', '0017_systemtocorrlinks'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerAndSmsCustomer',
            fields=[
            ],
            options={
                'verbose_name': 'Customer',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('corrSMS.customer',),
        ),
        migrations.AlterModelOptions(
            name='systemtocorrlinks',
            options={'verbose_name': 'System To Corrlinks', 'verbose_name_plural': 'System To Corrlinks'},
        ),
        migrations.AddField(
            model_name='customer',
            name='image_count',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]