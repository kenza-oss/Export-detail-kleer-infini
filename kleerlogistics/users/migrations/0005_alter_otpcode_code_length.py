from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_userdocument_options_user_commission_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpcode',
            name='code',
            field=models.CharField(max_length=64),
        ),
    ]


