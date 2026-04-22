#!/usr/bin/env python3
"""
Importador DXF/STEP para CNC Guide
Uso: python importador_dxf_step.py --arquivo <caminho>
"""

import sys
import argparse
import os
from math import cos, sin, radians

def importar_dxf(caminho):
    try:
        import ezdxf
        doc = ezdxf.readfile(caminho)
        msp = doc.modelspace()
        pontos = []
        for entity in msp:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                pontos.append((start.x, start.y))
                pontos.append((end.x, end.y))
            elif entity.dxftype() == 'CIRCLE':
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                for ang in range(0, 360, 30):
                    rad = radians(ang)
                    x = cx + r * cos(rad)
                    y = cy + r * sin(rad)
                    pontos.append((x, y))
        if not pontos:
            return "Nenhuma geometria encontrada no DXF."
        gcode = "(Gerado a partir de DXF)\nG21 G90 G94\nG00 Z5\n"
        gcode += f"G00 X{pontos[0][0]:.3f} Y{pontos[0][1]:.3f}\n"
        gcode += "G01 Z-1 F100\n"
        for x, y in pontos[1:]:
            gcode += f"G01 X{x:.3f} Y{y:.3f} F500\n"
        gcode += "G00 Z5\nM30\n"
        return gcode
    except Exception as e:
        return f"Erro ao ler DXF: {e}"

def importar_step(caminho):
    try:
        import cadquery as cq
        part = cq.importers.importStep(caminho)
        faces = part.faces(">Z")
        if faces.size() == 0:
            return "Nenhuma face superior encontrada."
        wire = faces.val().outerWire()
        pts = [(v.X, v.Y) for v in wire.Vertices()]
        if not pts:
            return "Não foi possível extrair pontos do STEP."
        gcode = "(Gerado a partir de STEP)\nG21 G90 G94\nG00 Z5\n"
        gcode += f"G00 X{pts[0][0]:.3f} Y{pts[0][1]:.3f}\n"
        gcode += "G01 Z-1 F100\n"
        for x, y in pts[1:]:
            gcode += f"G01 X{x:.3f} Y{y:.3f} F500\n"
        gcode += "G00 Z5\nM30\n"
        return gcode
    except Exception as e:
        return f"Erro ao ler STEP: {e}"

def main():
    parser = argparse.ArgumentParser(description='Importa DXF/STEP e gera G-code')
    parser.add_argument('--arquivo', required=True, help='Caminho do arquivo')
    parser.add_argument('--formato', choices=['dxf', 'step'], help='Formato (opcional)')
    args = parser.parse_args()

    ext = os.path.splitext(args.arquivo)[1].lower()
    if args.formato:
        fmt = args.formato
    elif ext == '.dxf':
        fmt = 'dxf'
    elif ext in ('.step', '.stp'):
        fmt = 'step'
    else:
        print("Formato não reconhecido. Use --formato dxf ou step")
        sys.exit(1)

    if fmt == 'dxf':
        gcode = importar_dxf(args.arquivo)
    else:
        gcode = importar_step(args.arquivo)

    print(gcode)
    saida = os.path.splitext(args.arquivo)[0] + '.nc'
    with open(saida, 'w') as f:
        f.write(gcode)
    print(f"\nG-code salvo em: {saida}")

if __name__ == "__main__":
    main()
