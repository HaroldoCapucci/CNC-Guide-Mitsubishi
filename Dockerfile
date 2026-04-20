# Estágio 1: Build do frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Estágio 2: Backend Python + frontend servido estaticamente
FROM python:3.11-slim
WORKDIR /app

# Instala dependências do sistema (apenas se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend
COPY backend/ ./backend/

# Copia o build do frontend para a pasta static do Flask
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Cria diretório para o banco de dados SQLite
RUN mkdir -p /app/backend/data

# Variáveis de ambiente
ENV FLASK_ENV=production
ENV PORT=8000
ENV GROQ_API_KEY=""

# Expõe a porta
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização (Gunicorn)
CMD ["sh", "-c", "gunicorn --bind=0.0.0.0:$PORT --workers=4 --timeout=120 backend.api.main:app"]
