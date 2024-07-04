#!/bin/bash

# Navegue até o diretório correto se necessário
# cd main  # Descomente se necessário e substitua 'main' pelo diretório correto

# Inicie o aplicativo Flask com gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
