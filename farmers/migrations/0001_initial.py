# Generated by Django 5.0.6 on 2025-03-16 15:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Farmer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('aadhar_id', models.CharField(max_length=12, unique=True)),
                ('farm_area', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated_at', models.DateTimeField(auto_now=True)),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='farmers', to='farmers.block')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='farmers_created', to=settings.AUTH_USER_MODEL)),
                ('last_updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='farmers_updated', to=settings.AUTH_USER_MODEL)),
                ('surveyor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='farmers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['surveyor', 'block'], name='farmers_far_surveyo_fb775a_idx'), models.Index(fields=['created_by'], name='farmers_far_created_1423de_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated_at', models.DateTimeField(auto_now=True)),
                ('block', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_users', to='farmers.block')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_profiles', to=settings.AUTH_USER_MODEL)),
                ('last_updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_profiles', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['block', 'created_by'], name='farmers_use_block_i_79ef35_idx')],
            },
        ),
    ]
