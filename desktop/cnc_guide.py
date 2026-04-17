#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haroldo Capucci CNC Guide for Mitsubishi M800/M80
Co-autor: Arnaldo Santiago
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

MATERIAIS = {
    "Aço 1020": {"vc": 80, "fz": 0.05, "doc": 1.5},
    "Alumínio": {"vc": 150, "fz": 0.10, "doc": 2.0},
    "Inox 304": {"vc": 60, "fz": 0.03, "doc": 1.0},
    "Plástico": {"vc": 200, "fz": 0.15, "doc": 3.0},
}

OPERACOES_TORNO = ["G71 - Desbaste longitudinal", "G77 - Faceamento", "G78 - Rosqueamento"]
OPERACOES_FRESA = ["G12.1 - Interpolação polar", "G81 - Furação simples", "G83 - Furação com peck", "G34 - Rosqueamento rígido", "G05.1 - High speed"]

def sugerir_parametros(material, diametro=None):
    mat = MATERIAIS.get(material, MATERIAIS["Aço 1020"])
    rpm = int(mat["vc"] * 1000 / (3.1416 * (diametro if diametro else 10)))
    feed = int(rpm * mat["fz"] * 2)
    return rpm, feed, mat["doc"]

class Simulacao:
    def __init__(self, parent):
        self.fig, self.ax = plt.subplots(figsize=(5,4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.set_xlim(-10, 110)
        self.ax.set_ylim(-10, 110)
        self.ax.grid(True)
        self.ax.set_title("Simulação 2D")

    def desenhar_trajetoria(self, pontos):
        self.ax.clear()
        self.ax.set_xlim(-10, 110)
        self.ax.set_ylim(-10, 110)
        self.ax.grid(True)
        if pontos:
            xs, ys = zip(*pontos)
            self.ax.plot(xs, ys, 'r-', linewidth=2)
            self.ax.plot(xs[0], ys[0], 'go', markersize=8, label='Início')
            self.ax.plot(xs[-1], ys[-1], 'ro', markersize=8, label='Fim')
            self.ax.legend()
        self.canvas.draw()

def gerar_gcode_torno(op, material, diam, comp, prof, rpm, feed):
    gcode = f"(Gerado por CNC Guide - Haroldo Capucci & Arnaldo Santiago)\n"
    gcode += f"(Material: {material})\n"
    gcode += f"N10 G21 G90 G95\nN20 M03 S{rpm}\nN30 G00 X{diam+2} Z2\n"
    if "G71" in op:
        gcode += f"N40 G71 U{prof} R1\nN50 G71 P60 Q90 U0.5 W0.1 F{feed}\n"
        gcode += f"N60 G00 X0\nN70 G01 Z-{comp}\nN80 X{diam}\nN90 G00 Z2\nN100 G70 P60 Q90\n"
    elif "G77" in op:
        gcode += f"N40 G77 X0 Z-{comp} I{prof} F{feed}\n"
    elif "G78" in op:
        passo = 1.5
        gcode += f"N40 G78 X0 Z-{comp} I{passo} F{passo*feed/10}\n"
    gcode += f"N110 G00 X{diam+10}\nN120 M05\nN130 M30\n"
    return gcode

def gerar_gcode_fresa(op, material, larg, alt, prof, rpm, feed, xc=50, yc=50):
    gcode = f"(Gerado por CNC Guide - Haroldo Capucci & Arnaldo Santiago)\n"
    gcode += f"(Material: {material})\n"
    gcode += f"N10 G21 G90 G94\nN20 M03 S{rpm}\nN30 G00 X{xc-20} Y{yc-20} Z5\n"
    if "G12.1" in op:
        gcode += f"N40 G12.1\nN50 G01 X0 Y0 F{feed}\nN60 G03 X20 Y0 R10\nN70 G02 X0 Y0 R10\nN80 G13.1\n"
    elif "G81" in op:
        gcode += f"N40 G81 X{xc} Y{yc} Z-{prof} R2 F{feed}\nN50 G80\n"
    elif "G83" in op:
        gcode += f"N40 G83 X{xc} Y{yc} Z-{prof} R2 Q2 F{feed}\nN50 G80\n"
    elif "G34" in op:
        gcode += f"N40 G34 X{xc} Y{yc} Z-{prof} K1.5 F{feed}\n"
    elif "G05.1" in op:
        gcode += f"N40 G05.1 Q1\nN50 G01 X{xc+30} Y{yc} F{feed*2}\nN60 G05.1 Q0\n"
    gcode += f"N70 G00 Z10\nN80 M05\nN90 M30\n"
    return gcode

class CNCGuideApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Haroldo Capucci CNC Guide - Mitsubishi M800/M80")
        self.root.geometry("950x650")
        self.status = tk.Label(root, text="🤖 Desenvolvido por Haroldo Capucci & Arnaldo Santiago | CNC Guide v1.0", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.frame_torno = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_torno, text="🔧 Torno")
        self.criar_aba_torno()
        self.frame_fresa = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_fresa, text="🛠️ Fresadora")
        self.criar_aba_fresa()
        self.frame_sim = ttk.LabelFrame(root, text="Simulação 2D")
        self.frame_sim.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sim = Simulacao(self.frame_sim)

    def criar_aba_torno(self):
        ttk.Label(self.frame_torno, text="Material:").grid(row=0, column=0, padx=5, pady=5)
        self.mat_torno = ttk.Combobox(self.frame_torno, values=list(MATERIAIS.keys()), state="readonly")
        self.mat_torno.grid(row=0, column=1, padx=5, pady=5)
        self.mat_torno.current(0)
        ttk.Label(self.frame_torno, text="Operação:").grid(row=1, column=0, padx=5, pady=5)
        self.op_torno = ttk.Combobox(self.frame_torno, values=OPERACOES_TORNO, state="readonly")
        self.op_torno.grid(row=1, column=1, padx=5, pady=5)
        self.op_torno.current(0)
        ttk.Label(self.frame_torno, text="Diâmetro (mm):").grid(row=2, column=0, padx=5, pady=5)
        self.diam_torno = ttk.Entry(self.frame_torno)
        self.diam_torno.insert(0, "50")
        self.diam_torno.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(self.frame_torno, text="Comprimento (mm):").grid(row=3, column=0, padx=5, pady=5)
        self.comp_torno = ttk.Entry(self.frame_torno)
        self.comp_torno.insert(0, "100")
        self.comp_torno.grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(self.frame_torno, text="Profundidade (mm):").grid(row=4, column=0, padx=5, pady=5)
        self.prof_torno = ttk.Entry(self.frame_torno)
        self.prof_torno.insert(0, "2")
        self.prof_torno.grid(row=4, column=1, padx=5, pady=5)
        btn_sugerir = ttk.Button(self.frame_torno, text="Sugerir Parâmetros", command=self.sugerir_torno)
        btn_sugerir.grid(row=5, column=0, padx=5, pady=5)
        btn_gerar = ttk.Button(self.frame_torno, text="Gerar Código G", command=self.gerar_torno)
        btn_gerar.grid(row=5, column=1, padx=5, pady=5)
        self.txt_gcode_torno = tk.Text(self.frame_torno, height=15, width=70, font=('Courier', 9))
        self.txt_gcode_torno.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        btn_salvar = ttk.Button(self.frame_torno, text="💾 Salvar .NC", command=lambda: self.salvar_gcode(self.txt_gcode_torno))
        btn_salvar.grid(row=7, column=0, columnspan=2, pady=5)
        self.frame_torno.columnconfigure(0, weight=1)
        self.frame_torno.rowconfigure(6, weight=1)

    def criar_aba_fresa(self):
        ttk.Label(self.frame_fresa, text="Material:").grid(row=0, column=0, padx=5, pady=5)
        self.mat_fresa = ttk.Combobox(self.frame_fresa, values=list(MATERIAIS.keys()), state="readonly")
        self.mat_fresa.grid(row=0, column=1, padx=5, pady=5)
        self.mat_fresa.current(0)
        ttk.Label(self.frame_fresa, text="Operação:").grid(row=1, column=0, padx=5, pady=5)
        self.op_fresa = ttk.Combobox(self.frame_fresa, values=OPERACOES_FRESA, state="readonly")
        self.op_fresa.grid(row=1, column=1, padx=5, pady=5)
        self.op_fresa.current(0)
        ttk.Label(self.frame_fresa, text="Largura (mm):").grid(row=2, column=0, padx=5, pady=5)
        self.larg_fresa = ttk.Entry(self.frame_fresa)
        self.larg_fresa.insert(0, "80")
        self.larg_fresa.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(self.frame_fresa, text="Altura (mm):").grid(row=3, column=0, padx=5, pady=5)
        self.alt_fresa = ttk.Entry(self.frame_fresa)
        self.alt_fresa.insert(0, "60")
        self.alt_fresa.grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(self.frame_fresa, text="Profundidade (mm):").grid(row=4, column=0, padx=5, pady=5)
        self.prof_fresa = ttk.Entry(self.frame_fresa)
        self.prof_fresa.insert(0, "5")
        self.prof_fresa.grid(row=4, column=1, padx=5, pady=5)
        btn_sugerir = ttk.Button(self.frame_fresa, text="Sugerir Parâmetros", command=self.sugerir_fresa)
        btn_sugerir.grid(row=5, column=0, padx=5, pady=5)
        btn_gerar = ttk.Button(self.frame_fresa, text="Gerar Código G", command=self.gerar_fresa)
        btn_gerar.grid(row=5, column=1, padx=5, pady=5)
        self.txt_gcode_fresa = tk.Text(self.frame_fresa, height=15, width=70, font=('Courier', 9))
        self.txt_gcode_fresa.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        btn_salvar = ttk.Button(self.frame_fresa, text="💾 Salvar .NC", command=lambda: self.salvar_gcode(self.txt_gcode_fresa))
        btn_salvar.grid(row=7, column=0, columnspan=2, pady=5)
        self.frame_fresa.columnconfigure(0, weight=1)
        self.frame_fresa.rowconfigure(6, weight=1)

    def sugerir_torno(self):
        mat = self.mat_torno.get()
        diam = float(self.diam_torno.get())
        rpm, feed, doc = sugerir_parametros(mat, diam)
        self.prof_torno.delete(0, tk.END)
        self.prof_torno.insert(0, str(doc))
        messagebox.showinfo("Sugestão", f"RPM: {rpm}  Avanço: {feed} mm/min  Prof: {doc} mm")

    def sugerir_fresa(self):
        mat = self.mat_fresa.get()
        rpm, feed, doc = sugerir_parametros(mat, 10)
        self.prof_fresa.delete(0, tk.END)
        self.prof_fresa.insert(0, str(doc))
        messagebox.showinfo("Sugestão", f"RPM: {rpm}  Avanço: {feed} mm/min  Prof: {doc} mm")

    def gerar_torno(self):
        try:
            op = self.op_torno.get()
            mat = self.mat_torno.get()
            diam = float(self.diam_torno.get())
            comp = float(self.comp_torno.get())
            prof = float(self.prof_torno.get())
            rpm, feed, _ = sugerir_parametros(mat, diam)
            gcode = gerar_gcode_torno(op, mat, diam, comp, prof, rpm, feed)
            self.txt_gcode_torno.delete(1.0, tk.END)
            self.txt_gcode_torno.insert(tk.END, gcode)
            pontos = [(0,0), (diam,0), (diam, -comp), (0, -comp)]
            self.sim.desenhar_trajetoria(pontos)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def gerar_fresa(self):
        try:
            op = self.op_fresa.get()
            mat = self.mat_fresa.get()
            larg = float(self.larg_fresa.get())
            alt = float(self.alt_fresa.get())
            prof = float(self.prof_fresa.get())
            rpm, feed, _ = sugerir_parametros(mat, 10)
            gcode = gerar_gcode_fresa(op, mat, larg, alt, prof, rpm, feed)
            self.txt_gcode_fresa.delete(1.0, tk.END)
            self.txt_gcode_fresa.insert(tk.END, gcode)
            pontos = [(0,0), (larg,0), (larg, alt), (0, alt), (0,0)]
            self.sim.desenhar_trajetoria(pontos)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def salvar_gcode(self, text_widget):
        gcode = text_widget.get(1.0, tk.END)
        if not gcode.strip():
            messagebox.showwarning("Aviso", "Nenhum código gerado.")
            return
        arquivo = filedialog.asksaveasfilename(defaultextension=".nc", filetypes=[("NC files", "*.nc")])
        if arquivo:
            with open(arquivo, "w") as f:
                f.write(gcode)
            messagebox.showinfo("Sucesso", f"Arquivo salvo em {arquivo}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CNCGuideApp(root)
    root.mainloop()
