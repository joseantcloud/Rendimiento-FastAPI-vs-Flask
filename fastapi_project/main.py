import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Crear la aplicación FastAPI
app = FastAPI()

# Habilitar CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las URL de origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados
)

# Ruta para obtener datos de una API externa (ejemplo: JSONPlaceholder)
@app.get("/test-api")
async def test_api():
    try:
        # Llamar a una API externa de manera asíncrona (JSONPlaceholder)
        async with httpx.AsyncClient() as client:
            response = await client.get("https://jsonplaceholder.typicode.com/posts")
            data = response.json()  # Convertir la respuesta JSON a un diccionario

        # Retornar los primeros 10 elementos de la respuesta
        return JSONResponse(content=data[:10])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Ruta de prueba para asegurarse de que la API esté funcionando
@app.get("/ping")
async def ping():
    return {"message": "API FastAPI is working"}
