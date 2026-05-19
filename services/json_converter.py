# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES/JSON_CONVERTER.PY — CONVERSOR DE ARCHIVOS A SCHEMA JSON
# AnalytiQ AI Suite
#
# Extrae SOLO la estructura de un archivo (Excel, CSV, TSV).
# NUNCA se incluyen datos reales, valores de muestra ni contenido de celdas.
#
# Por cada columna genera:
#   - name:          Nombre de la columna
#   - type:          Tipo de dato inferido (string, integer, float, datetime, boolean, unknown)
#   - nullable:      Si la columna tiene valores vacios (true/false)
#   - unique_count:  Numero de valores unicos (sin mostrar cuales son)
#
# Por cada tabla genera:
#   - name:          Nombre de la hoja o tabla
#   - row_count:     Numero total de filas
#   - sheet_index:   Posicion de la hoja en el Excel
#   - columns:       Lista de columnas con sus metadatos
#   - relationships: Lista vacia (para rellenar manualmente si se necesita)
#
# A nivel global genera:
#   - source_file:   Nombre del archivo original
#   - extracted_at:  Fecha de extraccion
#   - total_tables:  Numero de tablas procesadas
#
# PRIVACIDAD: Se leen como maximo 200 filas para inferir tipos.
# Esas filas se descartan — nunca aparecen en el JSON de salida.
# ═══════════════════════════════════════════════════════════════════════════════

import json
import io
import datetime
import pandas as pd


# Filas maximas a leer para inferir tipos — se descartan tras el analisis
SAMPLE_ROWS = 200


def get_sheet_names(file_bytes: bytes, filename: str) -> list:
    """
    DEVUELVE LOS NOMBRES DE LAS HOJAS DE UN EXCEL.
    Para CSV/TSV devuelve lista vacia.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in ("xlsx", "xls"):
        xf = pd.ExcelFile(io.BytesIO(file_bytes))
        return xf.sheet_names
    return []


def extract_schema(file_bytes: bytes, filename: str, only_sheet: str = None) -> tuple:
    """
    EXTRAE EL SCHEMA DE METADATOS PURO DE UN ARCHIVO.
    No incluye ningun dato real en el JSON de salida.

    Args:
        file_bytes:  Contenido del archivo en bytes
        filename:    Nombre original del archivo
        only_sheet:  Nombre de la hoja a procesar (None = todas)

    Returns:
        (json_string, stats_dict)
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    tables = []

    if ext in ("xlsx", "xls"):
        engine = "openpyxl" if ext == "xlsx" else "xlrd"
        xf = pd.ExcelFile(io.BytesIO(file_bytes))

        sheets_to_process = [only_sheet] if only_sheet else xf.sheet_names

        for sheet in sheets_to_process:

            # Leer muestra para inferir tipos — se descarta tras el analisis
            df_sample = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=sheet,
                engine=engine,
                nrows=SAMPLE_ROWS,
            )

            # Contar filas totales usando solo la primera columna
            try:
                df_count = pd.read_excel(
                    io.BytesIO(file_bytes),
                    sheet_name=sheet,
                    engine=engine,
                    usecols=[0],
                )
                row_count = len(df_count)
            except Exception:
                row_count = len(df_sample)

            columns = _extract_columns(df_sample)

            tables.append({
                "name":          sheet,
                "row_count":     row_count,
                "sheet_index":   xf.sheet_names.index(sheet),
                "columns":       columns,
                "relationships": [],
            })

    elif ext in ("csv", "tsv"):
        sep = "\t" if ext == "tsv" else _detect_separator(
            file_bytes[:2048].decode("utf-8", errors="ignore")
        )

        df_sample = pd.read_csv(
            io.BytesIO(file_bytes),
            sep=sep,
            nrows=SAMPLE_ROWS,
            encoding="utf-8-sig",
        )

        try:
            df_count = pd.read_csv(
                io.BytesIO(file_bytes),
                sep=sep,
                usecols=[0],
                encoding="utf-8-sig",
            )
            row_count = len(df_count)
        except Exception:
            row_count = len(df_sample)

        table_name = filename.rsplit(".", 1)[0]
        columns = _extract_columns(df_sample)

        tables.append({
            "name":          table_name,
            "row_count":     row_count,
            "sheet_index":   0,
            "columns":       columns,
            "relationships": [],
        })

    else:
        raise ValueError(f"Formato '{ext}' no soportado. Usa xlsx, xls, csv o tsv.")

    schema = {
        "metadata": {
            "source_file":  filename,
            "extracted_at": datetime.date.today().isoformat(),
            "total_tables": len(tables),
            "privacy_note": "Este schema contiene unicamente estructura de metadatos. Ningun dato real ha sido incluido.",
        },
        "tables": tables,
    }

    json_str = json.dumps(schema, ensure_ascii=False, indent=2)

    stats = {
        "tables":      len(tables),
        "total_cols":  sum(len(t["columns"]) for t in tables),
        "table_names": [t["name"] for t in tables],
        "size_kb":     round(len(json_str.encode()) / 1024, 1),
    }

    return json_str, stats


# ── EXTRACCION DE METADATOS POR COLUMNA ───────────────────────────────────────

def _extract_columns(df: pd.DataFrame) -> list:
    """
    EXTRAE METADATOS ESTRUCTURALES DE CADA COLUMNA.
    No incluye ningun valor real del archivo.

    Por cada columna devuelve:
        - name:         Nombre de la columna
        - type:         Tipo de dato inferido
        - nullable:     Si tiene valores vacios
        - unique_count: Cuantos valores distintos hay (sin decir cuales)
    """
    columns = []

    for col_name in df.columns:
        col_name_clean = str(col_name).strip()
        if not col_name_clean:
            continue

        series = df[col_name]

        col_meta = {
            "name":         col_name_clean,
            "type":         _detect_type(series),
            "nullable":     bool(series.isna().any()),
            "unique_count": int(series.dropna().nunique()),
        }

        columns.append(col_meta)

    return columns


def _detect_type(series: pd.Series) -> str:
    """
    INFIERE EL TIPO DE DATO DE UNA COLUMNA.
    Solo analiza la estructura, no guarda ningun valor.

    Tipos posibles:
        boolean  — columnas con exactamente 2 valores logicos
        datetime — fechas y timestamps
        integer  — numeros enteros
        float    — numeros decimales
        string   — texto libre
        unknown  — columna vacia o tipos mixtos
    """
    series_clean = series.dropna()

    if len(series_clean) == 0:
        return "unknown"

    # Boolean por tipo nativo de pandas
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    # Boolean por contenido: solo 2 valores logicos conocidos
    unique_lower = set(str(v).strip().lower() for v in series_clean.unique())
    bool_pairs = [
        {"true", "false"},
        {"si", "no"},
        {"yes", "no"},
        {"1", "0"},
        {"s", "n"},
    ]
    if unique_lower in bool_pairs:
        return "boolean"

    # Datetime por tipo nativo de pandas
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Datetime por contenido: intentar parsear como fecha
    if pd.api.types.is_object_dtype(series):
        try:
            parsed = pd.to_datetime(
                series_clean.head(20),
                infer_datetime_format=True,
                errors="coerce",
            )
            if parsed.notna().sum() >= len(parsed) * 0.8:
                return "datetime"
        except Exception:
            pass

    # Integer
    if pd.api.types.is_integer_dtype(series):
        return "integer"

    # Float — comprobar si en realidad son enteros con decimales .0
    if pd.api.types.is_float_dtype(series):
        try:
            if (series_clean % 1 == 0).all():
                return "integer"
        except Exception:
            pass
        return "float"

    # Numerico generico
    if pd.api.types.is_numeric_dtype(series):
        return "float"

    return "string"


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _detect_separator(sample: str) -> str:
    """Detecta el separador mas frecuente en una muestra de CSV."""
    counts = {
        ",":  sample.count(","),
        ";":  sample.count(";"),
        "\t": sample.count("\t"),
    }
    return max(counts, key=counts.get)
