#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f brasil_soberano.db ]; then
  echo "Criando banco de dados..."
  python3 database.py
fi

# Gerar BS_SECRET persistente se não existir
SECRET_FILE=".bs_secret"
if [ ! -f "$SECRET_FILE" ]; then
  python3 -c "import secrets; print(secrets.token_hex(32))" > "$SECRET_FILE"
  chmod 600 "$SECRET_FILE"
  echo "🔑 BS_SECRET gerado e salvo em $SECRET_FILE"
fi
export BS_SECRET=$(cat "$SECRET_FILE")

echo "🇧🇷 Brasil Soberano — produção com Gunicorn"
echo "🔒 Modo seguro: headers, rate limit, audit log, CSRF"

# Gunicorn: 2 workers, bind localhost:5000
exec gunicorn \
  --workers 2 \
  --bind 127.0.0.1:5000 \
  --timeout 60 \
  --access-logfile /tmp/bs-access.log \
  --error-logfile /tmp/brasil-soberano.log \
  --log-level info \
  --forwarded-allow-ips '*' \
  app:app
