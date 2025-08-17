# Comparativa de Rendimiento: FastAPI vs Flask en Azure con Contenedores y Pruebas de Carga

## Introducción

La evaluación de frameworks backend va mucho más allá de la facilidad de desarrollo o de la popularidad en la comunidad. Lo realmente crítico es entender cómo se comportan bajo condiciones reales de uso, cuando múltiples usuarios concurrentes hacen peticiones, cuando la latencia se acumula y cuando la infraestructura en la nube empieza a escalar.

Una mala elección tecnológica puede derivar en:

- **Altas latencias**, que impactan directamente en la experiencia de usuario.  
- **Fallas bajo picos de tráfico**, comprometiendo la estabilidad del sistema en momentos clave.  
- **Costos innecesarios en la nube**, ya que un framework menos eficiente puede requerir más recursos para ofrecer el mismo nivel de servicio.  

Por ello, el uso de métricas objetivas (**Requests per Second, latencia promedio, percentiles de respuesta, tasa de errores**) se convierte en una práctica esencial dentro de la ingeniería del software moderna y DevOps.  

Este documento aborda un caso práctico que combina **Docker, Azure App Service y pruebas de carga con Locust** para demostrar cómo una estrategia basada en métricas ofrece claridad y respaldo en la toma de decisiones técnicas.  

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
  ```

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
- **FastAPI**: mejor rendimiento, menor latencia y más eficiente bajo concurrencia.  
- **Flask**: mayor simplicidad y comunidad madura, pero menos eficiente en alta carga.  
- **Negocio**: elegir bien reduce costos en Azure y mejora experiencia de usuario final.  

---

## Clean-up (para borrar todo)
```bash
az group delete --name demofastvsflask --yes --no-wait
```
