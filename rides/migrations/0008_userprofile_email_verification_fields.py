from django.db import migrations, models


def add_missing_email_verification_columns(apps, schema_editor):
    """Add email verification columns only when they are missing in the DB."""
    user_profile_model = apps.get_model("rides", "UserProfile")
    table_name = user_profile_model._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if "email_verified" not in existing_columns:
        email_verified_field = models.BooleanField(default=False)
        email_verified_field.set_attributes_from_name("email_verified")
        schema_editor.add_field(user_profile_model, email_verified_field)

    if "email_verified_at" not in existing_columns:
        email_verified_at_field = models.DateTimeField(null=True, blank=True)
        email_verified_at_field.set_attributes_from_name("email_verified_at")
        schema_editor.add_field(user_profile_model, email_verified_at_field)


class Migration(migrations.Migration):

    dependencies = [
        ("rides", "0007_ride_vehicle_number_alter_userprofile_phone_number"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_missing_email_verification_columns,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="userprofile",
                    name="email_verified",
                    field=models.BooleanField(
                        default=False,
                        help_text="Whether email has been verified",
                    ),
                ),
                migrations.AddField(
                    model_name="userprofile",
                    name="email_verified_at",
                    field=models.DateTimeField(
                        blank=True,
                        null=True,
                        help_text="When email was successfully verified",
                    ),
                ),
            ],
        ),
    ]
