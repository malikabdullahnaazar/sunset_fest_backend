# Generated by Django 5.2 on 2025-04-21 14:55

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0012_remove_room_available_rooms'),
    ]

    operations = [
        migrations.AddField(
            model_name='addon',
            name='has_time_slots',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='addon',
            name='min_persons',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.CreateModel(
            name='AddOnTimeSlot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('total_capacity', models.PositiveIntegerField(default=0)),
                ('available_capacity', models.PositiveIntegerField(default=0)),
                ('price_override', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('add_on', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_slots', to='events.addon')),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='BookingAddOn',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('add_on', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.addon')),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_addons', to='events.booking')),
                ('time_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events.addontimeslot')),
            ],
        ),
    ]
