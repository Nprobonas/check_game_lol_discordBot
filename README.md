git clone du projet ...
cd dossier racine
# Initialiser l'environnement virtuel python avec :
python -m venv venv 
# puis :
source venv/bin/activate
# Installation des dépendances
pip install -r requirements.txt
# créer un .env afin de stocker les clés API et Token DISCORD avec la forme suivante : 
DISCORD_TOKEN="ton_token"
RIOT_API_KEY="ta_cle_riot"

# Execute le bot dans ton terminal en lançant le fichier python
python main.py
