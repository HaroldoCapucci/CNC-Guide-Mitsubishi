import json, os
ARQ = os.path.join(os.path.dirname(__file__), 'ferramentas.json')
def carregar():
    if not os.path.exists(ARQ): return []
    with open(ARQ) as f: return json.load(f)
def salvar(f):
    with open(ARQ, 'w') as f: json.dump(f, f, indent=2)
def adicionar(nome, diam, material, vc, fz):
    f = carregar()
    f.append({'id': len(f)+1, 'nome': nome, 'diam': diam, 'material': material, 'vc': vc, 'fz': fz})
    salvar(f)
def listar(): return carregar()
def remover(id):
    f = carregar()
    f = [t for t in f if t['id'] != id]
    salvar(f)
if __name__ == "__main__":
    print("=== Biblioteca de Ferramentas ===")
    for t in listar():
        print(f"{t['id']}: {t['nome']} - Ø{t['diam']}mm")
