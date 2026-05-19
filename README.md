# AnalytiQ AI Suite

Multi-Language Analytics AI — Genera, valida, explica y documenta formulas de Power BI, Looker Studio, Google Sheets y Excel usando inteligencia artificial con fallback automatico entre proveedores.

---

## Descripcion

AnalytiQ AI Suite es una aplicacion web construida con Streamlit que actua como asistente de inteligencia artificial para analistas de datos y desarrolladores BI. Permite trabajar con cuatro plataformas analiticas desde una unica interfaz, con un sistema de fallback entre proveedores de IA que garantiza disponibilidad continua.

Privacidad por diseno: solo se procesan metadatos (nombres de tablas y columnas). Nunca se envian datos reales a ningun modelo de IA.

---

## Modulos disponibles

- Power BI (DAX): Generar, Validar, Explicar, Evaluar, Chat, Medidas Base
- Looker Studio: Generar, Validar, Explicar, Evaluar, Chat, Campos Base
- Google Sheets: Generar, Validar, Explicar, Evaluar, Chat, Formulas Base
- Excel: Generar, Validar, Explicar, Evaluar, Chat, Formulas Base
- Docs: Documentacion completa del modelo con exportacion a PDF (todas las plataformas)
- JSON: Extraccion de schema de metadatos desde archivos Excel, CSV y TSV

---

## Proveedores de IA — Fallback automatico

El sistema sigue este orden de prioridad:

    9Router → Groq → SambaNova → Gemini

Si un proveedor alcanza su limite de tokens o no esta disponible, cambia automaticamente al siguiente sin interrumpir el flujo de trabajo.

---

## Estructura del proyecto

```
ANALYTIQ-AI/
│
├── app.py                          # Punto de entrada principal (Streamlit)
├── styles.py                       # Sistema de CSS dinamico por plataforma
├── requirements.txt                # Dependencias Python
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # Modelos LLM, colores PDF, constantes globales
│
├── core/
│   ├── __init__.py
│   ├── llm.py                      # Cliente LLM unificado con fallback automatico
│   ├── pdf.py                      # Generador de PDFs con ReportLab
│   └── tokens.py                   # Tracking de tokens por proveedor
│
├── modules/
│   ├── __init__.py
│   ├── power_bi/
│   │   ├── generator.py            # Generacion de medidas DAX y DAX recomendados
│   │   ├── validator.py            # Validacion estatica + IA de medidas DAX
│   │   └── core_functions.py       # Explicar, Evaluar, Chat, Medidas Base, Docs
│   ├── looker/
│   │   ├── generator.py            # Generacion de campos calculados Looker
│   │   ├── validator.py            # Validacion de expresiones Looker
│   │   └── core_functions.py       # Explicar, Evaluar, Chat, Campos Base, Docs
│   ├── sheets/
│   │   ├── generator.py            # Generacion de formulas Google Sheets
│   │   ├── validator.py            # Validacion de formulas
│   │   └── core_functions.py       # Explicar, Evaluar, Chat, Formulas Base, Docs
│   └── excel/
│       ├── generator.py            # Generacion de formulas Excel
│       ├── validator.py            # Validacion de formulas
│       └── core_functions.py       # Explicar, Evaluar, Chat, Formulas Base, Docs
│
├── services/
│   ├── __init__.py
│   └── json_converter.py           # Extraccion de schema desde archivos reales
│
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── render_helpers.py       # Helpers de renderizado compartidos
│   │   └── schema_panel.py         # Panel de carga de schema (JSON o SQL Server)
│   └── tabs/
│       ├── tabs_power_bi.py        # Pestanas del modulo Power BI
│       ├── tabs_looker.py          # Pestanas del modulo Looker Studio
│       ├── tabs_sheets.py          # Pestanas del modulo Google Sheets
│       ├── tabs_excel.py           # Pestanas del modulo Excel
│       ├── tabs_docs.py            # Pestana de Documentacion global
│       └── tabs_json.py            # Pestana del Conversor JSON
│
└── examples/
    ├── schema_power_bi.json        # Schema de ejemplo para Power BI
    ├── schema_looker_studio.json   # Schema de ejemplo para Looker Studio
    ├── schema_google_sheets.json   # Schema de ejemplo para Google Sheets
    └── schema_excel.json           # Schema de ejemplo para Excel
```

---

## Instalacion local

### Requisitos previos

- Python 3.11 o superior
- Al menos una API Key de los proveedores soportados (Groq, SambaNova, Gemini o 9Router)

### Paso 1 — Clonar el repositorio

```bash
git clone https://gitlab.nfqsolutions.es/oscar.herruzo/analytiq-ai-suite.git
cd analytiq-ai-suite
```

### Paso 2 — Crear entorno virtual

En Windows:
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

En Mac o Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4 — Configurar las API Keys

Crea la carpeta `.streamlit` en la raiz del proyecto y dentro el archivo `secrets.toml`:

```
ANALYTIQ-AI/
└── .streamlit/
    └── secrets.toml        <- crear este archivo manualmente
```

Contenido del archivo `secrets.toml`:

```toml
[ai_config]
BASE_URL = "https://tu-9router-url"
API_KEY  = "tu-9router-key"

GROQ_API_KEY       = "gsk_..."
SAMBANOVA_API_KEY  = "..."
GEMINI_API_KEY     = "AI..."
```

No es obligatorio tener todos los proveedores. Con solo GROQ_API_KEY ya funciona.

### Paso 5 — Lanzar la aplicacion

```bash
streamlit run app.py
```

La aplicacion se abre automaticamente en http://localhost:8501

---

## Despliegue en Streamlit Cloud

Streamlit Cloud permite desplegar la aplicacion de forma gratuita y publica directamente desde GitHub.

### Paso 1 — Subir el proyecto a GitHub

Asegurate de que el archivo `.streamlit/secrets.toml` esta en el `.gitignore` para no exponer las API Keys:

```bash
echo ".streamlit/secrets.toml" >> .gitignore
git add .
git commit -m "initial commit"
git push origin main
```

### Paso 2 — Crear cuenta en Streamlit Cloud

Ve a https://share.streamlit.io y accede con tu cuenta de GitHub.

### Paso 3 — Crear nueva aplicacion

1. Haz clic en "New app"
2. Selecciona el repositorio de GitHub
3. Branch: main
4. Main file path: app.py
5. Haz clic en "Deploy"

### Paso 4 — Configurar las API Keys en Streamlit Cloud

Una vez desplegada la app, ve a Settings de la aplicacion y busca la seccion "Secrets". Pega exactamente el mismo contenido que tienes en tu archivo `secrets.toml` local:

```toml
[ai_config]
BASE_URL = "https://tu-9router-url"
API_KEY  = "tu-9router-key"

GROQ_API_KEY       = "gsk_..."
SAMBANOVA_API_KEY  = "..."
GEMINI_API_KEY     = "AI..."
```

Guarda los cambios y la aplicacion se reiniciara automaticamente con las claves configuradas.

### Paso 5 — URL publica

Streamlit Cloud te asignara una URL publica del tipo:

```
https://tu-usuario-nombre-repositorio-app-xxxx.streamlit.app
```

Puedes compartir esa URL con cualquier persona para que acceda a la aplicacion sin necesidad de instalar nada.

---

## Flujo de trabajo recomendado

1. Abre el modulo "JSON" en la barra de navegacion
   - Sube tu archivo Excel, CSV o TSV
   - Haz clic en "Extraer schema JSON"
   - Descarga el archivo _schema.json generado

2. Ve al modulo de tu plataforma (Power BI, Looker, Sheets o Excel)
   - En el panel izquierdo selecciona "Subir JSON"
   - Sube el schema descargado en el paso anterior
   - La IA ya conoce la estructura de tu modelo

3. Usa las pestanas del modulo para trabajar con tu modelo
   - Generar: describe en lenguaje natural lo que necesitas
   - Validar: pega una formula y comprueba si es correcta
   - Explicar: pega una formula y obtiene una explicacion detallada
   - Evaluar: analiza si la logica de negocio de una formula es correcta
   - Chat: pregunta libremente sobre tu modelo de datos

4. Cuando tengas el modelo listo, ve al modulo "Docs"
   - Selecciona la plataforma
   - Sube el schema
   - Genera la documentacion completa y exporta a PDF

---

## Seguridad

- El archivo `secrets.toml` esta excluido del repositorio via `.gitignore`
- Solo se procesan metadatos: nombres de tablas y columnas
- Los datos reales de los archivos nunca se envian a ninguna IA
- La conversion de archivos a schema JSON es 100% local, sin llamadas externas

---

## Autor

Oscar Herruzo
oscar.herruzo@nfqsolutions.es
NFQ Solutions — 2025
