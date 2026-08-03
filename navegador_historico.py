import os
import time
from datetime import datetime
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

def ejecutar_navegador():
    print("🤖 Iniciando Robot Navegador del Boletín Oficial...")
    
    # 1. Credenciales de Supabase
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: No se encontraron las credenciales de Supabase.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    palabras_clave = ["industria", "comercio", "tecnología", "impuesto", "aduana", "exportación", "importación", "energía", "pyme", "agro", "resolución", "decreto"]
    
    guardadas = 0

    with sync_playwright() as p:
        # Abrimos un navegador oculto (Chromium)
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        
        try:
            print("🌐 Navegando a la sección de búsqueda del Boletín Oficial...")
            # Entramos al buscador de la Sección Primera
            page.goto("https://www.boletinoficial.gob.ar/seccion/primera", timeout=60000)
            
            # Esperamos a que cargue la lista de publicaciones recientes
            page.wait_for_selector(".aviso-item, .item-aviso, h3, a", timeout=15000)
            
            # Extraemos todos los enlaces y títulos visibles en la portada actual
            elementos = page.locator("a").all()
            print(f"🔍 Se encontraron {len(elementos)} enlaces en la página. Analizando contenido...")
            
            for el in elementos:
                try:
                    titulo = el.inner_text().strip()
                    link = el.get_attribute("href")
                    
                    if titulo and link and len(titulo) > 20:
                        texto_busq = titulo.lower()
                        
                        # Si tiene alguna palabra clave de nuestro interés industrial/económico
                        if any(palabra in texto_busq for palabra in palabras_clave):
                            # Aseguramos que el link sea absoluto
                            if link.startswith("/"):
                                link = "https://www.boletinoficial.gob.ar" + link
                                
                            # Verificamos si ya existe en Supabase
                            existe = supabase.table("resoluciones").select("id").eq("fuente_oficial_url", link).execute()
                            
                            if not existe.data:
                                fecha_hoy = datetime.now().strftime('%Y-%m-%d')
                                
                                supabase.table("resoluciones").insert({
                                    "numero_resolucion": "BO - " + fecha_hoy,
                                    "titulo": titulo[:150],
                                    "organismo": "Boletín Oficial (Navegador)",
                                    "fecha_publicacion": fecha_hoy,
                                    "texto_completo": "Normativa extraída mediante navegación automatizada del Boletín Oficial.",
                                    "fuente_oficial_url": link,
                                    "estado_clasificacion": "Pendiente"
                                }).execute()
                                
                                guardadas += 1
                                print(f"   ✅ Guardada: {titulo[:60]}...")
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error durante la navegación web: {e}")
        finally:
            browser.close()

    print(f"\n🏁 ¡Navegación finalizada! Se guardaron {guardadas} resoluciones reales en tu Radar.")

if __name__ == "__main__":
    ejecutar_navegador()
