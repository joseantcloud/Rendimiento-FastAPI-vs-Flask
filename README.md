# Comparativa de Rendimiento: FastAPI vs Flask en Azure con Contenedores y Pruebas de Carga

## Introducción

La evaluación de frameworks backend va mucho más allá de la facilidad de desarrollo o de la popularidad en la comunidad. Lo realmente crítico es entender cómo se comportan bajo condiciones reales de uso, cuando múltiples usuarios concurrentes hacen peticiones, cuando la latencia se acumula y cuando la infraestructura en la nube empieza a escalar.

Una mala elección tecnológica puede derivar en:

Altas latencias, que impactan directamente en la experiencia de usuario.

Fallas bajo picos de tráfico, comprometiendo la estabilidad del sistema en momentos clave.

Costos innecesarios en la nube, ya que un framework menos eficiente puede requerir más recursos para ofrecer el mismo nivel de servicio.

Por ello, el uso de métricas objetivas (Requests per Second, latencia promedio, percentiles de respuesta, tasa de errores) se convierte en una práctica esencial dentro de la ingeniería del software moderna y DevOps. Medir no solo permite comparar frameworks como Flask y FastAPI, sino también fundamentar decisiones de arquitectura en datos cuantificables en lugar de percepciones subjetivas.

En este documento se aborda un caso práctico que combina Docker, Azure App Service y pruebas de carga con Locust para demostrar cómo una estrategia basada en métricas ofrece claridad y respaldo en la toma de decisiones técnicas.
---

###
Requisitos

Antes de iniciar con la construcción, despliegue y pruebas, es necesario contar con las siguientes herramientas y servicios configurados:

1. Cuenta en Azure

Una suscripción activa de Azure.

Permisos para crear Resource Groups, App Service Plans, App Services y Azure Container Registry (ACR).

Es recomendable contar con acceso de rol Contributor o superior.

2. Entorno Local

Sistema operativo: Windows, Linux o macOS.

Conectividad estable a internet para ejecutar pruebas y subir imágenes.

Python 3.10+ instalado para ejecutar los proyectos y pruebas con Locust.

3. Azure CLI

Instalado en el entorno local.

Versión mínima recomendada: 2.60+.

Verificación:

az --version


Permite crear recursos en Azure desde línea de comandos y automatizar la integración.

4. Docker

Instalado en el entorno local.

Verificación de instalación:

docker --version


Necesario para construir las imágenes de FastAPI y Flask a partir de los Dockerfiles.

Requiere autenticación en Azure Container Registry (ACR) para subir imágenes.

5. Azure Container Registry (ACR)

Registro privado en Azure para almacenar imágenes Docker.

Ejemplo: fastvsflaskacrdemo.azurecr.io.

Se crea con:

az acr create --resource-group <rg> --name <acr-name> --sku Basic

6. Azure App Service

Servicio PaaS de Azure que permite desplegar las imágenes Docker como aplicaciones web.

Requiere un App Service Plan creado previamente.

Ejemplo de dos aplicaciones a desplegar:

fastapi-app (puerto 8000)

flask-app (puerto 8001)

7. Locust

Herramienta de pruebas de carga que se instala localmente:

pip install locust


Permite generar usuarios concurrentes, medir latencia, fallos y Requests per Second (RPS).

Accesible desde la interfaz web en http://localhost:8089 durante las pruebas.
---

## Construcción y Subida de Imágenes a Azure Container Registry (ACR)

### Crear Resource Group y ACR
```bash
az group create --name demofastvsflask --location eastus
az acr create --resource-group demofastvsflask --name fastvsflaskacrdemo --sku Basic --admin-enabled true
az acr login --name fastvsflaskacrdemo
```

### Flask – Construcción y subida
```bash
docker build -t flask-app:latest .
docker tag flask-app:latest fastvsflaskacrdemo.azurecr.io/flask-app:v1
docker push fastvsflaskacrdemo.azurecr.io/flask-app:v1
```

### FastAPI – Construcción y subida
```bash
docker build -t fast-app:latest .
docker tag fast-app:latest fastvsflaskacrdemo.azurecr.io/fast-app:v1
docker push fastvsflaskacrdemo.azurecr.io/fast-app:v1
```

---

## Creación de App Services en Azure
```bash
az appservice plan create --name fastvsflask-plan --resource-group demofastvsflask --sku B1 --is-linux

# Flask App
az webapp create --resource-group demofastvsflask --plan fastvsflask-plan --name flask-webapp-demo --deployment-container-image-name fastvsflaskacrdemo.azurecr.io/flask-app:v1

# FastAPI App
az webapp create --resource-group demofastvsflask --plan fastvsflask-plan --name fastapi-webapp-demo --deployment-container-image-name fastvsflaskacrdemo.azurecr.io/fast-app:v1
```

Configurar credenciales del ACR en las WebApps:
```bash
az webapp config container set --name flask-webapp-demo --resource-group demofastvsflask --docker-registry-server-url https://fastvsflaskacrdemo.azurecr.io --docker-registry-server-user <ACR-USERNAME> --docker-registry-server-password <ACR-PASSWORD>

az webapp config container set --name fastapi-webapp-demo --resource-group demofastvsflask --docker-registry-server-url https://fastvsflaskacrdemo.azurecr.io --docker-registry-server-user <ACR-USERNAME> --docker-registry-server-password <ACR-PASSWORD>
```

---

## Pruebas de Carga con Locust

### Instalar Locust
```bash
pip install locust
```

### locustfile.py
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_api(self):
        self.client.get("/test-api")
```

### Ejecutar Locust
```bash
locust -f locustfile.py --host=https://flask-webapp-demo.azurewebsites.net
locust -f locustfile.py --host=https://fastapi-webapp-demo.azurewebsites.net
```

Acceder a la interfaz web en: http://localhost:8089

---

## Métricas Clave y su Importancia

1. **Latencia (P50, P95, P99):** mide rapidez de respuesta y experiencia de usuario. Una diferencia de 100 ms puede marcar la percepción de fluidez en apps de alto tráfico.  
2. **Requests per Second (RPS):** refleja capacidad de procesamiento concurrente. Más RPS con menos recursos = mayor eficiencia y menores costos en Azure.  
3. **Errores (HTTP 5xx):** revelan la estabilidad del sistema bajo presión. Una app con menor error-rate inspira confianza en producción.  
4. **Uso de CPU/Memoria:** define qué tan liviano es el framework en ejecución. Directamente ligado a facturación en nube.  
5. **Escalabilidad horizontal (Auto-Scale Azure):** cómo responde cada framework al aumentar instancias. FastAPI suele escalar con menor overhead.  

---

## Conclusiones
- **FastAPI**: mayor rendimiento gracias a asincronía → mejor escalabilidad, menor latencia y consumo más eficiente de recursos.  
- **Flask**: más sencillo, estable y con mayor ecosistema, pero menos eficiente bajo alta concurrencia.  
- **Impacto en negocio**: elegir bien el framework impacta en **costos de infraestructura**, **experiencia de usuario** y **tiempo de respuesta al mercado**.  

Este flujo (Docker + ACR + App Service + Locust) es un pipeline reproducible en cualquier proyecto backend moderno con cultura DevOps.
