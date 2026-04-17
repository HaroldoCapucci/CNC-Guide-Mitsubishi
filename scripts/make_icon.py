from PIL import Image, ImageDraw, ImageFont

def gerar_icone():
    img = Image.new('RGB', (256, 256), color='#0066cc')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        font = ImageFont.load_default()
    draw.text((70, 70), "HC", fill='white', font=font)
    img.save("icon.ico", format='ICO', sizes=[(256,256)])
    print("Ícone icon.ico gerado com sucesso!")

if __name__ == "__main__":
    gerar_icone()
