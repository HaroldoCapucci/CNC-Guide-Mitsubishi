import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class AIClient:
    # Modelos disponíveis
    AVAILABLE_MODELS = {
        "llama-3.1-8b-instant": "Llama 3.1 8B (rápido)",
        "mixtral-8x7b-32768": "Mixtral 8x7B (potente)",
        "gemma2-9b-it": "Gemma 2 9B (Google)",
        "offline": "Modo Simulado (sem IA)"
    }

    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.model = model
        if model != "offline":
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY não definida no arquivo .env")
            self.client = Groq(api_key=api_key)
        else:
            self.client = None

    def analyze_gcode(self, gcode: str, agent_name: str) -> str:
        if self.model == "offline":
            # Resposta simulada para testes
            return f"[SIMULADO] {agent_name} analisou o G-code. A trajetória parece segura, sem colisões detectadas."

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

    @classmethod
    def get_available_models(cls):
        return cls.AVAILABLE_MODELS
