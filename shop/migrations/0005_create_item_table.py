from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_add_product_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(upload_to='items/')),
                ('price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='items', to='shop.category')),
            ],
        ),
    ]
