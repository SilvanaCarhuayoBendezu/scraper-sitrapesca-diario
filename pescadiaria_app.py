# pescadiaria_app.py
from datetime import datetime
import os, time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ========= CONFIGURACIÓN DE FECHAS DE INICIO Y FIN =========
# Ejemplo:
# fecha_inicio = '25/04/2025' + " 00:00"
# fecha_fin = fecha_inicio[:10] + " " + str(datetime.now().hour) + ":" + f"{datetime.now().minute:02d}"

fecha_inicio = os.getenv("SITRAP_FECHA_INICIO", "25/04/2025 00:00")
if "SITRAP_FECHA_FIN" in os.environ:
    fecha_fin = os.environ["SITRAP_FECHA_FIN"]
else:
    # Usa el formato solicitado: mismo día que inicio, hora actual (HH:MM)
    hhmm = f"{datetime.now().hour}:{datetime.now().minute:02d}"
    fecha_fin = f"{fecha_inicio[:10]} {hhmm}"

# ========= DESCARGAS =========
DOWNLOAD_DIR = os.path.abspath(os.environ.get("DOWNLOAD_DIR", "./downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def build_driver(headless: bool = True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    try:
        # Permitir descargas en modo headless
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass
    return driver

def login_and_open_app(driver, ruc: str, doc: str, clave: str, card_index: int):
    url = "https://sistemas.produce.gob.pe/#/administrados"
    driver.get(url)

    # Selector de tipo de login (valor "2")
    select_el = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div/form/select"))
    )
    Select(select_el).select_by_value("2")

    # Campos (mismos XPATH que usabas)
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/form/div[2]/input'))
    ).send_keys(ruc, Keys.ENTER)

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/form/div[4]/input'))
    ).send_keys(doc, Keys.ENTER)

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/form/div[6]/input'))
    ).send_keys(clave, Keys.ENTER)

    # Espera que desaparezca el formulario de login (si aplica)
    try:
        WebDriverWait(driver, 60).until(
            EC.invisibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/form'))
        )
        print("✔ Login completado.")
    except Exception:
        print("El formulario no desapareció; continúo.")

    # Cierra modal si existe
    try:
        driver.execute_script("document.querySelector('.modal-dialog .btn-primary').click();")
    except Exception:
        pass

    # Abrir tarjeta SITRAPESCA (usa índice variable)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"#ng-view > div > div > div.row > div:nth-child({card_index}) > div > a"))
    )
    driver.execute_script(f"document.querySelector('#ng-view > div > div > div.row > div:nth-child({card_index}) > div > a').click();")

def open_faenas_y_calas(driver):
    # Espera navegación del menú superior
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/div[1]/nav/div/div[2]/ul[1]/li[8]/a'))
    )
    # Dropdown posición 6 → "Faenas y Calas"
    dropdown = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "(//ul[@class='nav navbar-nav']/li[contains(@class, 'dropdown')])[6]"))
    )
    dropdown.click()

    menu_option = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.LINK_TEXT, "Faenas y Calas"))
    )
    menu_option.click()

    WebDriverWait(driver, 15).until(EC.url_contains("FaenasCalas"))

def set_checkboxes_and_csv(driver):
    # Marca Faenas / Calas / Tallas
    for css in [
        "input[type='checkbox'][data-bind='checked: Model.ListadoFaenas']",
        "input[type='checkbox'][data-bind='checked: Model.ListadoCalas']",
        "input[type='checkbox'][data-bind='checked: Model.ListadoComposicionTallas']",
    ]:
        cb = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        if not cb.is_selected():
            cb.click()

    # Seleccionar **CSV** (nuevo tipo de selección)
    radio_csv = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='radio' and @id='radio3' and @value='3' and @data-bind='checked:Model.TipoFormato']"))
    )
    if not radio_csv.is_selected():
        radio_csv.click()

def set_date_range(driver, inicio: str, fin: str):
    # Fecha inicio
    inp_ini = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaInicio']"))
    )
    inp_ini.clear()
    inp_ini.send_keys(inicio)

    # Fecha fin
    inp_fin = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaFin']"))
    )
    inp_fin.clear()
    inp_fin.send_keys(fin)

def generar_reporte(driver):
    print(f"Descargando CSVs entre: {fecha_inicio} → {fecha_fin}")
    btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-bind='click: fnVerReporte']"))
    )
    btn.click()
    # Espera básica; si quieres, cambia a espera activa por archivo en DOWNLOAD_DIR
    time.sleep(30)

def run_company(nombre: str, ruc: str, doc: str, clave: str, card_index: int):
    print(f"\n=== Iniciando Descarga SITRAPESCA - {nombre} ===")
    driver = build_driver(headless=True)  # en Actions, mejor headless
    try:
        login_and_open_app(driver, ruc=ruc, doc=doc, clave=clave, card_index=card_index)
        open_faenas_y_calas(driver)
        set_checkboxes_and_csv(driver)
        set_date_range(driver, fecha_inicio, fecha_fin)
        generar_reporte(driver)
    finally:
        driver.quit()
        print(f"✔ {nombre}: proceso finalizado. Archivos en {DOWNLOAD_DIR}")

if __name__ == "__main__":
    # ===== CREDENCIALES COMO ENV VARS =====
    # Colócalas como Secrets → “Actions secrets” y en el workflow pasas env:
    # EXALMAR
    exalmar_ruc   = os.getenv("EXALMAR_RUC",   "20380336384")
    exalmar_doc   = os.getenv("EXALMAR_DOC",   "21814871")
    exalmar_clave = os.getenv("EXALMAR_CLAVE", "t6VX3Riy&")
    # ULTRAMAR
    ultramar_ruc   = os.getenv("ULTRAMAR_RUC",   "20538051081")
    ultramar_doc   = os.getenv("ULTRAMAR_DOC",   "40621802")
    ultramar_clave = os.getenv("ULTRAMAR_CLAVE", "Pesaa.2024")
    # CENTINELA
    centinela_ruc   = os.getenv("CENTINELA_RUC",   "20278966004")
    centinela_doc   = os.getenv("CENTINELA_DOC",   "32957283")
    centinela_clave = os.getenv("CENTINELA_CLAVE", "Medina123%")

    # ===== LISTADO DE EMPRESAS =====
    empresas = [
        # (nombre, ruc, doc, clave, card_index_en_dashboard)
        ("EXALMAR",  exalmar_ruc,  exalmar_doc,  exalmar_clave,  7),
        ("ULTRAMAR", ultramar_ruc, ultramar_doc, ultramar_clave, 8),
        #("CENTINELA", centinela_ruc, centinela_doc, centinela_clave, 9),
    ]

    for (nombre, ruc, doc, clave, card_idx) in empresas:
        run_company(nombre, ruc, doc, clave, card_idx)

    print(f"\n✅ Descargas finalizadas. Revisa: {DOWNLOAD_DIR}")
