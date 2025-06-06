# Generated by Django 5.2 on 2025-04-21 18:34

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0014_remove_addon_available_tickets_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomHold',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='tickethold',
            name='room_holds',
            field=models.ManyToManyField(blank=True, to='events.roomhold'),
        ),
        migrations.AddIndex(
            model_name='roomhold',
            index=models.Index(fields=['room', 'expires_at'], name='events_room_room_id_33e9d6_idx'),
        ),
    ]
