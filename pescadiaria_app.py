# pescadiaria_app.py

from datetime import datetime
import os, time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#fecha_hoy = datetime.now().strftime("%d/%m/%Y") + " 00:00"
#fecha_hoy = '25/04/2025 00:00'

fecha_inicio = '25/04/2025' + " 00:00"
fecha_fin = fecha_inicio[:10] + " " + str(datetime.now().hour) + ":" + f"{datetime.now().minute:02d}"

DOWNLOAD_DIR = os.path.abspath(os.environ.get("DOWNLOAD_DIR", "./downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def build_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari')

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass
    return driver

def run_sitrap(razon_social_val, ruc_val, clave_val, card_index):
    print(f"Iniciando Descarga XLSX SITRAPESCA - card {card_index}")
    driver = build_driver()
    url = "https://sistemas.produce.gob.pe/#/administrados"
    driver.get(url)

    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div/form/select")))
    Select(driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div/form/select")).select_by_value("2")

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[1]/div/div/form/div[2]/input'))).send_keys(razon_social_val, Keys.ENTER)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[1]/div/div/form/div[4]/input'))).send_keys(ruc_val, Keys.ENTER)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[1]/div/div/form/div[6]/input'))).send_keys(clave_val, Keys.ENTER)

    try:
        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/form')))
    except Exception:
        print("El formulario no desapareció; continúo igual.")

    try:
        driver.execute_script("document.querySelector('.modal-dialog .btn-primary').click();")
    except Exception:
        pass

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"#ng-view > div > div > div.row > div:nth-child({card_index}) > div > a")))
    driver.execute_script(f"document.querySelector('#ng-view > div > div > div.row > div:nth-child({card_index}) > div > a').click();")

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[1]/nav/div/div[2]/ul[1]/li[8]/a')))

    dropdown = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "(//ul[@class='nav navbar-nav']/li[contains(@class, 'dropdown')])[6]")))
    dropdown.click()
    menu_option = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.LINK_TEXT, "Faenas y Calas")))
    menu_option.click()
    WebDriverWait(driver, 10).until(EC.url_contains("FaenasCalas"))

    for css in [
        "input[type='checkbox'][data-bind='checked: Model.ListadoFaenas']",
        "input[type='checkbox'][data-bind='checked: Model.ListadoCalas']",
        "input[type='checkbox'][data-bind='checked: Model.ListadoComposicionTallas']"
    ]:
        cb = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        if not cb.is_selected():
            cb.click()

    radio = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='radio' and @id='radio2' and @value='1' and @data-bind='checked:Model.TipoFormato']")))
    if not radio.is_selected():
        radio.click()

    input_fecha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaInicio']")))
    input_fecha.clear()
    #input_fecha.send_keys(fecha_hoy)
    input_fecha.send_keys(fecha_inicio)
    print(f"Descargando archivos del día: {fecha_inicio}")

    end_fecha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-bind='value: Model.FechaFin']")))
    end_fecha.clear()
    end_fecha.send_keys(fecha_fin)
    print(f"Descargando archivos del día: {end_fecha}")
    

    boton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-bind='click: fnVerReporte']")))
    boton.click()

    time.sleep(25)  # espera básica a la descarga
    driver.quit()

if __name__ == "__main__":
    run_sitrap(razon_social_val="20380336384",  ruc_val="21814871", clave_val="t6VX3Riy&",  card_index=7)
    run_sitrap(razon_social_val="20538051081", ruc_val="40621802", clave_val="Pesaa.2024", card_index=8)
    run_sitrap(razon_social_val="20278966004", ruc_val="32957283", clave_val="Medina123%", card_index=9)
    print(f"Descargas en: {DOWNLOAD_DIR}")



