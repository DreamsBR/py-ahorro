# Usa una imagen base de Python
FROM python:3.11.9

# Establece el directorio de trabajo
WORKDIR /app

# Instala netcat
RUN apt-get update && apt-get install -y netcat-traditional

# Copia todo el contenido del directorio actual al contenedor
COPY . /app/

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto del servidor de desarrollo
EXPOSE 8000

# El CMD se sobrescribe en docker-compose.yml
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]