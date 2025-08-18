# Comparativa de Rendimiento: FastAPI vs Flask en Azure (Contenedores + Pruebas de Carga)

> Evaluación objetiva de **latencia**, **throughput (RPS)**, **errores**, **consumo** y **coste por petición (CPP)** ejecutando ambos frameworks en el **mismo App Service Plan**.

## Índice
- [Introducción](#introducción)
- [Objetivo](#objetivo)
- [Alcance y supuestos](#alcance-y-supuestos)
- [Qué medimos](#qué-medimos)
- [Metodología](#metodología)
- [Entregables](#entregables)
- [Métricas clave](#métricas-clave)
- [Observabilidad](#observabilidad)
- [Cómo presentar resultados](#cómo-presentar-resultados)
- [Conclusiones](#conclusiones)
- [Requisitos](#requisitos)
- [Construcción y push a ACR](#construcción-y-push-a-acr)
- [Despliegue en Azure App Service](#despliegue-en-azure-app-service)
- [Pruebas de carga con Locust](#pruebas-de-carga-con-locust)
- [Estructura sugerida del proyecto](#estructura-sugerida-del-proyecto)
- [Fórmula de coste por petición](#fórmula-de-coste-por-petición)
- [Clean-up](#clean-up-para-borrar-todo)

---

## Introducción

Elegir framework backend no es cuestión de gusto: impacta **SLO/SLA**, **UX** y **coste operativo**. La pregunta clave no es “¿cuál es más popular?”, sino **“¿cuál cumple mejor nuestros objetivos de rendimiento y escala al menor coste por petición?”**.

Una elección inadecuada se traduce en **latencias altas**, **5xx/429** en picos y **sobreaprovisionamiento**. Para evitarlo, usamos medición objetiva: **instrumentación**, **pruebas de carga** y **despliegue homogéneo en contenedores**.

## Objetivo

Comparar **FastAPI** y **Flask** desplegados en **Azure App Service (Linux, contenedor)**, midiendo su comportamiento bajo carga con **Locust** y **cuantificando el coste por petición** utilizando **la misma capacidad de cómputo**.

## Alcance y supuestos

- Misma **región** y **App Service Plan** para ambas apps.
- **Endpoints equivalentes** (`/test-api`, `/ping`) e **idempotentes**.
- Sin BD externa (foco en **runtime web**).
- Interpretación basada en **percentiles** (no promedios).

## Qué medimos

- **Latencia** (P50/P95/P99) y su distribución.
- **Throughput / RPS** sostenido.
- **Tasa de errores** (5xx/429) y sus causas.
- **Uso de CPU y memoria** por instancia.
- **Elasticidad** (escala horizontal) y **CPP** (coste por request).

## Metodología

1. **Build**: imágenes Docker de ambos servicios con **base común** y dependencias mínimas.
2. **Registro**: push a **Azure Container Registry (ACR)**.
3. **Despliegue**: dos **WebApps Linux** en el **mismo plan**, con **health checks** y `Always On`.
4. **Pruebas**: **Locust** con usuarios concurrentes y *spawn rate* controlados; export de métricas.
5. **Análisis**: comparar **P95/P99, RPS, errores y consumo**; estimar **CPP**.

## Entregables

- Imágenes Docker **versionadas** en ACR.
- Config de App Service (contenedor, **health check**, **Always On**, **WEBSITES_PORT**).
- `locustfile.py` y export de resultados (CSV / gráficas).
- **Resumen ejecutivo** con conclusiones y recomendaciones operativas.

## Métricas clave

### Latencia (P50/P95/P99)
- Impacto directo en UX y conversión.
- **P95** detecta colas/esporádicos; **P99** revela “colas largas”.
- Objetivo típico API síncrona: **P95 < 300 ms (interna) / < 500 ms (externa)**.
- Acciones: HTTP keep-alive, compresión, reducir *hops*, *pooling* eficiente.

### Throughput / RPS sostenido
- Eficiencia bajo concurrencia: **más RPS = menor coste** en mismo plan.
- ASGI (FastAPI + Uvicorn/Gunicorn) suele rendir más que WSGI (Flask + Gunicorn) en I/O.

### Tasa de errores (5xx/429)
- Estabilidad bajo estrés. Objetivo: **< 0.1%** en pruebas sostenidas.
- Si aparece 429/timeout: *backpressure*, *circuit breakers*, *auto-scale*.

### CPU y memoria
- Coste directo en la nube. Señales:
  - CPU sostenida **> 70%** → escala horizontal antes que *size-up*.
  - OOM → revisar *limits* y consumo por worker.

### Escalabilidad horizontal y elasticidad
- Tiempos de *warm-up* y sensibilidad al *spawn rate*.
- FastAPI (ASGI) suele escalar con **menor overhead**; validar con reglas de *auto-scale* por **P95** y **RPS**.

### Coste por petición (CPP)
- **CPP = Coste_hora_plan / (RPS_sostenido × 3600)**
- Métrica puente técnica-negocio; comparar a igual plan.

## Observabilidad

- **Trazas** (duración por capa), **logs estructurados** (`correlationId`) y **métricas** (P95/RPS/error rate).
- Recomendado: **Azure Monitor** + **OpenTelemetry**; *dashboards* por servicio y versión de imagen.

## Cómo presentar resultados

- **Tabla comparativa**: P50/P95/P99, RPS, Error %, CPU/Mem, CPP.
- **Gráficas Locust**: RPS vs tiempo, percentiles de latencia, usuarios activos, fallos.
- **Hallazgos accionables**: límites y clase de **Gunicorn**, `--workers`, `--threads`, `--worker-class` y políticas de **auto-scale**.

## Conclusiones

**FastAPI**
- ASGI y E/S asíncrona → típicamente mejor **P95/P99** y **RPS** en el mismo plan → **CPP menor**.
- Ideal para **alto tráfico**, integraciones **I/O-bound**, *streaming* y **WebSockets**.
- Consideración: dominio de `async/await`; para **CPU-bound**, subir workers multiproceso.

**Flask**
- WSGI síncrono, simple y con ecosistema maduro → excelente para **CRUD** pequeños, *back-offices* y prototipos.
- Bajo cargas altas suele requerir **más instancias** para sostener el mismo RPS → **CPP mayor**.
- Encaja cuando dependes de librerías bloqueantes o el equipo domina Flask.

**Recomendación**
- Elige por **SLO de latencia** y **CPP objetivo**: si buscas P95 bajo y eficiencia en concurrencia, **FastAPI** es el *default*.
- Si la prioridad es simplicidad y el tráfico es moderado, **Flask** acelera *time-to-market*.
- Independiente del framework: instrumenta **P95/P99, RPS y errores**, habilita **auto-escalado**, usa **connection pooling** y **pruebas de carga** en el pipeline.

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


## Métricas clave y su importancia

- **Latencia (P50, P95, P99):** impacto directo en la experiencia de usuario (UX). Diferencias de ~100 ms pueden definir permanencia o abandono.
- **Requests per Second (RPS):** eficiencia bajo concurrencia; a mayor RPS en el mismo plan, **menor coste por petición (CPP)**.
- **Errores (HTTP 5xx/429):** estabilidad bajo estrés; fallos recurrentes invalidan la escalabilidad percibida.
- **CPU y memoria:** consumo facturable en la nube; frameworks ligeros reducen el gasto mensual.
- **Escalabilidad horizontal:** por su naturaleza asíncrona, **FastAPI** suele escalar mejor con más instancias.

---

## Conclusiones

### FastAPI
- Basado en **ASGI** y orientado a E/S asíncrona → suele ofrecer mejor **P95/P99** y mayor **RPS** en el mismo App Service Plan.
- **CPP menor** gracias a más throughput por vCPU; escala horizontal con menos overhead.
- Ideal para **APIs de alto tráfico**, integraciones **I/O-bound**, *streaming* y **WebSockets**.
- Consideración: requiere conocer `async/await`. Para cargas **CPU-bound**, aumentar *workers* multiproceso (Gunicorn/Uvicorn).

### Flask
- **WSGI** síncrono, muy simple y con ecosistema maduro → excelente para **CRUD** pequeños, *back-offices* y prototipos.
- Bajo cargas altas suele requerir **más instancias** para sostener el mismo RPS → **CPP mayor**.
- Encaja bien cuando dependes de librerías bloqueantes o el equipo domina Flask.

### Recomendación de negocio/operación
- Decide según **SLO de latencia** y **CPP objetivo**: si buscas P95 bajo y eficiencia en concurrencia, **FastAPI** es el candidato por defecto.
- Si la prioridad es **simplicidad** y el tráfico es **moderado**, **Flask** acelera el *time-to-market* con menor curva de aprendizaje.
- Sea cual sea el framework: instrumenta **P95/P99, RPS y errores**, habilita **auto-escalado**, usa **connection pooling** y define **pruebas de carga** en el pipeline para evitar regresiones.

---

## Clean-up (para borrar todo)

```bash
az group delete --name demofastvsflask --yes --no-wait
```

---