#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f brasil_soberano.db ]; then
  echo "Criando banco de dados..."
  python3 database.py
fi
echo "🇧🇷 Brasil Soberano rodando em http://localhost:5000"
exec python3 app.py
