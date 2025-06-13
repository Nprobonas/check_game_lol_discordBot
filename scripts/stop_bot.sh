#!/bin/bash

# Script d'arrêt du bot à 02h00 du matin

SCREEN=/opt/sbin/screen
$SCREEN -S discord_bot -X quit
