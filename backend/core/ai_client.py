import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class AIClient:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não definida no arquivo .env")
        self.client = Groq(api_key=api_key)
        # ATUALIZAÇÃO: Modelo antigo 'llama3-8b-8192' descontinuado.
        # Substituído por 'llama-3.1-8b-instant' (recomendado pela Groq)
        self.model = "llama-3.1-8b-instant"

    def analyze_gcode(self, gcode: str, agent_name: str) -> str:
        prompt = f"""Você é um especialista em usinagem CNC chamado {agent_name}.
Analise o seguinte código G-code e forneça um breve resumo do que ele faz.
Destaque possíveis problemas ou sugestões de otimização.
Responda em português, de forma clara e objetiva, no máximo 4 frases.

G-code:
{gcode}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Erro ao consultar IA: {str(e)}"
