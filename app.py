import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Radar de Resoluciones y Impacto",
    page_icon="⚖️",
    layout="wide"
)

# --- CONEXIÓN A SUPABASE Y GEMINI ---
# Intentamos leer de los secrets de Streamlit Cloud
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    # Si estás probando local o faltan secrets, podés poner tus claves de respaldo aquí
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Inicializar clientes
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
modelo_gemini = genai.GenerativeModel('gemini-2.5-flash')
# --- TÍTULO PRINCIPAL ---
st.title("⚖️ Radar Inteligente de Normativas y Resoluciones")
st.markdown("Monitoreo en tiempo real del Boletín Oficial con análisis de impacto mediante Inteligencia Artificial.")

# --- CARGAR DATOS DE SUPABASE ---
try:
    respuesta = supabase.table("resoluciones").select("*").order("fecha_publicacion", desc=True).execute()
    resoluciones = respuesta.data
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    resoluciones = []

if not resoluciones:
    st.warning("⚠️ No hay resoluciones pendientes en este momento en el Radar.")
else:
    # --- INTERFAZ: SELECCIÓN DE RESOLUCIÓN ---
    st.sidebar.header("📂 Bandeja de Entrada")
    nombres_resoluciones = [f"{r['numero_resolucion']} - {r['titulo'][:50]}..." for r in resoluciones]
    
    seleccion = st.sidebar.selectbox("Seleccioná una normativa para analizar:", nombres_resoluciones)
    
    # Encontrar la resolución seleccionada
    indice = nombres_resoluciones.index(seleccion)
    resolucion_seleccionada = resoluciones[indice]
    
    # --- CUERPO PRINCIPAL ---
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Detalle de la Normativa")
        st.write(f"**Organismo:** {resolucion_seleccionada.get('organismo', 'N/D')}")
        st.write(f"**Fecha de Publicación:** {resolucion_seleccionada.get('fecha_publicacion', 'N/D')}")
        st.markdown(f"**Enlace Oficial:** [Ver en Boletín Oficial]({resolucion_seleccionada.get('fuente_oficial_url', '#')})")
        
        with st.expander("Ver título completo"):
            st.write(resolucion_seleccionada.get('titulo', ''))
            
        with st.expander("Ver texto actual en base de datos"):
            st.write(resolucion_seleccionada.get('texto_completo', ''))
            
    with col2:
        st.subheader("🧠 Análisis de Impacto IA")
        
        if st.button("🚀 EJECUTAR ANÁLISIS IA", type="primary"):
            with st.spinner("Extrayendo texto legal oficial y procesando con Gemini..."):
                
                link_oficial = resolucion_seleccionada.get("fuente_oficial_url")
                texto_a_analizar = resolucion_seleccionada.get("texto_completo", "")
                
                # Si el texto es el genérico del navegador, lo buscamos en vivo en la web oficial
                if "Normativa extraída mediante navegación" in texto_a_analizar and link_oficial:
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        respuesta_web = requests.get(link_oficial, headers=headers, timeout=10)
                        if respuesta_web.status_code == 200:
                            soup_web = BeautifulSoup(respuesta_web.content, 'html.parser')
                            parrafos = soup_web.find_all(['p', 'div'])
                            texto_extraido = " ".join([p.get_text() for p in parrafos if p.get_text()])
                            
                            if len(texto_extraido) > 100:
                                texto_a_analizar = texto_extraido
                                # Actualizamos en Supabase para futuras consultas
                                supabase.table("resoluciones").update({"texto_completo": texto_extraido}).eq("id", resolucion_seleccionada["id"]).execute()
                    except Exception as e:
                        print(f"Aviso de extracción web: {e}")

                # Generar análisis con Gemini
                prompt = f"""
                Actúa como un Consultor Senior de Empresas y experto en cumplimiento legal en Argentina.
                Analiza la siguiente normativa del Boletín Oficial y provee:
                1. Resumen ejecutivo del impacto principal.
                2. Sectores económicos beneficiados y perjudicados.
                3. Riesgos u obligaciones críticas para las empresas.
                
                Texto de la normativa:
                {texto_a_analizar[:10000]}
                """
                
                try:
                    analisis = modelo_gemini.generate_content(prompt)
                    st.success("¡Análisis completado con éxito!")
                    st.markdown(analisis.text)
                except Exception as e:
                    st.error(f"Error al generar el análisis con la IA: {e}")
