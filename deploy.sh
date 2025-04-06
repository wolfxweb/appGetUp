#!/bin/bash

echo "🔄 Atualizando projeto"
cd /opt
rm -rf /opt/appGetUp
git clone https://github.com/wolfxweb/appGetUp.git /opt/appGetUp
cd /opt/appGetUp

echo "🐍 Criando ambiente virtual"
rm -rf venv
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando dependências"
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages

echo "🔁 Reiniciando serviço"
systemctl daemon-reload
systemctl restart appgetup
systemctl status appgetup
