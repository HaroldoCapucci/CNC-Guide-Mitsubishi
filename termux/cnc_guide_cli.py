#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haroldo Capucci CNC Guide CLI for Termux (Android)
Co-autor: Arnaldo Santiago
"""

import os

MATERIAIS = {
    "1": {"nome": "Aço 1020", "vc": 80, "fz": 0.05, "doc": 1.5},
    "2": {"nome": "Alumínio", "vc": 150, "fz": 0.10, "doc": 2.0},
    "3": {"nome": "Inox 304", "vc": 60, "fz": 0.03, "doc": 1.0},
    "4": {"nome": "Plástico", "vc": 200, "fz": 0.15, "doc": 3.0},
}

OPERACOES_TORNO = {"1": "G71 - Desbaste", "2": "G77 - Faceamento", "3": "G78 - Rosqueamento"}
OPERACOES_FRESA = {"1": "G12.1 - Polar", "2": "G81 - Furação", "3": "G83 - Peck", "4": "G34 - Rosq rígido", "5": "G05.1 - High speed"}

def limpar_tela(): os.system('clear')
def cabecalho():
    print("\033[1;34m" + "="*50)
    print("   CNC GUIDE - MITSUBISHI M800/M80")
    print("   Co-autor: Arnaldo Santiago")
    print("="*50 + "\033[0m")

def sugerir_parametros(material_key, diametro=10):
    mat = MATERIAIS[material_key]
    rpm = int(mat["vc"] * 1000 / (3.1416 * diametro))
    feed = int(rpm * mat["fz"] * 2)
    return rpm, feed, mat["doc"]

def gerar_gcode_torno(op_key, mat_key, diam, comp, prof):
    mat = MATERIAIS[mat_key]
    rpm, feed, _ = sugerir_parametros(mat_key, diam)
    gcode = f"(Gerado por CNC Guide - Haroldo Capucci & Arnaldo Santiago)\n"
    gcode += f"(Material: {mat['nome']})\nN10 G21 G90 G95\nN20 M03 S{rpm}\nN30 G00 X{diam+2} Z2\n"
    if op_key == "1":
        gcode += f"N40 G71 U{prof} R1\nN50 G71 P60 Q90 U0.5 W0.1 F{feed}\nN60 G00 X0\nN70 G01 Z-{comp}\nN80 X{diam}\nN90 G00 Z2\nN100 G70 P60 Q90\n"
    elif op_key == "2":
        gcode += f"N40 G77 X0 Z-{comp} I{prof} F{feed}\n"
    elif op_key == "3":
        passo = 1.5
        gcode += f"N40 G78 X0 Z-{comp} I{passo} F{passo*feed/10}\n"
    gcode += f"N110 G00 X{diam+10}\nN120 M05\nN130 M30\n"
    return gcode

def gerar_gcode_fresa(op_key, mat_key, larg, alt, prof):
    mat = MATERIAIS[mat_key]
    rpm, feed, _ = sugerir_parametros(mat_key, 10)
    gcode = f"(Gerado por CNC Guide - Haroldo Capucci & Arnaldo Santiago)\n"
    gcode += f"(Material: {mat['nome']})\nN10 G21 G90 G94\nN20 M03 S{rpm}\nN30 G00 X{larg/2-20} Y{alt/2-20} Z5\n"
    if op_key == "1":
        gcode += f"N40 G12.1\nN50 G01 X0 Y0 F{feed}\nN60 G03 X20 Y0 R10\nN70 G02 X0 Y0 R10\nN80 G13.1\n"
    elif op_key == "2":
        gcode += f"N40 G81 X{larg/2} Y{alt/2} Z-{prof} R2 F{feed}\nN50 G80\n"
    elif op_key == "3":
        gcode += f"N40 G83 X{larg/2} Y{alt/2} Z-{prof} R2 Q2 F{feed}\nN50 G80\n"
    elif op_key == "4":
        gcode += f"N40 G34 X{larg/2} Y{alt/2} Z-{prof} K1.5 F{feed}\n"
    elif op_key == "5":
        gcode += f"N40 G05.1 Q1\nN50 G01 X{larg/2+30} Y{alt/2} F{feed*2}\nN60 G05.1 Q0\n"
    gcode += f"N70 G00 Z10\nN80 M05\nN90 M30\n"
    return gcode

def menu_torno():
    print("\n\033[1;33m--- TORNO ---\033[0m")
    for k, v in OPERACOES_TORNO.items(): print(f"{k}. {v}")
    op = input("Escolha: ")
    if op not in OPERACOES_TORNO: return
    print("Materiais:") 
    for k, v in MATERIAIS.items(): print(f"{k}. {v['nome']}")
    mat = input("Material: ")
    if mat not in MATERIAIS: return
    diam = float(input("Diâmetro (mm): ") or "50")
    comp = float(input("Comprimento (mm): ") or "100")
    prof = float(input("Profundidade (mm): ") or "2")
    gcode = gerar_gcode_torno(op, mat, diam, comp, prof)
    print("\n\033[1;32mG-CODE:\033[0m\n", gcode)
    if input("Salvar? (s/n): ").lower() == 's':
        nome = input("Nome: ") or "torno"
        with open(f"{nome}.nc", "w") as f: f.write(gcode)
        print(f"{nome}.nc salvo.")

def menu_fresa():
    print("\n\033[1;33m--- FRESADORA ---\033[0m")
    for k, v in OPERACOES_FRESA.items(): print(f"{k}. {v}")
    op = input("Escolha: ")
    if op not in OPERACOES_FRESA: return
    print("Materiais:")
    for k, v in MATERIAIS.items(): print(f"{k}. {v['nome']}")
    mat = input("Material: ")
    if mat not in MATERIAIS: return
    larg = float(input("Largura (mm): ") or "80")
    alt = float(input("Altura (mm): ") or "60")
    prof = float(input("Profundidade (mm): ") or "5")
    gcode = gerar_gcode_fresa(op, mat, larg, alt, prof)
    print("\n\033[1;32mG-CODE:\033[0m\n", gcode)
    if input("Salvar? (s/n): ").lower() == 's':
        nome = input("Nome: ") or "fresa"
        with open(f"{nome}.nc", "w") as f: f.write(gcode)
        print(f"{nome}.nc salvo.")

def main():
    while True:
        limpar_tela()
        cabecalho()
        print("1. Torno\n2. Fresadora\n0. Sair")
        escolha = input("\nOpção: ")
        if escolha == "1": menu_torno()
        elif escolha == "2": menu_fresa()
        elif escolha == "0": break
        else: print("Inválido")
        input("Pressione Enter...")
    print("Encerrado. Créditos: Haroldo Capucci & Arnaldo Santiago")

if __name__ == "__main__":
    main()
