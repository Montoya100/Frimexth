import streamlit as st
import pandas as pd
import urllib.parse
import requests
import json
import os
import random
import re
from datetime import datetime

LOGO_URL = "https://raw.githubusercontent.com/Montoya100/Frimexth/main/logo.png"
DATA_FILE = "productos_frimex.json"
POPULAR_FILE = "populares_frimex.json"
BANNER_FILE = "banner_frimex.json"
SUGGESTION_FILE = "sugerencia_frimex.json"
THEME_FILE = "tema_frimex.json"
TRIVIA_FILE = "trivia_frimex.json"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 1. Configuración de la página
st.set_page_config(
    page_title="Frimex",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = str(val).replace("$", "").replace("MXN", "").strip()
        return float(cleaned)
    except:
        return default

# ==========================================
# GESTIÓN DE MODO OSCURO / CLARO
# ==========================================
def load_dark_mode_setting():
    if os.path.exists(THEME_FILE):
        try:
            with open(THEME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("auto_dark_mode", True))
        except:
            pass
    return True

def save_dark_mode_setting(enabled):
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            json.dump({"auto_dark_mode": bool(enabled)}, f, ensure_ascii=False, indent=4)
    except:
        pass

if "auto_dark_mode" not in st.session_state:
    st.session_state.auto_dark_mode = load_dark_mode_setting()

# 2. Inicialización estricta de Estados
if "cart" not in st.session_state:
    st.session_state.cart = {}

if "nav_view" not in st.session_state:
    st.session_state.nav_view = "catalogo"

if "selected_cat" not in st.session_state:
    st.session_state.selected_cat = "Todo"

if "show_variants_modal" not in st.session_state:
    st.session_state.show_variants_modal = False

if "current_modal_base" not in st.session_state:
    st.session_state.current_modal_base = ""

if "current_modal_items" not in st.session_state:
    st.session_state.current_modal_items = []

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if "trivia_answered" not in st.session_state:
    st.session_state.trivia_answered = False

if "trivia_won" not in st.session_state:
    st.session_state.trivia_won = False

if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""

if "customer_address" not in st.session_state:
    st.session_state.customer_address = ""

if "customer_notes" not in st.session_state:
    st.session_state.customer_notes = ""

if "order_sent" not in st.session_state:
    st.session_state.order_sent = False

LOYVERSE_TOKEN = "0c1c93162c4441099be4862722f079b9"
WHATSAPP_PHONE = "522381174698"

DEFAULT_TRIVIA = [
    {
        "pregunta": "¿Cuál es el ingrediente principal de un buen guacamole tradicional?",
        "opciones": "Aguacate | Tomate verde | Calabaza",
        "respuesta": "Aguacate"
    },
    {
        "pregunta": "¿En qué estado de la República Mexicana se encuentra Tehuacán y Cacaloapan?",
        "opciones": "Puebla | Veracruz | Oaxaca",
        "respuesta": "Puebla"
    },
    {
        "pregunta": "¿Qué tipo de saborizante natural predomina en las botanas picositas estilo mexicano?",
        "opciones": "Chile y limón | Menta y chocolate | Canela y azúcar",
        "respuesta": "Chile y limón"
    }
]

def load_saved_trivia():
    if os.path.exists(TRIVIA_FILE):
        try:
            with open(TRIVIA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except:
            pass
    return DEFAULT_TRIVIA

if "trivia_questions_db" not in st.session_state:
    st.session_state.trivia_questions_db = load_saved_trivia()

DEFAULT_BANNER = "https://raw.githubusercontent.com/Montoya100/Frimexth/main/banner.png"
DEFAULT_PRODUCT_IMG = "https://raw.githubusercontent.com/Montoya100/Frimexth/main/image.jpg"

def load_saved_banner():
    if os.path.exists(BANNER_FILE):
        try:
            with open(BANNER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    url = str(data.get("url", "")).strip()
                    if url and url.lower() != "nan":
                        return url
        except:
            pass
    return DEFAULT_BANNER

if "banner_url" not in st.session_state:
    st.session_state.banner_url = load_saved_banner()

def load_saved_suggestion():
    if os.path.exists(SUGGESTION_FILE):
        try:
            with open(SUGGESTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except:
            pass
    return {}

if "cart_suggestion" not in st.session_state:
    st.session_state.cart_suggestion = load_saved_suggestion()

@st.cache_data(ttl=60)
def fetch_loyverse_products():
    headers = {
        "Authorization": f"Bearer {LOYVERSE_TOKEN}",
        "Content-Type": "application/json"
    }
    products_list = []
    try:
        items_res = requests.get("https://api.loyverse.com/v1.0/items", headers=headers, timeout=5)
        if items_res.status_code == 200:
            raw_items = items_res.json().get("items", [])
            route_items = [i for i in raw_items if "venta en ruta" in str(i.get("category_name", "")).lower() or "frimex" in str(i.get("category_name", "")).lower()]
            if not route_items:
                route_items = raw_items

            for item in route_items:
                cat_name = item.get("category_name", "Individual")
                cat_lower = str(cat_name).lower()
                category_mapped = "Para compartir" if "compartir" in cat_lower or "familiar" in cat_lower or "fritura" in cat_lower else "Individual"
                
                variants = item.get("variants", [])
                item_name = item.get("item_name", "Producto")
                desc = item.get("description", "")
                base_item_price = safe_float(item.get("price"), 0.0)
                
                if variants:
                    for var in variants:
                        price = safe_float(var.get("price", base_item_price), 0.0)
                        var_name = var.get("variant_name", "")
                        display_name = f"{item_name} ({var_name})" if var_name and var_name != "Default" else item_name
                        products_list.append({
                            "id": str(var.get("variant_id", item.get("id"))),
                            "name": display_name,
                            "category": category_mapped,
                            "price": price,
                            "description": desc,
                            "image": DEFAULT_PRODUCT_IMG
                        })
                else:
                    products_list.append({
                        "id": str(item.get("id")),
                        "name": item_name,
                        "category": category_mapped,
                        "price": base_item_price,
                        "description": desc,
                        "image": DEFAULT_PRODUCT_IMG
                    })
    except:
        pass

    if not products_list:
        products_list = [
            {"id": "p1", "name": "Pistaches Salados (90g)", "category": "Individual", "price": 35.0, "description": "Pistaches tostados con sal de mar.", "image": DEFAULT_PRODUCT_IMG},
            {"id": "p2", "name": "Fritura (Con Chile)", "category": "Para compartir", "price": 25.0, "description": "Crujientes frituras artesanales.", "image": DEFAULT_PRODUCT_IMG}
        ]
    return products_list

def load_saved_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except:
            pass
    initial = fetch_loyverse_products()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(initial, f, ensure_ascii=False, indent=4)
    return initial

if "products" not in st.session_state:
    st.session_state.products = load_saved_products()

if "popular_items" not in st.session_state:
    st.session_state.popular_items = [
        {"id": "p1", "name": "Pistaches Salados (90g)", "price": 35.0, "image": DEFAULT_PRODUCT_IMG}
    ]

text_color = "#f1f5f9" if st.session_state.auto_dark_mode else "#1e293b"
sub_text_color = "#94a3b8" if st.session_state.auto_dark_mode else "#64748b"
card_bg = "#1e293b" if st.session_state.auto_dark_mode else "#ffffff"
border_color = "#334155" if st.session_state.auto_dark_mode else "#e2e8f0"

BTN_GENERAL = "#DC2626"
BTN_GENERAL_HOVER = "#B91C1C"
BTN_CART_FAB = "#EF4444"

# ==========================================
# CSS ESTRICTO: ELIMINAR HEADER NATIVO, YITH Y BOTONES EXTERNOS
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<style>
    /* ELIMINAR HEADER NATIVO DE STREAMLIT QUE TAPA EL LOGO */
    header[data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* BLOQUEO TOTAL DE ELEMENTOS YITH Y BOTONES EXTERNOS (G-HUB, PINTEREST, ETC.) */
    body > div[style*="position: fixed"], 
    body > iframe, 
    div[class*="viewerBadge"], 
    div[class*="assistive"],
    div[class*="yith"],
    div[id*="yith"],
    button[class*="yith"],
    div:has(> a[href*="pinterest"]),
    div:has(> button[title*="Share"]),
    div:has(> button[title*="G-Hub"]) {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    .stApp, body, html, [data-testid="stAppViewContainer"] {{
        background-color: {"#121212" if st.session_state.auto_dark_mode else "#f8fafc"} !important;
        color: {text_color} !important;
    }}

    .block-container {{
        padding-top: 6.5rem !important;
        padding-bottom: 6rem !important;
        max-width: 100% !important;
    }}

    /* BARRA SUPERIOR FIJA ABSOLUTA Y CON MÁXIMO Z-INDEX */
    .sticky-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 90px;
        z-index: 999999 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 8px 20px;
        background-color: {"#121212" if st.session_state.auto_dark_mode else "#ffffff"} !important;
        border-bottom: 2px solid {BTN_GENERAL} !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}

    .sticky-logo {{
        max-height: 72px;
        width: auto;
        object-fit: contain;
        display: block !important;
        visibility: visible !important;
    }}

    /* BOTONES Y ACCIONES */
    button, .stButton > button, div[data-testid="stButton"] > button {{
        background-color: {BTN_GENERAL} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(220, 38, 38, 0.2) !important;
    }}
    button:hover, .stButton > button:hover {{
        background-color: {BTN_GENERAL_HOVER} !important;
        transform: translateY(-2px) !important;
    }}

    .product-card, .pop-card-box {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 14px;
        position: relative;
    }}
</style>
""", unsafe_allow_html=True)

def add_to_cart(pid):
    st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + 1

def remove_from_cart(pid):
    if pid in st.session_state.cart:
        if st.session_state.cart[pid] > 1:
            st.session_state.cart[pid] -= 1
        else:
            del st.session_state.cart[pid]

total_items = sum(st.session_state.cart.values())
total_amount = sum(safe_float(next((p.get("price") for p in st.session_state.products if str(p.get("id")) == str(pid)), 0)) * qty for pid, qty in st.session_state.cart.items())

# ==========================================
# BARRA FIJA CON LOGOTIPO PROTAGONISTA
# ==========================================
st.markdown(f"""
<div class="sticky-header">
    <img src="{LOGO_URL}" class="sticky-logo" onerror="this.style.display='none'" />
</div>
""", unsafe_allow_html=True)

# Controles superiores (Buscador / Carrito con Icono Outline puro)
col_spacer, col_cart = st.columns([4, 1])
with col_cart:
    # Renderizamos mediante columnas separadas para garantizar el icono outline de Material Symbols sin emojis
    icon_col, btn_col = st.columns([1, 3], vertical_alignment="center")
    with icon_col:
        st.markdown('<span class="material-symbols-outlined" style="font-size: 24px; color: #DC2626; display: block; text-align: right;">shopping_cart</span>', unsafe_allow_html=True)
    with btn_col:
        btn_label = f"({total_items}) - ${total_amount:.2f}" if total_items > 0 else "Carrito"
        if st.button(btn_label, use_container_width=True, key="top_cart_btn"):
            st.session_state.nav_view = "carrito" if st.session_state.nav_view != "carrito" else "catalogo"
            st.rerun()

st.write("")

if st.session_state.nav_view == "catalogo":
    search_query = st.text_input("Buscar productos...", placeholder="Buscar productos...", label_visibility="collapsed")
    st.write("---")
    
    st.markdown('<div style="background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%); color: white; padding: 12px; border-radius: 12px; text-align: center; font-weight: 700; margin-bottom: 14px;"><span class="material-symbols-outlined" style="vertical-align: -4px; margin-right: 4px;">local_shipping</span> ¡Envíos directos en ruta Frimex!</div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    for idx, p in enumerate(st.session_state.products):
        with cols[idx % 3]:
            pid = str(p.get("id"))
            p_price = safe_float(p.get("price"), 0.0)
            st.markdown(f"""
            <div class="product-card">
                <img src="{p.get('image', DEFAULT_PRODUCT_IMG)}" style="width: 100%; height: 100px; object-fit: cover; border-radius: 8px;" />
                <div style="font-weight: 800; font-size: 1rem; margin-top: 8px; color: {text_color};">{p.get('name')}</div>
                <div style="color: {BTN_GENERAL}; font-weight: 900; margin-top: 4px;">${p_price:.2f} MXN</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Agregar", key=f"add_{pid}_{idx}", use_container_width=True):
                add_to_cart(pid)
                st.rerun()

elif st.session_state.nav_view == "carrito":
    if st.button("Volver al Catálogo", use_container_width=False):
        st.session_state.nav_view = "catalogo"
        st.rerun()
        
    st.markdown("### <span class='material-symbols-outlined' style='vertical-align: bottom; color: #DC2626;'>shopping_cart</span> Carrito de Compras", unsafe_allow_html=True)
    if not st.session_state.cart:
        st.info("Tu carrito está vacío.")
    else:
        for item_id, qty in list(st.session_state.cart.items()):
            p = next((item for item in st.session_state.products if str(item.get("id")) == str(item_id)), None)
            if p:
                st.write(f"- {qty}x {p.get('name')} (${safe_float(p.get('price')) * qty:.2f} MXN)")