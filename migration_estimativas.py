"""
Migração: adiciona colunas de estimativa ao users
Execute dentro do container: docker compose exec web python migration_estimativas.py
"""
import sqlite3, os, shutil, datetime

db_path = os.path.join('app', 'database', 'app.db')
backup = db_path + '.bak_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy(db_path, backup)
print(f"Backup criado: {backup}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
cols = [c[1] for c in cursor.fetchall()]

for col_name, col_type in [
    ("production_hours", "REAL"),
    ("estimated_loss_percentage", "REAL"),
    ("has_product_sheet", "TEXT"),
]:
    if col_name not in cols:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        print(f"Adicionado: {col_name}")
    else:
        print(f"Já existe: {col_name}")

conn.commit()
conn.close()
print("Migração concluída!")
