import requests
from flask import Flask, jsonify
from flask_cors import CORS

# Crear la aplicación Flask
app = Flask(__name__)

# Habilitar CORS para permitir solicitudes desde cualquier origen
CORS(app)

# Ruta para obtener datos de una API externa (ejemplo: JSONPlaceholder)
@app.route("/test-api", methods=["GET"])
def test_api():
    try:
        # Llamar a una API externa (JSONPlaceholder)
        response = requests.get("https://jsonplaceholder.typicode.com/posts")
        data = response.json()  # Convertir la respuesta JSON a un diccionario

        # Retornar los primeros 10 elementos de la respuesta
        return jsonify(data[:10])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta de prueba para asegurarse de que la API esté funcionando
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "API Flask is working"})

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)  # Asegúrate de que el puerto sea el correcto