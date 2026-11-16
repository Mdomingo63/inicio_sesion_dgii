#!/usr/bin/env python3
"""
Automatización del login en la Oficina Virtual (OFV) de la DGII - República Dominicana.

Flujo:
  1. Llena Usuario + Clave y hace clic en "Entrar" (BtnAceptar).
  2. Espera el campo "Tarjeta" (#ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken).
  3. Lee su atributo data-original-title ("Favor introducir el código número: 19 de su tarjeta"),
     extrae la posición, busca el código en tarjeta_dgii.json, lo escribe y envía el formulario.

Credenciales: variables de entorno o archivo .env (NUNCA en el código).
Uso:
    python login_dgii.py            # navegador visible
    python login_dgii.py --headless # sin ventana
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

# --- Configuración -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
URL_LOGIN = "https://www.dgii.gov.do/OFV/login.aspx"
DIR_CAPTURAS = BASE_DIR / "capturas"

# Selectores (con alternativas por si la DGII cambia ligeramente los IDs)
SELECTORES_USUARIO = [
    "#ctl00_ContentPlaceHolder1_txtUsuario",
    "#ctl00_ContentPlaceHolder1_txtUserName",
    "input[id*='ContentPlaceHolder1'][id*='Usuario' i]",
    "input[id*='ContentPlaceHolder1'][id*='User' i]",
    "input[type='text'][name*='ContentPlaceHolder1']",
]
SELECTORES_CLAVE = [
    "#ctl00_ContentPlaceHolder1_txtPassword",
    "#ctl00_ContentPlaceHolder1_txtClave",
    "input[type='password'][id*='ContentPlaceHolder1']",
    "input[type='password']",
]
XPATH_BOTON_ENTRAR = '//*[@id="ctl00_ContentPlaceHolder1_BtnAceptar"]'
SELECTOR_TARJETA = "#ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken"

# Regex: "Favor introducir el código número: 19 de su tarjeta"
REGEX_POSICION = re.compile(r"n[uú]mero\s*:?\s*(\d{1,3})", re.IGNORECASE)
REGEX_POSICION_RESPALDO = re.compile(r"(\d{1,3})")

TIMEOUT_MS = 30_000


class ErrorLoginDGII(Exception):
    """Error controlado del proceso de login (mensaje legible en español)."""


# --- Utilidades --------------------------------------------------------------
def log(mensaje: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {mensaje}", flush=True)


async def captura(page: Page, nombre: str) -> None:
    """Guarda un screenshot en capturas/ para diagnóstico."""
    DIR_CAPTURAS.mkdir(exist_ok=True)
    ruta = DIR_CAPTURAS / f"{datetime.now():%Y%m%d_%H%M%S}_{nombre}.png"
    try:
        await page.screenshot(path=str(ruta), full_page=True)
        log(f"📸 Captura guardada: {ruta.relative_to(BASE_DIR)}")
    except PlaywrightError as e:
        log(f"⚠️  No se pudo guardar la captura '{nombre}': {e}")


def cargar_configuracion() -> tuple[str, str, Path]:
    load_dotenv(BASE_DIR / ".env")
    usuario = os.getenv("DGII_USUARIO", "").strip()
    clave = os.getenv("DGII_CLAVE", "")
    ruta_tarjeta = Path(os.getenv("DGII_TARJETA_JSON", "tarjeta_dgii.json")).expanduser()
    if not ruta_tarjeta.is_absolute():
        ruta_tarjeta = BASE_DIR / ruta_tarjeta

    if not usuario or not clave:
        raise ErrorLoginDGII(
            "Faltan credenciales. Defina DGII_USUARIO y DGII_CLAVE en el archivo .env "
            "(copie .env.example a .env) o como variables de entorno."
        )
    return usuario, clave, ruta_tarjeta


def cargar_tarjeta(ruta: Path) -> dict[str, str]:
    if not ruta.exists():
        raise ErrorLoginDGII(f"No se encontró el archivo de tarjeta: {ruta}")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErrorLoginDGII(f"El archivo {ruta.name} no es un JSON válido: {e}") from e
    if not isinstance(datos, dict) or not datos:
        raise ErrorLoginDGII(f"{ruta.name} debe ser un objeto JSON {{\"1\": \"codigo\", ...}}.")

    # Normalizar claves ("01" -> "1") y valores a texto
    tarjeta = {str(int(k)): str(v).strip() for k, v in datos.items() if str(k).strip().isdigit()}

    # Aviso de permisos inseguros (solo en sistemas POSIX)
    if os.name == "posix" and (ruta.stat().st_mode & 0o077):
        log(f"⚠️  Permisos inseguros en {ruta.name}. Recomendado: chmod 600 {ruta.name}")
    return tarjeta


def extraer_posicion(texto: str) -> int:
    """Extrae el número de posición del texto del tooltip."""
    coincidencia = REGEX_POSICION.search(texto) or REGEX_POSICION_RESPALDO.search(texto)
    if not coincidencia:
        raise ErrorLoginDGII(f"No se pudo extraer el número de posición del texto: '{texto}'")
    return int(coincidencia.group(1))


def obtener_codigo(tarjeta: dict[str, str], posicion: int) -> str:
    codigo = tarjeta.get(str(posicion))
    if codigo is None:
        raise ErrorLoginDGII(f"La posición {posicion} no existe en el archivo de tarjeta.")
    if not codigo or set(codigo.upper()) == {"X"}:
        raise ErrorLoginDGII(
            f"La posición {posicion} todavía tiene el valor de ejemplo ('{codigo}'). "
            "Complete tarjeta_dgii.json con los códigos de su tarjeta física."
        )
    return codigo


async def primer_selector_visible(page: Page, selectores: list[str], descripcion: str):
    for selector in selectores:
        loc = page.locator(selector).first
        try:
            if await loc.count() and await loc.is_visible():
                return loc
        except PlaywrightError:
            continue
    raise ErrorLoginDGII(f"No se encontró el campo '{descripcion}' en la página de login.")


async def leer_texto_tooltip(page: Page) -> str:
    """Lee data-original-title del campo Tarjeta (con hover y alternativas por si viene vacío)."""
    campo = page.locator(SELECTOR_TARJETA)
    for intento in range(10):
        texto = await campo.get_attribute("data-original-title")
        if not texto:
            texto = await campo.get_attribute("title")
        if not texto:
            # El tooltip de Bootstrap a veces se inicializa al pasar el mouse
            try:
                await campo.hover(timeout=2_000)
            except PlaywrightError:
                pass
            # Respaldo: tooltip visible (sin depender de su ID dinámico)
            visible = page.locator(".tooltip .tooltip-inner").first
            if await visible.count():
                texto = (await visible.inner_text()).strip()
        if texto:
            return texto.strip()
        await page.wait_for_timeout(500)
    raise ErrorLoginDGII("El campo Tarjeta no tiene el texto 'data-original-title' con la posición solicitada.")


async def detectar_error_en_pagina(page: Page) -> str | None:
    """Busca mensajes de error visibles típicos de la OFV."""
    candidatos = page.locator(
        "[id*='lblMensaje'], [id*='lblError'], .alert-danger, .error, .validation-summary-errors"
    )
    for i in range(await candidatos.count()):
        el = candidatos.nth(i)
        try:
            if await el.is_visible():
                texto = (await el.inner_text()).strip()
                if texto:
                    return texto
        except PlaywrightError:
            continue
    return None


# --- Flujo principal ---------------------------------------------------------
async def login(headless: bool) -> int:
    usuario, clave, ruta_tarjeta = cargar_configuracion()
    tarjeta = cargar_tarjeta(ruta_tarjeta)
    log(f"Tarjeta cargada: {len(tarjeta)} posiciones desde {ruta_tarjeta.name}")

    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=headless)
        contexto = await navegador.new_context(locale="es-DO", viewport={"width": 1280, "height": 900})
        page = await contexto.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        try:
            # ---------------- Paso 0: abrir la página ----------------
            log(f"Abriendo {URL_LOGIN} ...")
            await page.goto(URL_LOGIN, wait_until="domcontentloaded")
            await captura(page, "01_pagina_login")

            # ---------------- Paso 1: Usuario + Clave ----------------
            campo_usuario = await primer_selector_visible(page, SELECTORES_USUARIO, "Usuario")
            campo_clave = await primer_selector_visible(page, SELECTORES_CLAVE, "Clave")
            await campo_usuario.fill(usuario)
            await campo_clave.fill(clave)
            log("Usuario y clave ingresados.")

            campo_tarjeta = page.locator(SELECTOR_TARJETA)
            boton = page.locator(f"xpath={XPATH_BOTON_ENTRAR}")

            # Algunas versiones de la OFV muestran el campo Tarjeta desde el inicio.
            tarjeta_ya_visible = await campo_tarjeta.count() and await campo_tarjeta.is_visible()
            if not tarjeta_ya_visible:
                await captura(page, "02_credenciales")
                log("Haciendo clic en 'Entrar' (paso 1)...")
                await boton.click()
                try:
                    await campo_tarjeta.wait_for(state="visible", timeout=TIMEOUT_MS)
                except PlaywrightTimeoutError:
                    await captura(page, "error_sin_campo_tarjeta")
                    msg = await detectar_error_en_pagina(page)
                    raise ErrorLoginDGII(
                        "No apareció el campo Tarjeta tras el paso 1. "
                        + (f"Mensaje de la DGII: '{msg}'" if msg else "Verifique usuario y clave.")
                    )

            # ---------------- Paso 2: Tarjeta de coordenadas ----------------
            await captura(page, "03_campo_tarjeta")
            texto = await leer_texto_tooltip(page)
            log(f"Texto del tooltip: '{texto}'")
            posicion = extraer_posicion(texto)
            codigo = obtener_codigo(tarjeta, posicion)
            log(f"Posición solicitada: {posicion} → código encontrado (oculto: {'*' * len(codigo)}).")

            await campo_tarjeta.fill(codigo)
            await captura(page, "04_tarjeta_llena")

            log("Enviando formulario...")
            url_antes = page.url
            await boton.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
            except PlaywrightTimeoutError:
                log("⚠️  La página tardó en estabilizarse; se continúa con la verificación.")
            await captura(page, "05_resultado")

            # ---------------- Verificación ----------------
            error = await detectar_error_en_pagina(page)
            sigue_en_login = "login.aspx" in page.url.lower() and await campo_tarjeta.count() > 0
            if error or sigue_en_login:
                raise ErrorLoginDGII(
                    "El login no se completó. "
                    + (f"Mensaje de la DGII: '{error}'" if error else f"Se permanece en {url_antes}.")
                )

            log(f"✅ Login exitoso. URL actual: {page.url}")
            if not headless:
                log("El navegador permanecerá abierto. Presione Ctrl+C para cerrar.")
                try:
                    await page.wait_for_event("close", timeout=0)
                except (PlaywrightError, asyncio.CancelledError):
                    pass
            return 0

        except PlaywrightTimeoutError as e:
            await captura(page, "error_timeout")
            raise ErrorLoginDGII(f"Tiempo de espera agotado: {e}") from e
        finally:
            await navegador.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Login automático en la OFV de la DGII.")
    parser.add_argument("--headless", action="store_true", help="Ejecutar sin mostrar el navegador")
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(login(args.headless)))
    except ErrorLoginDGII as e:
        log(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log("Proceso interrumpido por el usuario.")
        sys.exit(130)
    except PlaywrightError as e:
        log(f"❌ Error de Playwright: {e}")
        log("Sugerencia: ejecute 'playwright install chromium' si el navegador no está instalado.")
        sys.exit(1)


if __name__ == "__main__":
    main()
