from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0045_auto_20180917_0645'),
    ]

    operations = [
        migrations.AlterField(
            field=models.CharField(
                help_text='The name of the document type.', max_length=96,
                unique=True, verbose_name='Label'
            ), model_name='documenttype', name='label',
        ),
    ]
