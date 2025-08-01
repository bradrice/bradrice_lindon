# Generated by Django 5.2.4 on 2025-08-01 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('figures', '0005_alter_mypagegalleryimage_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='figuredetail',
            options={'ordering': ['weight', 'title']},
        ),
        migrations.RemoveField(
            model_name='figuredetail',
            name='gallery_number',
        ),
        migrations.AddField(
            model_name='figuredetail',
            name='weight',
            field=models.IntegerField(default=0, help_text='Lower number means higher priority in sorting.'),
        ),
    ]
