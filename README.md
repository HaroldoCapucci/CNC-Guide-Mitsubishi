# Haroldo Capucci CNC Guide for Mitsubishi M800/M80

**Versão:** 1.0
**Autores:** Haroldo Capucci & Arnaldo Santiago
**Licença:** MIT

Ferramenta completa para geração de códigos G para controles Mitsubishi M800/M80, com suporte a **torno** (G71, G77, G78) e **fresadora** (G12.1, G81, G83, G34, G05.1). Possui versão desktop (Tkinter) e versão CLI para Termux (Android).

## Funcionalidades
- Interface gráfica com abas Torno / Fresadora
- Simulação 2D via matplotlib
- IA por regras (sugestão de parâmetros por material e operação)
- Geração de código G otimizado
- Barra de status com créditos para **Arnaldo Santiago**
- Versão CLI para celular (Termux)

## Instalação
### Desktop (Windows/Linux)
```bash
cd desktop
pip install -r requirements.txt
python cnc_guide.py
```

### Termux (Android)
```bash
pkg install python
cd termux
bash install.sh
python cnc_guide_cli.py
```
