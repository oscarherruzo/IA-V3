# CLIENTE LLM UNIFICADO: 9ROUTER COMO PRIMARIO + GROQ / SAMBANOVA / GEMINI COMO FALLBACK
# LA LÓGICA DE FALLBACK RESPETA EL ORDEN: 9Router → Groq → SambaNova → Gemini

import streamlit as st
import time
from openai import OpenAI
from groq import Groq
from google import genai
from google.genai import types as genai_types
import requests  

from config.settings import (
    MODEL_9ROUTER, MODEL_GROQ, MODEL_SAMBANOVA, MODEL_GEMINI,
    QUOTA_KEYWORDS,
)


# ── DETECCIÓN DE ERRORES DE CUOTA ─────────────────────────────────────────────

def _is_quota_error(e: Exception) -> bool:
    # COMPRUEBA SI LA EXCEPCIÓN INDICA UN LÍMITE DE TASA O CUOTA AGOTADA
    err_str = str(e).lower()
    if any(kw in err_str for kw in QUOTA_KEYWORDS):
        return True
    status = getattr(e, "status_code", None) or getattr(e, "status", None)
    if status == 429:
        return True
    if type(e).__name__ in ("RateLimitError", "APIStatusError"):
        return True
    return False


# ── ESTIMADOR DE TOKENS SIN DEPENDENCIAS EXTERNAS ────────────────────────────

def _count_tokens(messages: list, response_text: str) -> dict:
    # ESTIMA TOKENS DE PROMPT Y COMPLETION BASÁNDOSE EN LONGITUD DE TEXTO
    prompt_tokens = 0
    for msg in messages:
        prompt_tokens += 4
        prompt_tokens += max(1, len(msg.get("content", "")) // 4)
    prompt_tokens += 2
    completion_tokens = max(1, len(response_text) // 4)
    return {
        "prompt":     prompt_tokens,
        "completion": completion_tokens,
        "total":      prompt_tokens + completion_tokens,
    }


def _accumulate(provider: str, counts: dict):
    # ACUMULA LOS TOKENS Y LLAMADAS EN EL SESSION STATE PARA EL PANEL DE TOKENS
    st.session_state[f"tokens_{provider}_prompt"]     += counts["prompt"]
    st.session_state[f"tokens_{provider}_completion"] += counts["completion"]
    st.session_state[f"tokens_{provider}_calls"]      += 1


# ── SINGLETONS DE CLIENTES (CACHEADOS POR STREAMLIT) ─────────────────────────

@st.cache_resource
def _client_9router(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key)

@st.cache_resource
def _client_groq(api_key: str) -> Groq:
    return Groq(api_key=api_key)

@st.cache_resource
def _client_sambanova(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")

@st.cache_resource
def _client_gemini(api_key: str):
    return genai.Client(api_key=api_key)


# ── FUNCIÓN PRINCIPAL DE LLAMADA LLM ─────────────────────────────────────────

def call_llm(messages: list, temperature: float = 0.1, max_tokens: int = 2000) -> str:
    """
    LLAMADA UNIFICADA AL LLM CON FALLBACK AUTOMÁTICO.
    ORDEN: 9Router (local) → Groq → SambaNova → Gemini

    Args:
        messages:    Lista de dicts con "role" y "content"
        temperature: Temperatura de generación (0.1 por defecto = determinista)
        max_tokens:  Límite de tokens de salida

    Returns:
        str: Texto de la respuesta del modelo
    """
    import requests
    
    ss = st.session_state

    router_url = ss.get("router_base_url", "").strip()
    router_key = ss.get("router_api_key", "").strip()
    groq_key   = ss.get("groq_api_key", "").strip()
    snova_key  = ss.get("sambanova_api_key", "").strip()
    gemini_key = ss.get("gemini_api_key", "").strip()

    # ── 1. 9ROUTER ────────────────────────────────────────────────────────────
    router_available = False
    if router_url and router_key:
        try:
            # VERIFICAR QUE 9ROUTER ESTÁ DISPONIBLE
            test_response = requests.get(
                f"{router_url}/models",
                headers={"Authorization": f"Bearer {router_key}"},
                timeout=2
            )
            router_available = test_response.status_code == 200
        except:
            router_available = False
    
    if router_available:
        try:
            client   = _client_9router(router_url, router_key)
            response = client.chat.completions.create(
                model=MODEL_9ROUTER,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content

            # ACUMULAMOS TOKENS REALES SI EL ENDPOINT LOS DEVUELVE
            if hasattr(response, "usage") and response.usage:
                _accumulate("9router", {
                    "prompt":     response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total":      response.usage.total_tokens,
                })
            else:
                _accumulate("9router", _count_tokens(messages, text))

            return text

        except Exception as e:
            if not _is_quota_error(e):
                raise
            if groq_key or snova_key or gemini_key:
                st.toast("9Router sin tokens — cambiando de proveedor")

    # ── 2. GROQ ───────────────────────────────────────────────────────────────
    if groq_key:
        try:
            client     = _client_groq(groq_key)
            completion = client.chat.completions.create(
                model=MODEL_GROQ,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = completion.choices[0].message.content
            _accumulate("groq", _count_tokens(messages, text))
            return text
        except Exception as e:
            if not _is_quota_error(e):
                raise
            if snova_key or gemini_key:
                st.toast("Groq sin tokens — cambiando de proveedor")

    # ── 3. SAMBANOVA ──────────────────────────────────────────────────────────
    if snova_key:
        try:
            client     = _client_sambanova(snova_key)
            completion = client.chat.completions.create(
                model=MODEL_SAMBANOVA,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = completion.choices[0].message.content
            _accumulate("sambanova", _count_tokens(messages, text))
            return text
        except Exception as e:
            if _is_quota_error(e) and gemini_key:
                st.toast("SambaNova limitada — saltando a Gemini")
            elif not gemini_key:
                raise

    # ── 4. GEMINI ─────────────────────────────────────────────────────────────
    if gemini_key:
        try:
            client      = _client_gemini(gemini_key)
            system_text = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_text   = messages[-1]["content"]
            prompt      = (system_text + "\n\n" + user_text) if system_text else user_text
            config      = genai_types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            try:
                response = client.models.generate_content(
                    model=MODEL_GEMINI, contents=prompt, config=config,
                )
                text = response.text
            except Exception as e_gem:
                if _is_quota_error(e_gem):
                    st.toast("Límite de Gemini (15 RPM) alcanzado. Esperando 65s...")
                    time.sleep(65)
                    response = client.models.generate_content(
                        model=MODEL_GEMINI, contents=prompt, config=config,
                    )
                    text = response.text
                else:
                    raise
            _accumulate("gemini", _count_tokens([{"role": "user", "content": prompt}], text))
            return text
        except Exception as e:
            raise e

    raise ValueError("No hay API Keys ni URL de 9Router configuradas.")