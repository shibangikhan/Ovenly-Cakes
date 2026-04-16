from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_create_product_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='products', to='shop.category'),
        ),
    ]
