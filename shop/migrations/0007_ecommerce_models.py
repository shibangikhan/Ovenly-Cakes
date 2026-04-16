from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_remove_product_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='cart', to='shop.user')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash on Delivery'), ('online', 'Online Payment')], max_length=10)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('unpaid', 'Unpaid'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('order_status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('payment_reference', models.CharField(blank=True, max_length=255, null=True)),
                ('payment_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='orders', to='shop.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('product', 'Product'), ('item', 'Item')], max_length=10)),
                ('product_id', models.PositiveIntegerField()),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cart', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='items', to='shop.cart')),
            ],
            options={
                'ordering': ['created_at'],
                'unique_together': {('cart', 'product_type', 'product_id')},
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('product', 'Product'), ('item', 'Item')], max_length=10)),
                ('product_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='items', to='shop.order')),
            ],
        ),
    ]
