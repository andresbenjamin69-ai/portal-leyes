import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from supabase import create_client, Client

def ejecutar_robot():
    print("🤖 Iniciando escaneo del Boletín Oficial...")
    
    # 1. Leer las contraseñas desde el entorno seguro (GitHub Secrets)
    url_supabase = os.environ.get("SUPABASE_URL")
    key_supabase = os.environ.get("SUPABASE_KEY")
    
    if not url_supabase or not key_supabase:
        print("❌ Error: No se encontraron las credenciales de Supabase.")
        return

    supabase: Client = create_client(url_supabase, key_supabase)
    
    # 2. Conectar al RSS oficial de Leyes y Decretos de Argentina
    rss_url = "https://www.boletinoficial.gob.ar/rss/primera"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        respuesta = requests.get(rss_url, headers=headers, timeout=15)
        root = ET.fromstring(respuesta.content)
    except Exception as e:
        print(f"❌ Error al conectar con el Boletín Oficial: {e}")
        return

    # 3. Nuestro filtro de control: Palabras clave de interés industrial
    palabras_clave = ["industria", "comercio", "tecnología", "impuesto", "aduana", "exportación", "importación", "energía", "pyme", "agro"]
    nuevas_leyes = 0
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')

    # 4. Revisar cada publicación de hoy
    for item in root.findall('./channel/item'):
        titulo = item.find('title').text
        link = item.find('link').text
        descripcion = item.find('description').text
        
        texto_busqueda = (titulo + " " + descripcion).lower()
        
        # Si la resolución tiene alguna de nuestras palabras clave...
        if any(palabra in texto_busqueda for palabra in palabras_clave):
            
            # Verificamos que no la hayamos guardado antes (buscando por el link)
            existe = supabase.table("resoluciones").select("id").eq("fuente_oficial_url", link).execute()
            
            if not existe.data:
                print(f"✅ Nueva normativa detectada: {titulo[:50]}...")
                
                # La insertamos en el Radar como 'Pendiente'
                supabase.table("resoluciones").insert({
                    "numero_resolucion": "BO - " + fecha_hoy,
                    "titulo": titulo,
                    "organismo": "Boletín Oficial de la República Argentina",
                    "fecha_publicacion": fecha_hoy,
                    "texto_completo": descripcion,
                    "fuente_oficial_url": link,
                    "estado_clasificacion": "Pendiente"
                }).execute()
                
                nuevas_leyes += 1

    print(f"🏁 Escaneo finalizado. Se agregaron {nuevas_leyes} resoluciones a tu Radar.")

if __name__ == "__main__":
    ejecutar_robot()
