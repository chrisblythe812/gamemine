from django.db import connection, transaction


# Django doesn't support path change of ImageField so using raw sql
def migrate_media_field_forwards(model, image_field):
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE %s SET %s = SUBSTR(%s, 7) WHERE %s LIKE 'media%%%%'" %
        (model._meta.db_table, image_field, image_field, image_field)
    )
    transaction.commit_unless_managed()


def migrate_media_field_backwards(model, image_field):
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE %s SET %s ='media/' ||  %s WHERE %s != ''" %
        (model._meta.db_table, image_field, image_field, image_field)
    )
    transaction.commit_unless_managed()
