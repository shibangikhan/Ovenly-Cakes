from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_create_item_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
    ]
