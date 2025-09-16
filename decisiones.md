## Resumen del enfoque

Para cumplir con las consignas del tp2, implemente una app **Python + Flask** muy simple, una base de datos **PostgreSQL** en contenedor con **volumen persistente**, y un `docker-compose.yml` que levanta **QA** y **PROD** con **la misma imagen** pero **distintas variables de entorno**. Se publicaron imágenes en Docker Hub con tags `dev`y y `v1.0`.

---

## Elección de la aplicación y tecnología utilizada

* **Tecnología:** *Python 3.12 + Flask*.
* **Motivos:**

  * **Simplicidad:** Flask permite exponer una API funcional en pocas líneas.
  * **Rapidez de setup:** no requiere frameworks pesados ni tooling complejo.
  * **Enfoque docente:** es fácil mostrar diferencias de entorno (QA/PROD) y la conexión a una DB en contenedor.
* **Funcionalidad mínima:**

  * `GET /health` para ver estado.
  * `GET /items` y `POST /items` contra Postgres (creación de tabla si no existe + CRUD mínimo).

---

## Elección de imagen base y justificación

* **Imagen base:** `python:3.12-slim`.
* **Justificación:**

  * **Oficial y mantenida** por la comunidad de Python (seguridad y actualizaciones).
  * **Ligera** comparada con la variante completa, reduciendo peso de la imagen.
  * **Suficiente** para Flask y el driver de Postgres (`psycopg2-binary`) instalando solo `libpq-dev` y build tools mínimos.

---

## Estructura y justificación del Dockerfile

**Dockerfile (resumen de pasos clave):**

1. `FROM python:3.12-slim` → base liviana oficial.
2. `ENV PYTHONDONTWRITEBYTECODE=1` y `PYTHONUNBUFFERED=1` → evita `.pyc` y fuerza logs por stdout.
3. `WORKDIR /app` → directorio de trabajo estándar.
4. `apt-get ... libpq-dev build-essential` → dependencias mínimas para `psycopg2`.
5. `COPY app/requirements.txt .` + `pip install -r` → **capa de cache** para dependencias.
6. `COPY app/ .` → copia del código.
7. `EXPOSE 5000` → puerto de Flask.
8. `CMD ["python","app.py"]` → comando por defecto.

**Decisión de 1 sola etapa:** La app es muy pequeña; un build multi-stage sería sobreingeniería aquí. Este Dockerfile es **simple**, **rápido** de construir y **suficiente** para el TP.

---

## Elección de base de datos y justificación

* **DB:** PostgreSQL (imagen oficial `postgres:14`).
* **Motivos:**

  * Estándar sólido en la industria, con tooling y documentación abundante.
  * Imagen oficial estable y simple de orquestar.
  * Driver maduro en Python (`psycopg2-binary`).
* **Conexión desde la app:** variables de entorno (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) leídas por `db.py`. El host interno es `db` (nombre del servicio en Compose).

---

## Configuración de QA y PROD (variables de entorno)

* **Misma imagen** para ambos entornos; la diferencia está en **`.env`**:

  * **QA (`.env.qa`):**

    * `FLASK_DEBUG=1` (JSON "pretty", mensajes detallados).
    * `APP_ENV=qa` (etiqueta informativa).
    * Puertos: host `5001` → contenedor `5000`.
  * **PROD (`.env.prod`):**

    * `FLASK_DEBUG=0` (JSON compacto, sin debug).
    * `APP_ENV=prod`.
    * Puertos: host `5002` → contenedor `5000`.
* **Compose:** `depends_on` + `healthcheck` en `db` aseguran que la app arranque cuando la DB está lista.

> **Nota:** Para simplificar el TP, QA y PROD apuntan a **la misma base de datos**. Si se requiriera aislamiento, bastaría con definir distintos `DB_NAME`/credenciales o duplicar el servicio `db` (p. ej. `db-qa` y `db-prod`).

---

## Estrategia de persistencia de datos (volúmenes)

* **Volumen nombrado:** `dbdata` → montado en `/var/lib/postgresql/data` en el contenedor de Postgres.
* **Motivo:** los datos **sobreviven** aunque el contenedor de `db` se detenga/elimine (`docker compose down`), cumpliendo la exigencia de **persistencia entre reinicios**.
* **Verificación realizada:**

  1. Insertar registros con `POST /items`.
  2. `docker compose down`.
  3. `docker compose up -d`.
  4. `GET /items` devuelve los mismos datos → persistencia OK.

---

## Estrategia de versionado y publicación

* **Tags en Docker Hub:**

  * `agustinreynaucc/tp2-flask:dev` → tag de **desarrollo/QA**.
  * `agustinreynaucc/tp2-flask:v1.0` → **versión estable** para PROD.
* **Convención:** estilo SemVer **simplificado** para el TP. Futuras correcciones podrían etiquetarse como `v1.0.1`, `v1.1`, etc.
* **Motivo:** separar **cambios frecuentes** (QA) de la **versión entregable** (PROD), garantizando **reproducibilidad** y control en despliegues.

---

## Evidencia de funcionamiento (dónde insertar capturas/logs)

> **Colocar aquí capturas de pantalla** o adjuntar logs que demuestren:

1. **La aplicación corriendo en ambos entornos**

   ![App QA y PROD](evidencia/evidencia_uno.png)

2. **Conexión exitosa a la base de datos**

   ![Conexion a la db](evidencia/evidencia_dos.png)

3. **Datos persisten entre reinicios de contenedor**

   ![Datos persistiendo](evidencia/evidencia_uno.png)

> Ejemplos de comandos útiles para generar evidencia (opcional):
>
> ```bash
> docker compose ps > evidencia_ps.txt
> docker logs tp2_app_qa  --since 5m > evidencia_logs_qa.txt
> docker logs tp2_app_prod --since 5m > evidencia_logs_prod.txt
> ```

---

## Problemas y soluciones

* **1) Error `UndefinedTable: relation "items" does not exist` al primer `POST /items`**

  * **Causa:** creación de tabla estaba en `GET /items`. Si se hacía `POST` primero, la tabla no existía.
  * **Solución rápida:** ejecutar `GET /items` antes del primer `POST`.
  * **Mejora sugerida:** crear la tabla en el arranque de la app.

* **2) Terminal bloqueada tras `docker compose up`**

  * **Causa:** se ejecutó sin `-d`; compose queda mostrando logs.
  * **Solución:** `CTRL+C` para detener, o usar `docker compose up -d` para correr en segundo plano.

* **3) `docker push` falló con `authorization failed`**

  * **Causa:** no se había hecho `docker login` o el tag no tenía el namespace correcto.
  * **Solución:** `docker login`, etiquetar como `usuario/imagen:tag` y (si aplica) crear el repo en Docker Hub.

* **4) QA no respondía en `/health`**

  * **Causa:** solo se recreó `app-prod` (no se levantó `app-qa`).
  * **Solución:** `docker compose up -d app-qa` para iniciar QA también.

* **5) Creación de archivos `.env` en Windows**

  * **Causa:** diferencias entre CMD/PowerShell; here-strings no funcionaron en CMD.
  * **Solución:** usar `echo ... > archivo` y `echo ... >> archivo` (compatible con CMD/PowerShell).

---

## Reproducibilidad (cómo asegurar que corre igual en cualquier máquina)

* **Plantillas de entorno**: `.env.example.qa` y `.env.example.prod` versionadas en Git.
* **Archivos reales** `.env.qa` y `.env.prod` listados en `.gitignore`.
* **Compose con versiones fijas**: `postgres:14`, `agustinreynaucc/tp2-flask:dev` (QA) y `:v1.0` (PROD).
* **Procedimiento estándar** para cualquier máquina:

  1. `git clone ... && cd ...`
  2. `copy .env.example.qa .env.qa` y `copy .env.example.prod .env.prod`
  3. `docker compose pull`
  4. `docker compose up -d`
  5. Verificación: `/health` en 5001 (QA) y 5002 (PROD)

---

## Anexo (fragmentos útiles)

* **Servicios y puertos**:

  * QA → `http://localhost:5001`
  * PROD → `http://localhost:5002`
  * DB → `localhost:5432` (expuesto para clientes externos si se requiere)
* **Volumen**: `dbdata` → `/var/lib/postgresql/data` (Postgres)
* **Imagenes Docker Hub**:

  * `agustinreynaucc/tp2-flask:dev`
  * `agustinreynaucc/tp2-flask:v1.0`

---

> **Nota:** Las **capturas** y/o **logs** se insertarán en la sección de *Evidencia de funcionamiento* donde está indicado con *\[PONER CAPTURA]* o *\[PONER CAPTURA/LOG]*.
