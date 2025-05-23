# Generated by Django 5.1 on 2024-10-14 15:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Accounts', '0008_saldototaleinvestimenti'),
        ('Users', '0006_remove_utente_famiglia_utente_famiglia'),
    ]

    operations = [
        migrations.CreateModel(
            name='PosizioneAperta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saldo_totale', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('saldo_investito', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('pmc', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('differenza', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('ticker', models.CharField(max_length=10)),
                ('nome_azienda', models.CharField(max_length=20)),
                ('conto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Accounts.conto')),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Users.utente')),
            ],
        ),
    ]
