import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from supabase import create_client, Client

def ejecutar_historial():
    # 1. Leer las contraseñas de GitHub Secrets
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: No se encontraron las credenciales de Supabase.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 2. Configuración
    DIAS_HACIA_ATRAS = 90
    palabras_clave = ["industria", "comercio", "tecnología", "impuesto", "aduana", "exportación", "importación", "energía", "pyme", "agro", "resolución general"]

    print(f"🚀 Iniciando el Robot Explorador. Buscando {DIAS_HACIA_ATRAS} días hacia atrás...\n")
    leyes_guardadas = 0
    fecha_actual = datetime.now()

    sesion = requests.Session()
    sesion.headers.update({'User-Agent': 'Mozilla/5.0'})

    for i in range(DIAS_HACIA_ATRAS):
        fecha_busqueda = fecha_actual - timedelta(days=i)
        fecha_str = fecha_busqueda.strftime('%Y%m%d')
        fecha_legible = fecha_busqueda.strftime('%Y-%m-%d')
        
        url_diaria = f"https://www.boletinoficial.gob.ar/rss/primera/{fecha_str}"
        
        try:
            respuesta = sesion.get(url_diaria, timeout=10)
            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.content, 'xml')
                items = soup.find_all('item')
                
                for item in items:
                    titulo = item.title.text if item.title else ""
                    link = item.link.text if item.link else ""
                    descripcion = item.description.text if item.description else ""
                    
                    texto_busqueda = (titulo + " " + descripcion).lower()
                    
                    if any(palabra in texto_busqueda for palabra in palabras_clave):
                        existe = supabase.table("resoluciones").select("id").eq("fuente_oficial_url", link).execute()
                        
                        if not existe.data:
                            titulo_limpio = titulo[:150] + "..." if len(titulo) > 150 else titulo
                            supabase.table("resoluciones").insert({
                                "numero_resolucion": "BO - " + fecha_legible,
                                "titulo": titulo_limpio,
                                "organismo": "Estado Nacional",
                                "fecha_publicacion": fecha_legible,
                                "texto_completo": descripcion,
                                "fuente_oficial_url": link,
                                "estado_clasificacion": "Pendiente"
                            }).execute()
                            
                            leyes_guardadas += 1
                            print(f"✅ Guardada: {titulo_limpio[:50]}...")
            
        except Exception as e:
            print(f"❌ Error en {fecha_legible}: {e}")
        
        # Pausa para no saturar al servidor
        time.sleep(2)

    print(f"\n🏁 ¡Misión Cumplida! Se guardaron {leyes_guardadas} normativas reales.")

if __name__ == "__main__":
    ejecutar_historial()
