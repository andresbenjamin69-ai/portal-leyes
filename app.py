import streamlit as st
from supabase import create_client, Client
from google import genai

# Configuración inicial de la página
st.set_page_config(page_title="Inteligencia Regulatoria", page_icon="🏛️", layout="wide")

# Conexión a Supabase
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].rstrip('/')
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Por favor, configura tus Secrets en Streamlit Cloud.")
    st.stop()

# Funciones para traer datos de la base
@st.cache_data(ttl=60)
def cargar_resoluciones():
    respuesta = supabase.table("resoluciones").select("*").execute()
    return respuesta.data

@st.cache_data(ttl=60)
def cargar_impactos(resolucion_id):
    respuesta = supabase.table("impactos_industria").select("*").eq("resolucion_id", resolucion_id).execute()
    return respuesta.data

# Cargamos los datos
resoluciones = cargar_resoluciones()

# --- MENÚ LATERAL ---
st.sidebar.title("🏛️ Portal Regulatorio")
st.sidebar.markdown("---")

if not resoluciones:
    st.warning("No hay resoluciones cargadas en la base de datos.")
    st.stop()

# Selector global de la norma a analizar
nombres_leyes = {res['id']: f"{res['numero_resolucion']} - {res['organismo']}" for res in resoluciones}
ley_seleccionada_id = st.sidebar.selectbox("Seleccione la Norma a consultar:", options=list(nombres_leyes.keys()), format_func=lambda x: nombres_leyes[x])

ley_actual = next(res for res in resoluciones if res['id'] == ley_seleccionada_id)
impactos_actuales = cargar_impactos(ley_seleccionada_id)

seccion = st.sidebar.radio("Navegación", [
    "📑 1. Análisis de Resolución",
    "📊 2. Métricas de Impacto",
    "🌐 3. Monitor de Industria",
    "✨ 4. Analizar Nueva Ley (IA)"
])

# --- SECCIÓN 1: ANÁLISIS DE RESOLUCIÓN ---
if seccion == "📑 1. Análisis de Resolución":
    st.title("📑 Análisis de la Resolución")
    st.subheader(ley_actual['titulo'])
    
    col1, col2 = st.columns(2)
    col1.write(f"**Número:** {ley_actual['numero_resolucion']}")
    col1.write(f"**Organismo:** {ley_actual['organismo']}")
    col2.write(f"**Fecha de Publicación:** {ley_actual['fecha_publicacion']}")
    if ley_actual.get('fuente_oficial_url'):
        col2.write(f"[🔗 Ver en Boletín Oficial]({ley_actual['fuente_oficial_url']})")
        
    st.markdown("---")
    st.markdown("### 📝 Resumen Ejecutivo")
    st.info(ley_actual['resumen_ejecutivo'])
    
    st.markdown("### ⚖️ Articulado Clave")
    st.write(ley_actual['articulado_clave'])

# --- SECCIÓN 2: MÉTRICAS DE IMPACTO ---
elif seccion == "📊 2. Métricas de Impacto":
    st.title("📊 Métricas de Impacto Sectorial")
    st.markdown(f"**Impacto estimado para:** {ley_actual['numero_resolucion']}")
    st.markdown("---")
    
    if impactos_actuales:
        for impacto in impactos_actuales:
            # Semáforo de colores según el impacto
            if impacto['tipo_impacto'] == 'Positivo':
                color = "success"
                icono = "🟢"
            elif impacto['tipo_impacto'] == 'Negativo':
                color = "error"
                icono = "🔴"
            else:
                color = "warning"
                icono = "🟡"
                
            with st.container():
                st.subheader(f"{icono} Industria: {impacto['industria']}")
                col1, col2 = st.columns(2)
                col1.metric("Tipo de Impacto", impacto['tipo_impacto'])
                col2.metric("Severidad", impacto['nivel_severidad'])
                
                if color == "success":
                    st.success(f"**Descripción:** {impacto['descripcion_impacto']}")
                elif color == "error":
                    st.error(f"**Descripción:** {impacto['descripcion_impacto']}")
                else:
                    st.warning(f"**Descripción:** {impacto['descripcion_impacto']}")
                    
                st.markdown(f"**Posibles Consecuencias:** {impacto['posibles_consecuencias']}")
                st.markdown("---")
    else:
        st.write("Aún no se han generado métricas de impacto para esta resolución.")

# --- SECCIÓN 3: MONITOR DE INDUSTRIA ---
elif seccion == "🌐 3. Monitor de Industria":
    st.title("🌐 Monitor de Industria y Fuentes")
    st.markdown("Cruce de la normativa con datos reales de mercado e informes sectoriales.")
    st.markdown("---")
    
    if impactos_actuales:
        for impacto in impactos_actuales:
            with st.expander(f"Ver contexto para: {impacto['industria']}", expanded=True):
                st.write(f"🏢 **Fuente consultada:** {impacto['fuente_sectorial']}")
                st.write("📌 *Nota: En la siguiente fase, conectaremos este módulo a fuentes públicas (INDEC, Cámaras) para mostrar índices de precios y producción en tiempo real.*")
    else:
        st.write("No hay fuentes sectoriales asociadas a esta resolución.")

# --- SECCIÓN 4: ANALIZAR CON IA (GEMINI) ---
elif seccion == "✨ 4. Analizar Nueva Ley (IA)":
    st.title("✨ Analizar Nueva Ley con Gemini API")
    st.markdown("Pegue el texto crudo de un proyecto de ley o resolución para que Gemini extraiga los impactos y genere el resumen.")
    
    texto_ley = st.text_area("Texto de la Norma:", height=200)
    
    if st.button("🧠 Analizar con IA"):
        if not texto_ley:
            st.warning("Por favor, ingresa el texto de la ley.")
        else:
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                st.info("Consultando a Gemini... Esto puede demorar unos segundos.")
                
                # Prompt estructurado para la IA
                prompt = f"""
                Actúa como un analista regulatorio experto. Analiza el siguiente texto de una resolución y devuelve:
                1. Un resumen ejecutivo breve (máximo 3 párrafos).
                2. Enumera los 2 impactos más importantes que tendrá en las industrias.
                
                TEXTO:
                {texto_ley}
                """
                
                respuesta_ia = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                st.success("¡Análisis Completado!")
                st.markdown("### Resultado:")
                st.write(respuesta_ia.text)
                
            except Exception as e:
                st.error(f"Error al conectar con Gemini: {e}")
