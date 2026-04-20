#!/bin/bash
pkg update -y
pkg install python -y
pip install numpy
echo "Instalação concluída. Execute: python cnc_guide_cli.py"
