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
                    import requests
from bs4 import BeautifulSoup

# ... (código existente de tu app.py hasta llegar al botón de análisis)

if st.button("🧠 EJECUTAR ANÁLISIS IA"):
    with st.spinner("Leyendo documento oficial y analizando con Gemini..."):
        
        # 1. Obtenemos el link oficial guardado en la base de datos para esta resolución
        link_oficial = resolucion_seleccionada["fuente_oficial_url"]
        texto_a_analizar = resolucion_seleccionada["texto_completo"]
        
        # 2. Si el texto es el genérico del navegador, lo vamos a buscar a la web real en vivo
        if "Normativa extraída mediante navegación" in texto_a_analizar and link_oficial:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                respuesta_web = requests.get(link_oficial, headers=headers, timeout=10)
                if respuesta_web.status_code == 200:
                    soup_web = BeautifulSoup(respuesta_web.content, 'html.parser')
                    
                    # Buscamos los bloques de texto principales de la resolución en la página oficial
                    # (El Boletín Oficial suele estructurar el texto en párrafos o contenedores de contenido)
                    parrafos = soup_web.find_all(['p', 'div'], class_=['texto', 'contenido', 'aviso-detalle'])
                    texto_extraido = " ".join([p.get_text() for p in parrafos])
                    
                    if len(texto_extraido) > 100:
                        texto_a_analizar = texto_extraido
                        
                        # Opcional: Actualizamos el texto en Supabase para que ya quede guardado para siempre
                        supabase.table("resoluciones").update({"texto_completo": texto_extraido}).eq("id", resolucion_seleccionada["id"]).execute()
            except Exception as e:
                print(f"No se pudo extraer el texto en vivo, usando respaldo: {e}")

        # 3. Aquí es donde entra Gemini a procesar el texto real (el que ya tenías armado)
        # prompt_gemini = f"Analiza esta normativa: {texto_a_analizar} ..."
        # respuesta_ia = modelo_gemini.generate_content(prompt_gemini)
        
        st.success("¡Análisis completado con éxito!")
        # st.write(respuesta_ia.text)

# ==========================================
# SECCIÓN 2: INTELIGENCIA REGULATORIA (REPORTES)
# ==========================================
elif seccion == "📑 2. Inteligencia Regulatoria":
    st.title("📑 Reportes Ejecutivos Analizados")
    
    analizadas = [r for r in resoluciones if r['estado_clasificacion'] == 'Analizar']
    
    if not analizadas:
        st.warning("No hay normativas analizadas. Ve al Radar para analizar la primera.")
    else:
        opciones = {r['id']: f"{r['numero_resolucion']} - {r['titulo']}" for r in analizadas}
        seleccion_id = st.selectbox("📚 Seleccionar normativa para ver el reporte:", options=list(opciones.keys()), format_func=lambda x: opciones[x])
        
        res_actual = next(r for r in analizadas if r['id'] == seleccion_id)
        impactos = obtener_impactos(seleccion_id)
        
        # CABECERA DEL REPORTE
        with st.container(border=True):
            col_izq, col_der = st.columns([3, 1])
            with col_izq:
                st.subheader(res_actual['titulo'])
                st.caption(f"Emisor: {res_actual['organismo']} | Fecha: {res_actual['fecha_publicacion']}")
            with col_der:
                st.markdown(f"[🔗 Descargar / Ver Oficial]({res_actual['fuente_oficial_url']})")
                if st.button("Devolver al Radar"):
                    actualizar_estado(seleccion_id, "Pendiente")
                    st.rerun()
                    
            st.markdown("---")
            st.markdown("#### 📝 Resumen Ejecutivo")
            st.info(res_actual['resumen_ejecutivo'])
            st.markdown("#### ⚖️ Articulado Clave")
            st.write(res_actual['articulado_clave'])
            
        # SEMÁFORO DE IMPACTO SECTORIAL
        st.markdown("### 📊 Impacto Sectorial y Actores Clave")
        if impactos:
            for imp in impactos:
                color_border = "border: 2px solid #28a745;" if imp['tipo_impacto'] == 'Positivo' else "border: 2px solid #dc3545;" if imp['tipo_impacto'] == 'Negativo' else "border: 2px solid #ffc107;"
                icono = "🟢" if imp['tipo_impacto'] == 'Positivo' else "🔴" if imp['tipo_impacto'] == 'Negativo' else "🟡"
                
                with st.container(border=True):
                    st.markdown(f"#### {icono} Industria: {imp['industria']}")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tipo de Impacto", imp['tipo_impacto'])
                    c2.metric("Nivel de Severidad", imp['nivel_severidad'])
                    
                    st.write(f"**Análisis Estratégico:** {imp['descripcion_impacto']}")
                    st.markdown("---")
                    
                    c_actores1, c_actores2 = st.columns(2)
                    with c_actores1:
                        st.markdown(f"🏢 **Empresas de Interés:**\n{imp['empresas_afectadas']}")
                    with c_actores2:
                        st.markdown(f"🏛️ **Cámaras/Entidades:**\n{imp['camaras_representativas']}")

# ==========================================
# SECCIÓN 3: MONITOR DE INDUSTRIA (DATOS)
# ==========================================
elif seccion == "📈 3. Monitor de Industria":
    st.title("📈 Monitor de Industria")
    st.markdown("Impacto de las resoluciones cruzado con datos de mercado reales.")
    st.info("💡 En esta fase, los gráficos muestran estructuras simuladas para visualizar dónde conectaremos las APIs del BCRA, INDEC y Yahoo Finance.")
    
    # Simulación de un gráfico financiero sectorial
    st.markdown("### Rendimiento del Merval: Sector Tecnológico vs Mercado")
    st.caption("Proyección de impacto ante beneficios fiscales (Datos ilustrativos)")
    
    # Generamos datos visuales de prueba para mostrar capacidad
    fechas = pd.date_range("2026-07-01", periods=30)
    datos_simulados = pd.DataFrame({
        "Sector Tecnología (Globant/MELI)": np.random.randn(30).cumsum() + 100,
        "Índice Merval (Promedio)": (np.random.randn(30) * 0.5).cumsum() + 100
    }, index=fechas)
    
    st.line_chart(datos_simulados, height=350)
    
    st.markdown("---")
    st.markdown("### Próximas integraciones programadas:")
    st.markdown("- **API BCRA:** Tipo de Cambio y Tasa de Política Monetaria en tiempo real.")
    st.markdown("- **API Yahoo Finance:** Variación intradiaria de los tickers mencionados en la Sección 2.")
