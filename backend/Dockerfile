FROM python:3.10-slim

WORKDIR /app

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Exposition du port
EXPOSE 5000

# Commande de lancement
CMD ["python", "app.py"]
