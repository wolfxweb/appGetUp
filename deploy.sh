#!/bin/bash

set -e

echo "🔄 Atualizando projeto"
cd /opt
rm -rf /opt/appGetUp
git clone https://github.com/wolfxweb/appGetUp.git /opt/appGetUp
cd /opt/appGetUp

echo "🐍 Criando ambiente virtual"
apt-get update -qq
apt-get install -y python3-venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando dependências (sem cache)"
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "🗄️ Rodando migrações do banco de dados"
python3 migrate_db.py
python3 migration_estimativas.py

echo "🔁 Reiniciando serviço"
systemctl daemon-reload
systemctl restart appgetup
systemctl status appgetup
