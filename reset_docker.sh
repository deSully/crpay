#!/bin/bash

# Nom du projet (modifie si besoin)
PROJECT_NAME="crpay"

# Arrêter et supprimer les containers, les réseaux et les volumes nommés dans le fichier docker-compose
echo "🛑 Arrêt des containers..."
docker-compose down

# Identifier le volume associé à la base Postgres
echo "🔍 Recherche du volume associé à Postgres..."
VOLUME_NAME=$(docker volume ls --format "{{.Name}}" | grep "${PROJECT_NAME}_postgres_data")

if [ -n "$VOLUME_NAME" ]; then
    echo "🗑️ Suppression du volume : $VOLUME_NAME"
    docker volume rm "$VOLUME_NAME"
else
    echo "✅ Aucun volume Postgres spécifique trouvé pour ce projet."
fi

# Nettoyage général (containers arrêtés, images inutilisées, réseaux non utilisés)
echo "🧹 Nettoyage Docker..."
docker system prune -f

# Rebuild et relance du projet
echo "🚀 Reconstruction et démarrage..."
docker-compose up --build

echo "✅ Docker reset terminé avec succès."

