# Generated by Django 3.1.1 on 2020-10-11 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('corrSMS', '0008_auto_20201011_1825'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='corrSMS.smstocorrlinks')),
            ],
        ),
        migrations.RemoveField(
            model_name='customer',
            name='sms_Customer_2',
        ),
        migrations.DeleteModel(
            name='SMSCustomer2',
        ),
    ]
