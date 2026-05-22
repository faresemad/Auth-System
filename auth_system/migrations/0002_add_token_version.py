from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_system", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="twofactor",
            name="token_version",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Increment to invalidate all existing JWT tokens for this user.",
            ),
        ),
    ]
