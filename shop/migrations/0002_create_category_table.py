from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS "shop_category" (
                    "id" bigserial PRIMARY KEY,
                    "name" varchar(200) NOT NULL,
                    "description" text NOT NULL,
                    "image" varchar(100) NOT NULL,
                    "is_active" boolean NOT NULL DEFAULT true,
                    "created_at" timestamp with time zone NOT NULL DEFAULT now()
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS \"shop_category\";",
        ),
    ]
