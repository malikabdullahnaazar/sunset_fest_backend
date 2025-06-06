# Generated by Django 5.2 on 2025-04-17 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_remove_feature_pricing_plans_pricingplan_feature'),
    ]

    operations = [
        migrations.AddField(
            model_name='accommodation',
            name='available_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='accommodation',
            name='total_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='addon',
            name='available_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='addon',
            name='total_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='pricingplan',
            name='available_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='pricingplan',
            name='total_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='room',
            name='available_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='room',
            name='total_tickets',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
