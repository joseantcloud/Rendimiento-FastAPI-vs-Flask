# Comparativa de Rendimiento: FastAPI vs Flask en Azure con Contenedores y Pruebas de Carga

## Introducción

Comparativa de Rendimiento: FastAPI vs Flask en Azure con Contenedores y Pruebas de Carga
Introducción

En ingeniería de software moderna, elegir el framework backend no es una cuestión de gusto: afecta SLO/SLA, experiencia de usuario y coste operativo. La pregunta clave no es “¿cuál es más popular?”, sino “cuál cumple nuestros objetivos de rendimiento y escala en producción con el menor coste por petición”.

Una mala elección se traduce en latencias elevadas, errores 5xx/429 en picos y sobreaprovisionamiento de infraestructura. Para evitarlo, adoptamos un enfoque de medición objetiva alineado a prácticas DevOps: instrumentación, pruebas de carga y despliegue homogéneo con contenedores.

##Objetivo

Comparar FastAPI y Flask desplegados en Azure App Service (Linux, contenedor), midiendo su comportamiento bajo carga con Locust y cuantificando el coste por petición usando la misma capacidad de cómputo.

Qué medimos

Latencia (P50/P95/P99) y su distribución.

Throughput / RPS sostenido en el mismo plan.

Tasa de errores (5xx/429) y causas.

Uso de CPU y memoria por instancia.

Elasticidad (escala horizontal) y coste por request.

Metodología

Build: imágenes Docker de ambos servicios (base común y dependencias mínimas).

Registro: publicación en Azure Container Registry (ACR).

Despliegue: dos WebApps Linux en el mismo App Service Plan, autenticando con Managed Identity frente a ACR y habilitando health checks.

Pruebas: Locust con usuarios concurrentes y spawn rate controlados; export de métricas.

Análisis: comparación de P95/P99, RPS, errores y consumo; estimación de coste por request.

Alcance y supuestos

Misma región y plan para ambos servicios.

Endpoints equivalentes (/test-api, /ping) y pruebas idempotentes.

Sin BD externa (foco en el runtime web).

Interpretación basada en percentiles y no solo promedios.

Entregables

Imágenes Docker versionadas en ACR.

Config de App Service (contenedor, health check, Always On).

locustfile.py y export de resultados (CSV/gráficas).

Resumen ejecutivo con conclusiones y recomendaciones operativas.

###Métricas Clave y su Importancia

Latencia (P50/P95/P99)

Impacto directo en UX y conversión.

P95 detecta colas/esporádicos; P99 revela “colas largas”.

Objetivo típico API síncrona: P95 < 300 ms (interna) / < 500 ms (externa).

Acciones: pooling HTTP eficiente, keep-alive, compresión, reducir hops/redes.

Throughput / RPS sostenido

Eficiencia bajo concurrencia; mayor RPS con el mismo plan = menor coste.

Relacionado con el modelo de concurrencia: ASGI (FastAPI + Uvicorn/Gunicorn) suele rendir más que WSGI (Flask + Gunicorn) en I/O.

Tasa de errores (5xx/429)

Estabilidad bajo estrés. Objetivo: < 0.1% en pruebas sostenidas.

Si aparece 429/timeout: activar backpressure, circuit breakers y auto-scale.

Uso de CPU y Memoria

Directamente facturable en la nube.

Señales: CPU sostenida >70% o OOM → ampliar réplicas (horizontal) antes que size-up.

Escalabilidad horizontal y elasticidad

Tiempos de warm-up y sensibilidad a spawn rate.

FastAPI (ASGI) suele escalar con menor overhead; validar con auto-scale basado en RPS y P95.

Coste por petición (CPP)

Aproximación: CPP = Coste_hora_plan / (RPS_sostenido × 3600)

Métrica puente entre técnica y negocio; comparar CPP entre frameworks a igual plan.

Observabilidad

Trazas (duración por capa), logs estructurados (correlationId) y métricas (P95/RPS/error rate).

Recomendado: Azure Monitor + OpenTelemetry; dashboards por servicio y por versión de imagen.

Cómo presentar resultados

Tabla comparativa: P50/P95/P99, RPS, Error %, CPU/Mem, CPP.

Gráficas Locust: RPS vs tiempo, latencia percentil, usuarios activos, fallos.

Hallazgos accionables: límites de worker Gunicorn, número de workers/threads, --workers y --worker-class apropiados, y políticas de auto-scale recomendadas.

Conclusiones orientadas a decisión

FastAPI: mejor latencia P95/P99 y RPS con igual plan → menor CPP y mejor experiencia bajo picos.
Flask: simplicidad y ecosistema maduro; adecuado para cargas moderadas o servicios sin I/O intensivo.

Negocio: seleccionar en función de CPP objetivo, SLO de latencia y complejidad del equipo. Integrar pruebas en pipeline (pre-prod) para evitar regresiones de rendimiento.
---

## Requisitos

Antes de iniciar con la construcción, despliegue y pruebas, es necesario contar con las siguientes herramientas y servicios configurados:

### 1. Cuenta en Azure
- Suscripción activa de Azure.
- Permisos para crear **Resource Groups, App Service Plans, WebApps y Azure Container Registry (ACR)**.
- Rol mínimo recomendado: **Contributor**.

### 2. Entorno Local
- Sistema operativo: Windows, Linux o macOS.
- Python **3.10+** instalado para ejecutar Locust y las apps de prueba.
- Conectividad a internet estable para subir imágenes y ejecutar pruebas.

### 3. Azure CLI
- Instalación local, versión **2.60+**.
- Verificación:
  ```bash
  az --version
````

### 4. Docker

- Instalación local para construir y testear imágenes.
- Verificación:
  ```bash
  docker --version
  ```

### 5. Azure Container Registry (ACR)

- Registro privado en Azure para subir imágenes.
- Ejemplo: `fastvsflaskacrdemo.azurecr.io`.
- Se habilita con:
  ```bash
  az acr create --resource-group <rg> --name <acr-name> --sku Basic --admin-enabled true
  ```

### 6. Azure App Service

- PaaS de Azure que ejecuta imágenes Docker como aplicaciones web.
- Requiere un **App Service Plan**.
- Dos apps a desplegar:
  - `flask-webapp-demo` (puerto 8001)
  - `fastapi-webapp-demo` (puerto 8000)

### 7. Locust

- Instalación local:
  ```bash
  pip install locust
  ```
- Expone una UI web en: [http://localhost:8089](http://localhost:8089)

---

## Construcción y Subida de Imágenes a ACR

### Crear Resource Group y ACR

```bash
az group create --name demofastvsflask --location eastus
az acr create --resource-group demofastvsflask --name fastvsflaskacrdemo --sku Basic --admin-enabled true
az acr login --name fastvsflaskacrdemo
```

### Flask – Build y Push

```bash
docker build -t flask-app:latest .
docker tag flask-app:latest fastvsflaskacrdemo.azurecr.io/flask-app:v1
docker push fastvsflaskacrdemo.azurecr.io/flask-app:v1
```

### FastAPI – Build y Push

```bash
docker build -t fast-app:latest .
docker tag fast-app:latest fastvsflaskacrdemo.azurecr.io/fast-app:v1
docker push fastvsflaskacrdemo.azurecr.io/fast-app:v1
```

---

## Creación de App Services en Azure

```bash
az appservice plan create --name fastvsflask-plan --resource-group demofastvsflask --sku B1 --is-linux

az webapp create --resource-group demofastvsflask --plan fastvsflask-plan --name flask-webapp-demox-2025 --deployment-container-image-name fastvsflaskacrdemo.azurecr.io/flask-app:v1

az webapp create --resource-group demofastvsflask --plan fastvsflask-plan --name fastapi-webapp-demox-2025 --deployment-container-image-name fastvsflaskacrdemo.azurecr.io/fast-app:v1
```

---

## Pruebas de Carga con Locust

### Archivo `locustfile.py`

```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_api(self):
        self.client.get("/test-api")
```

### Ejecutar pruebas

```bash
locust -f locustfile.py --host=https://flask-webapp-demo.azurewebsites.net
locust -f locustfile.py --host=https://fastapi-webapp-demo.azurewebsites.net
```

Accede a: [http://localhost:8089](http://localhost:8089)

---

## Métricas Clave y su Importancia

1. **Latencia (P50, P95, P99):** impacto directo en UX. Una diferencia de 100 ms puede definir si un usuario permanece o abandona.
2. **Requests per Second (RPS):** eficiencia del framework bajo concurrencia → menos costo por petición.
3. **Errores (HTTP 5xx):** estabilidad bajo estrés; fallos recurrentes invalidan escalabilidad.
4. **CPU/Memoria:** consumo directo facturable en la nube. Frameworks ligeros reducen gasto mensual.
5. **Escalabilidad horizontal:** FastAPI, por ser asíncrono, escala mejor con más instancias.

---

## Conclusiones

FastAPI

Basado en ASGI y orientado a E/S asíncrona: suele entregar mejor P95/P99 y más RPS que Flask en el mismo App Service Plan.

Costo por petición (CPP) menor gracias a mayor throughput por vCPU; escala horizontal con menos overhead.

Ideal para APIs de alto tráfico, integraciones I/O-bound, streaming y WebSockets.

Consideraciones: requiere conocer async/await; para cargas CPU-bound conviene subir workers multiproceso (Gunicorn/Uvicorn).

Flask

WSGI síncrono, muy simple y con ecosistema maduro: excelente para servicios pequeños/CRUD, back-offices y prototipos.

Bajo cargas altas tiende a necesitar más instancias para sostener el mismo RPS → CPP mayor.

Encaja bien cuando dependes de librerías bloqueantes o equipos con fuerte experiencia previa en Flask.

Recomendación de negocio/operación

Elige con base en SLO de latencia y CPP objetivo: si buscas P95 bajo y eficiencia en concurrencia, FastAPI es el candidato por defecto.

Si la prioridad es simplicidad y el tráfico es moderado, Flask ofrece rapidez de entrega con menor curva de aprendizaje.

Independiente del framework: instrumenta P95/P99, RPS y errores, habilita auto-escalado, aplica connection pooling y define pruebas de carga en el pipeline para evitar regresiones.

---

## Clean-up (para borrar todo)

```bash
az group delete --name demofastvsflask --yes --no-wait
```
