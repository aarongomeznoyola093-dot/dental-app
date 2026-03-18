# Usa Python 3.11 como imagen base (ligera)
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de dependencias
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de la aplicación
COPY . .

# Railway asigna automáticamente un puerto mediante $PORT
# Este comando se ejecutará al iniciar el contenedor
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]