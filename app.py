import streamlit as st
from supabase import create_client, Client
from google import genai
import json
import pandas as pd
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA (SaaS Profesional) ---
st.set_page_config(page_title="Portal de Inteligencia Regulatoria", page_icon="🏛️", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].rstrip('/')
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception:
    st.error("Error de conexión. Verifica los Secrets.")
    st.stop()

# --- FUNCIONES DE BASE DE DATOS ---
def obtener_resoluciones():
    return supabase.table("resoluciones").select("*").order("fecha_publicacion", desc=True).execute().data

def obtener_impactos(resolucion_id):
    return supabase.table("impactos_industria").select("*").eq("resolucion_id", resolucion_id).execute().data

def actualizar_estado(resolucion_id, nuevo_estado):
    supabase.table("resoluciones").update({"estado_clasificacion": nuevo_estado}).eq("id", resolucion_id).execute()
    st.cache_data.clear()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.title("🏛️ Radar Regulatorio")
st.sidebar.markdown("---")
seccion = st.sidebar.radio("Navegación", [
    "📡 1. El Radar (Bandeja de Entrada)",
    "📑 2. Inteligencia Regulatoria",
    "📈 3. Monitor de Industria"
])
st.sidebar.markdown("---")
st.sidebar.caption("Desarrollado con Gemini IA & Supabase")

# Cargamos todas las resoluciones
resoluciones = obtener_resoluciones()

# ==========================================
# SECCIÓN 1: EL RADAR (FILTRO Y EJECUCIÓN IA)
# ==========================================
if seccion == "📡 1. El Radar (Bandeja de Entrada)":
    st.title("📡 Radar de Resoluciones Oficiales")
    st.markdown("Clasifica las nuevas normativas y ejecuta la IA solo en las relevantes.")
    
    # Filtro rápido superior
    df = pd.DataFrame(resoluciones)
    if not df.empty:
        # Mostramos un panel resumen con métricas
        col_pendientes = len(df[df['estado_clasificacion'] == 'Pendiente'])
        col_analizadas = len(df[df['estado_clasificacion'] == 'Analizar'])
        col_descartadas = len(df[df['estado_clasificacion'] == 'Descartado'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("⚪ Pendientes de Revisión", col_pendientes)
        c2.metric("🟢 Analizadas (En Panel)", col_analizadas)
        c3.metric("🔴 Descartadas", col_descartadas)
        st.markdown("---")
        
        # Selector de resolución pendiente
        pendientes = [r for r in resoluciones if r['estado_clasificacion'] == 'Pendiente']
        if pendientes:
            st.subheader("Bandeja de Entrada")
            # Diccionario para que el selectbox muestre algo lindo
            opciones = {r['id']: f"{r['fecha_publicacion']} | {r['numero_resolucion']} - {r['titulo']}" for r in pendientes}
            seleccion_id = st.selectbox("Seleccionar normativa a revisar:", options=list(opciones.keys()), format_func=lambda x: opciones[x])
            
            res_actual = next(r for r in pendientes if r['id'] == seleccion_id)
            
            # Tarjeta de lectura de la resolución
            with st.container(border=True):
                st.markdown(f"### {res_actual['titulo']}")
                st.markdown(f"**Organismo:** {res_actual['organismo']} | [🔗 Ver en Boletín Oficial]({res_actual['fuente_oficial_url']})")
                st.text_area("Texto Completo Original:", res_actual['texto_completo'], height=200, disabled=True)
                
                st.markdown("### Acción:")
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    if st.button("🔴 Descartar (Irrelevante)"):
                        actualizar_estado(seleccion_id, "Descartado")
                        st.rerun()
                
                with col_btn2:
                    if st.button("🧠 EJECUTAR ANÁLISIS IA", type="primary"):
                        with st.spinner("Procesando documento con Gemini. Generando métricas..."):
                            try:
                                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                                prompt = f"""
                                Eres un analista regulatorio. Analiza este texto legal y devuelve UNICAMENTE un JSON válido:
                                {{
                                    "resumen_ejecutivo": "Resumen claro de 3 líneas",
                                    "articulado_clave": "Puntos clave de la norma",
                                    "impactos": [
                                        {{
                                            "industria": "Nombre del sector",
                                            "tipo_impacto": "Positivo", 
                                            "nivel_severidad": "Alto",
                                            "descripcion_impacto": "por qué impacta",
                                            "empresas_afectadas": "ej: YPF, Globant",
                                            "camaras_representativas": "ej: UIA, CESSI"
                                        }}
                                    ]
                                }}
                                TEXTO: {res_actual['texto_completo']}
                                NOTA: tipo_impacto debe ser 'Positivo', 'Negativo' o 'Neutro'. nivel_severidad 'Alto', 'Medio' o 'Bajo'.
                                """
                                respuesta = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                                texto_json = respuesta.text.replace('```json', '').replace('
