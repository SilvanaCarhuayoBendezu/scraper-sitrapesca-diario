# pescadiaria_app.py
from datetime import datetime
import os, time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ========= CONFIGURACIÓN DE FECHAS DE INICIO Y FIN =========
fecha_inicio = os.getenv("SITRAP_FECHA_INICIO", "25/04/2025 00:00")
if "SITRAP_FECHA_FIN" in os.environ:
    fecha_fin = os.environ["SITRAP_FECHA_FIN"]
else:
    hhmm = f"{datetime.now().hour}:{datetime.now().minute:02d}"
    fecha_fin = f"{fecha_inicio[:10]} {hhmm}"

# ========= DESCARGAS =========
DOWNLOAD_DIR = os.path.abspath(os.environ.get("DOWNLOAD_DIR", "./downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def build_driver(headless: bool = True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    # Idioma: asegura que el DOM llegue en ES como en tu PC
    options.add_argument("--lang=es-419")
    options.add_argument("Accept-Language=es-419,es;q=0.9,en;q=0.8")
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
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass
    return driver

def js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", element)

def type_slow(el, text):
    el.click()
    el.clear()
    for ch in text:
        el.send_keys(ch)
        time.sleep(0.02)

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

    # Cierra modal si existe (simple)
    try:
        driver.execute_script("document.querySelector('.modal-dialog .btn-primary, .modal-footer .btn-primary, .modal-footer .btn')?.click();")
    except Exception:
        pass

    # Abrir tarjeta SITRAPESCA (usa índice variable) con JS click
    card_sel = f"#ng-view > div > div > div.row > div:nth-child({card_index}) > div > a"
    el = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, card_sel))
    )
    js_click(driver, el)

def open_faenas_y_calas(driver):
    # Espera navegación del menú superior
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/div[1]/nav/div/div[2]/ul[1]/li[8]/a'))
    )
    # Dropdown posición 6 → "Faenas y Calas" (JS click)
    dropdown = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "(//ul[@class='nav navbar-nav']/li[contains(@class, 'dropdown')])[6]"))
    )
    js_click(driver, dropdown)

    menu_option = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Faenas y Calas"))
    )
    js_click(driver, menu_option)

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
            js_click(driver, cb)

    # Seleccionar **CSV** (nuevo tipo de selección)
    radio_csv = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='radio' and @id='radio3' and @value='3' and @data-bind='checked:Model.TipoFormato']"))
    )
    if not radio_csv.is_selected():
        js_click(driver, radio_csv)

def set_date_range(driver, inicio: str, fin: str):
    inp_ini = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaInicio']"))
    )
    type_slow(inp_ini, inicio)

    inp_fin = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaFin']"))
    )
    type_slow(inp_fin, fin)

def generar_reporte(driver):
    print(f"Descargando CSVs entre: {fecha_inicio} → {fecha_fin}")
    btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-bind='click: fnVerReporte']"))
    )
    js_click(driver, btn)
    time.sleep(30)  # espera simple

def run_company(nombre: str, ruc: str, doc: str, clave: str, card_index: int):
    print(f"\n=== Iniciando Descarga SITRAPESCA - {nombre} ===")
    driver = build_driver(headless=True)
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
    exalmar_ruc   = os.getenv("EXALMAR_RUC",   "20380336384")
    exalmar_doc   = os.getenv("EXALMAR_DOC",   "21814871")
    exalmar_clave = os.getenv("EXALMAR_CLAVE", "t6VX3Riy&")

    ultramar_ruc   = os.getenv("ULTRAMAR_RUC",   "20538051081")
    ultramar_doc   = os.getenv("ULTRAMAR_DOC",   "40621802")
    ultramar_clave = os.getenv("ULTRAMAR_CLAVE", "Pesaa.2024")

    centinela_ruc   = os.getenv("CENTINELA_RUC",   "20278966004")
    centinela_doc   = os.getenv("CENTINELA_DOC",   "32957283")
    centinela_clave = os.getenv("CENTINELA_CLAVE", "Medina123%")

    empresas = [
        ("EXALMAR",  exalmar_ruc,  exalmar_doc,  exalmar_clave,  7),
        ("ULTRAMAR", ultramar_ruc, ultramar_doc, ultramar_clave, 8),
        # ("CENTINELA", centinela_ruc, centinela_doc, centinela_clave, 9),
    ]

    for (nombre, ruc, doc, clave, card_idx) in empresas:
        run_company(nombre, ruc, doc, clave, card_idx)

    print(f"\nDescargas finalizadas. Revisa: {DOWNLOAD_DIR}")

