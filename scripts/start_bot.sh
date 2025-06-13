#!/bin/bash

# Scripts de démarrage du bot à 7h00 du matin

# Chemin absolus 
WORKDIR=/volume1/NPR_main_dir/dev_project/python/discord_bot
VENV=$WORKDIR/venv
SCREEN=/opt/sbin/screen # -> version Entware
PYTHON=$VENV/bin/python # Venv du projhet python

cd $WORKDIR/check_game_lol_discordBot
.$VENV/bin/activate
$SCREEN -dmS discord_bot $PYTHON main.py