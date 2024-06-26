# Generated by Django 5.0.6 on 2024-06-26 08:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0001_initial'),
        ('pipeline', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pipeline',
            name='image',
        ),
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmbeddingConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('embedding', models.CharField(default='embed-multilingual-v3.0', max_length=255)),
                ('embedding_size', models.IntegerField(default=1024)),
                ('local_embedding', models.BooleanField(default=False)),
                ('pipeline', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='embedding_config', to='pipeline.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='ModelConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(default='command-r', max_length=255)),
                ('local_model', models.BooleanField(default=False)),
                ('temperature', models.FloatField(default=0.2)),
                ('chunk_size', models.IntegerField(default=512)),
                ('pipeline', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='model_config', to='pipeline.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='PipelineConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rerank', models.BooleanField(default=False)),
                ('top_k', models.IntegerField(default=0)),
                ('hybrid_search', models.BooleanField(default=False)),
                ('use_agent', models.BooleanField(default=False)),
                ('pipeline_type', models.CharField(choices=[('simple', 'Simple'), ('advanced', 'Advanced')], default='simple', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pipeline', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='config', to='pipeline.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='PipelineStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruction', models.TextField()),
                ('variable', models.CharField(max_length=255)),
                ('order', models.IntegerField()),
                ('knowledge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge.knowledge')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='pipeline.pipeline')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
