import streamlit as st
import pandas as pd
import urllib.parse
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

st.set_page_config(
    page_title="Frimex - Página Frimex",
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
                return bool(data.get("dark_mode", False))
        except:
            pass
    return False

def save_dark_mode_setting(enabled):
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            json.dump({"dark_mode": bool(enabled)}, f, ensure_ascii=False, indent=4)
    except:
        pass

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = load_dark_mode_setting()

# Inicialización estricta y persistente de Estados
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

WHATSAPP_PHONE = "522381174698"

# ==========================================
# GESTIÓN DE TRIVIA CONFIGURABLE
# ==========================================
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

# ==========================================
# LIGAS Y ARCHIVOS DE RESPALDO Y PERSISTENCIA
# ==========================================
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

def load_saved_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except:
            pass
    # Base inicial por defecto si el archivo no existe aún
    initial = [
        {"id": "p1", "name": "Pistaches Salados (90g)", "category": "Individual", "price": 35.0, "description": "Pistaches tostados con sal de mar.", "image": DEFAULT_PRODUCT_IMG},
        {"id": "p2", "name": "Fritura (Con Chile)", "category": "Para compartir", "price": 25.0, "description": "Crujientes frituras artesanales.", "image": DEFAULT_PRODUCT_IMG}
    ]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(initial, f, ensure_ascii=False, indent=4)
    return initial

def save_products_to_file(prod_list):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(prod_list, f, ensure_ascii=False, indent=4)
    except:
        pass

def save_populares_to_file(pop_list):
    try:
        with open(POPULAR_FILE, "w", encoding="utf-8") as f:
            json.dump(pop_list, f, ensure_ascii=False, indent=4)
    except:
        pass

def save_suggestion_to_file(sugg_dict):
    try:
        with open(SUGGESTION_FILE, "w", encoding="utf-8") as f:
            json.dump(sugg_dict, f, ensure_ascii=False, indent=4)
    except:
        pass

if "products" not in st.session_state:
    st.session_state.products = load_saved_products()

if "popular_items" not in st.session_state:
    st.session_state.popular_items = [
        {"id": "p1", "name": "Pistaches Salados (90g)", "price": 35.0, "image": DEFAULT_PRODUCT_IMG}
    ]

# ==========================================
# PALETAS DE COLORES Y ESTILOS
# ==========================================
if st.session_state.dark_mode:
    bg_color = "#121212"
    card_bg = "#1e1e1e"
    text_color = "#f3f4f6"
    sub_text_color = "#9ca3af"
    border_color = "#2d3748"
    input_bg = "#1e1e1e"
    input_text = "#ffffff"
    modal_bg = "#ffffff"
    modal_text = "#000000"
else:
    bg_color = "#f8fafc"
    card_bg = "#ffffff"
    text_color = "#0f172a"
    sub_text_color = "#64748b"
    border_color = "#e2e8f0"
    input_bg = "#ffffff"
    input_text = "#0f172a"
    modal_bg = "#ffffff"
    modal_text = "#000000"

HEADER_RED = "#cf291d"          
BTN_RED = "#b0271a"             
BTN_RED_HOVER = "#8f1f14"
DARK_CIRCLE_RED = "#7a160e"     
PRICE_BLACK = "#000000"        
FAB_YELLOW = "#facc15"          
WHATSAPP_GREEN = "#25D366"      

# ==========================================
# CSS: STICKY HEADER Y MODALES
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<style>
    header[data-testid="stHeader"], 
    div[data-testid="stToolbar"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    .stApp, body, html, [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    .block-container {{
        padding-top: 5rem !important;
        padding-bottom: 6rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }}
    @media (min-width: 768px) {{
        .block-container {{
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
    }}

    /* STICKY HEADER PERMANENTE */
    .frimex-sticky-header {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        background-color: {HEADER_RED} !important;
        padding: 10px 24px !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25) !important;
        box-sizing: border-box !important;
        z-index: 999999 !important;
    }}

    .frimex-sticky-header img {{
        max-height: 44px !important;
        width: auto !important;
        object-fit: contain !important;
    }}

    /* CARRITO DEL HEADER DESVINCULADO (INACTIVO AL CLIC) */
    .header-cart-circle {{
        background-color: {DARK_CIRCLE_RED} !important;
        width: 42px;
        height: 42px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        position: relative;
        pointer-events: none !important;
    }}

    .header-cart-circle .material-symbols-outlined {{
        font-size: 22px;
        color: #ffffff;
    }}

    .header-badge-exact {{
        position: absolute;
        top: -4px;
        right: -4px;
        background-color: {FAB_YELLOW};
        color: #000000 !important;
        font-weight: 900;
        font-size: 0.75rem;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        z-index: 40;
        pointer-events: none !important;
    }}

    /* FORZAR TEXTOS NEGROS EN LOS MODALES DE OPCIONES */
    div[data-testid="stDialog"] > div {{
        background-color: {modal_bg} !important;
        color: #000000 !important;
        border-radius: 16px !important;
        border: 1px solid {border_color} !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25) !important;
    }}
    div[data-testid="stDialog"] p, 
    div[data-testid="stDialog"] span, 
    div[data-testid="stDialog"] div, 
    div[data-testid="stDialog"] h3, 
    div[data-testid="stDialog"] label {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}

    /* BOTÓN FLOTANTE (FAB) INFERIOR - INTACTO */
    div[data-testid="stButton"]:has(button[kind="primary"]) {{
        position: fixed !important;
        bottom: 20px !important;
        left: 20px !important;
        right: auto !important;
        z-index: 9999999 !important;
        width: auto !important;
    }}
    div[data-testid="stButton"]:has(button[kind="primary"]) > button {{
        background: {FAB_YELLOW} !important;
        color: #1e293b !important;
        padding: 12px 22px !important;
        border-radius: 50px !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
        border: none !important;
        height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        white-space: nowrap !important;
    }}
    div[data-testid="stButton"]:has(button[kind="primary"]) > button p,
    div[data-testid="stButton"]:has(button[kind="primary"]) > button span {{
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-size: 1rem !important;
        font-weight: 900 !important;
        margin: 0 !important;
    }}
    div[data-testid="stButton"]:has(button[kind="primary"]) > button::before {{
        content: "\\e8cc";
        font-family: 'Material Symbols Outlined';
        font-size: 22px;
        vertical-align: -4px;
        margin-right: 4px;
    }}

    /* ESTILOS GENERALES Y FORMULARIOS */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] {{
        background-color: #ffffff !important;
        border: 2px solid {HEADER_RED} !important;
        border-radius: 30px !important;
    }}
    input[type="text"], input {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        background-color: #ffffff !important;
    }}
    div[data-testid="stTextInput"] > div {{
        background-color: #ffffff !important;
        border-radius: 30px !important;
    }}

    label p, .stTextInput label, .stTextArea label, [data-testid="stWidgetLabel"] p, .stRadio label p {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
        font-weight: 700 !important;
    }}

    button, .stButton > button {{
        background-color: {BTN_RED} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(176, 39, 26, 0.25) !important;
        transition: all 0.2s ease !important;
    }}
    button:hover, .stButton > button:hover {{
        background-color: {BTN_RED_HOVER} !important;
        transform: translateY(-1px) !important;
    }}

    .product-card, .pop-card-box {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 12px;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}

    .price-tag {{
        color: {PRICE_BLACK} !important;
        font-weight: 900 !important;
        font-size: 1.7rem !important;
        margin-top: 6px;
        margin-bottom: 8px;
        display: block;
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
# MODAL DE VARIANTES CONDICIONAL (TEXTOS NEGROS)
# ==========================================
@st.dialog("Seleccionar Presentación")
def variants_modal_dialog(base_name, variants_list):
    st.markdown(f"<h3 style='color: {BTN_RED} !important; margin-bottom: 2px; text-align: center; font-size: 1.3rem;'>{base_name}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #000000 !important; font-size: 0.85rem; font-weight: 600; text-align: center; margin-bottom: 10px;'>Escoge la opción que deseas agregar:</p>", unsafe_allow_html=True)
    st.markdown(f"<hr style='margin: 4px 0 12px 0; border-color: {border_color};'>", unsafe_allow_html=True)
    
    for idx, var in enumerate(variants_list):
        v_id = str(var.get("id"))
        v_name = var.get("name")
        v_price = safe_float(var.get("price"), 0.0)
        v_img = str(var.get("image", "")).strip()
        if not v_img or v_img.lower() == "nan" or "placeholder" in v_img:
            v_img = DEFAULT_PRODUCT_IMG
            
        qty_in_cart = st.session_state.cart.get(v_id, 0)
        
        st.markdown(f"""
        <div style="background: #f1f5f9; border: 1px solid {border_color}; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <img src="{v_img}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 8px;" onerror="this.src='{DEFAULT_PRODUCT_IMG}';" />
                <div style="flex-grow: 1;">
                    <span style="color: #000000 !important; font-weight: 800; font-size: 0.9rem; display: block; line-height: 1.2;">{v_name}</span>
                    <span style="color: #000000 !important; font-weight: 900; font-size: 1.35rem;">${v_price:.2f} MXN</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col_m, col_n, col_p = st.columns([1, 1.2, 1], vertical_alignment="center")
        with col_m:
            if st.button("-", key=f"m_minus_{v_id}_{idx}", use_container_width=True):
                remove_from_cart(v_id)
                st.rerun()
        with col_n:
            st.markdown(f"<div style='font-size: 1.15rem; font-weight: 900; text-align: center; color: #000000 !important;'>{qty_in_cart}</div>", unsafe_allow_html=True)
        with col_p:
            if st.button("+", key=f"m_plus_{v_id}_{idx}", use_container_width=True):
                add_to_cart(v_id)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")
    if st.button("Listo", use_container_width=True, key="close_modal_btn"):
        st.session_state.show_variants_modal = False
        st.rerun()

if st.session_state.show_variants_modal and st.session_state.nav_view == "catalogo":
    variants_modal_dialog(st.session_state.current_modal_base, st.session_state.current_modal_items)

# ==========================================
# STICKY HEADER PERMANENTE
# ==========================================
if total_items > 0:
    st.markdown(f"""
    <div class="frimex-sticky-header">
        <img src="{LOGO_URL}" onerror="this.style.display='none'" />
        <div class="header-cart-circle" title="Carrito">
            <div class="header-badge-exact">{total_items}</div>
            <span class="material-symbols-outlined">shopping_cart</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="frimex-sticky-header">
        <img src="{LOGO_URL}" onerror="this.style.display='none'" />
    </div>
    """, unsafe_allow_html=True)

if st.session_state.nav_view == "catalogo":
    # 1. BARRA DE BÚSQUEDA BLANCA CON CONTORNO ROJO
    search_query = st.text_input("Buscar productos", placeholder="¿Qué estás buscando hoy?", key="main_search_input")

    # 2. BANNER PRINCIPAL
    banner_to_show = str(st.session_state.banner_url).strip()
    if not banner_to_show or banner_to_show.lower() == "nan":
        banner_to_show = DEFAULT_BANNER

    st.markdown(f"""
    <div style="border: 1px solid {border_color}; border-radius: 16px; padding: 4px; margin-top: 10px; margin-bottom: 16px; background: {card_bg}; text-align: center; width: 100%; overflow: hidden;">
        <img src="{banner_to_show}" style="width: 100%; max-height: 260px; object-fit: cover; border-radius: 12px;" onerror="this.onerror=null;this.src='{DEFAULT_BANNER}';" />
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="background: linear-gradient(135deg, {BTN_RED} 0%, #d4382c 100%); color: white; padding: 12px 16px; border-radius: 12px; text-align: center; font-weight: 700; margin-bottom: 16px; font-size: 0.95rem;"><span class="material-symbols-outlined" style="vertical-align: -5px; margin-right: 6px; font-size: 20px;">local_shipping</span> ¡Envíos directos en ruta Frimex! Pide fácil y rápido</div>', unsafe_allow_html=True)

    # POPULARES
    popular_ids = [str(p.get("id")) for p in st.session_state.popular_items]
    if popular_ids and not search_query:
        st.markdown(f"<h4 style='margin-bottom: 12px; color: {text_color};'><span class='material-symbols-outlined' style='font-size: 22px; color: {BTN_RED}; vertical-align: bottom; margin-right: 6px;'>local_fire_department</span> Lo más pedido</h4>", unsafe_allow_html=True)
        pop_list = [p for p in st.session_state.products if str(p.get("id")) in popular_ids]
        if pop_list:
            pop_cols = st.columns(min(len(pop_list), 3))
            for idx, p in enumerate(pop_list):
                with pop_cols[idx % len(pop_cols)]:
                    pid = str(p.get("id"))
                    p_price = safe_float(p.get("price"), 0.0)
                    st.markdown(f"""
                    <div class="pop-card-box">
                        <div style="background: {BTN_RED}; color: white; font-size: 0.68rem; font-weight: 800; padding: 3px 10px; border-radius: 20px; position: absolute; top: 10px; right: 10px;">Popular</div>
                        <img src="{p.get('image', DEFAULT_PRODUCT_IMG)}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 8px; margin-top: 10px;" />
                        <div style="font-weight: 800; font-size: 1rem; margin-top: 8px; color: {text_color};">{p.get('name')}</div>
                        <span class="price-tag">${p_price:.2f} MXN</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Agregar +", key=f"pop_add_{pid}_{idx}", use_container_width=True):
                        add_to_cart(pid)
                        st.rerun()
            st.markdown("<hr style='margin: 16px 0; border-color: " + border_color + ";'>", unsafe_allow_html=True)

    # CATEGORÍAS
    cats = ["Todo", "Individual", "Para compartir"]
    cat_cols = st.columns(len(cats))
    for i, c in enumerate(cats):
        with cat_cols[i]:
            is_active = (st.session_state.selected_cat == c)
            display_label = f"● {c}" if is_active else c
            if st.button(display_label, use_container_width=True, key=f"cat_btn_{c}"):
                st.session_state.selected_cat = c
                st.rerun()

    st.write("")

    # LISTADO CON SOPORTE DE VARIANTES CONDICIONAL
    try:
        current_products_list = sorted(st.session_state.products, key=lambda x: str(x.get("name", "")).lower())
        if st.session_state.selected_cat == "Todo":
            cat_filtered = current_products_list
        else:
            cat_filtered = [p for p in current_products_list if str(p.get("category", "Individual")).strip() == st.session_state.selected_cat]

        filtered_products = [p for p in cat_filtered if search_query.lower() in str(p.get("name", "")).lower() or search_query.lower() in str(p.get("description", "")).lower()]
    except:
        filtered_products = []

    if not filtered_products:
        st.info("No se encontraron productos en esta categoría o búsqueda.")
    else:
        grouped_dict = {}
        for p in filtered_products:
            name_raw = str(p.get("name", "Producto")).strip()
            if "(" in name_raw and ")" in name_raw:
                base_name = name_raw.split("(")[0].strip()
            else:
                base_name = name_raw
                
            if base_name not in grouped_dict:
                grouped_dict[base_name] = []
            if not any(str(it.get("id")) == str(p.get("id")) for it in grouped_dict[base_name]):
                grouped_dict[base_name].append(p)

        group_items_list = sorted(list(grouped_dict.items()), key=lambda x: 0 if len(x[1]) > 1 else 1)
        
        for i in range(0, len(group_items_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(group_items_list):
                    base_name, items_group = group_items_list[i + j]
                    representative = items_group[0]
                    pid = str(representative.get("id"))
                    
                    with cols[j]:
                        st.markdown('<div class="product-card">', unsafe_allow_html=True)
                        img_src = str(representative.get("image", "")).strip()
                        if not img_src or img_src.lower() == "nan" or "placeholder" in img_src:
                            img_src = DEFAULT_PRODUCT_IMG
                        
                        st.image(img_src, use_container_width=True)
                        st.markdown(f'<div style="font-weight: 800; font-size: 1rem; margin-top: 8px; color: {text_color};">{base_name}</div>', unsafe_allow_html=True)
                        desc_text = str(representative.get("description", "")).strip()
                        if desc_text and desc_text.lower() != "nan":
                            st.markdown(f'<div style="color: {sub_text_color}; font-size: 0.82rem; margin-top: 2px;">{desc_text}</div>', unsafe_allow_html=True)
                        
                        prices = [safe_float(it.get("price"), 0.0) for it in items_group]
                        st.markdown(f'<span class="price-tag">${prices[0]:.2f} MXN</span>', unsafe_allow_html=True)
                        
                        if len(items_group) > 1:
                            if st.button("Ver Opciones", key=f"variants_btn_{base_name}_{pid}", use_container_width=True):
                                st.session_state.current_modal_base = base_name
                                st.session_state.current_modal_items = items_group
                                st.session_state.show_variants_modal = True
                                st.rerun()
                        else:
                            qty_in_cart = st.session_state.cart.get(pid, 0)
                            if qty_in_cart == 0:
                                if st.button("Agregar", key=f"add_{pid}", use_container_width=True):
                                    add_to_cart(pid)
                                    st.rerun()
                            else:
                                sub_c1, sub_c2, sub_c3 = st.columns([1, 1.2, 1], vertical_alignment="center")
                                with sub_c1:
                                    if st.button("-", key=f"minus_{pid}", use_container_width=True):
                                        remove_from_cart(pid)
                                        st.rerun()
                                with sub_c2:
                                    st.markdown(f"<div style='font-size: 1.05rem; font-weight: 900; text-align: center; color: {text_color};'>{qty_in_cart}</div>", unsafe_allow_html=True)
                                with sub_c3:
                                    if st.button("+", key=f"plus_{pid}", use_container_width=True):
                                        add_to_cart(pid)
                                        st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    # BOTÓN FLOTANTE (FAB) INFERIOR - 100% INTACTO Y FUNCIONAL
    if total_items > 0:
        if st.button(f"Ver Carrito • ${total_amount:.2f}", type="primary", key="native_floating_fab"):
            st.session_state.nav_view = "carrito"
            st.rerun()

elif st.session_state.nav_view == "carrito":
    if st.button("← Volver al Catálogo", use_container_width=False):
        st.session_state.nav_view = "catalogo"
        st.rerun()
        
    st.markdown(f"<h3 style='color: {text_color};'><span class='material-symbols-outlined' style='vertical-align: bottom; color: {BTN_RED};'>shopping_cart</span> Carrito de Compras</h3>", unsafe_allow_html=True)
    st.caption(f"Artículos seleccionados: {total_items}")
    
    if st.session_state.get("order_sent", False):
        st.success("¡Muchas gracias por tu compra! Tu pedido ha sido enviado con éxito a través de WhatsApp.")
        if st.button("Hacer un nuevo pedido", type="primary", use_container_width=True):
            st.session_state.order_sent = False
            st.session_state.cart = {}
            st.session_state.trivia_answered = False
            st.session_state.trivia_won = False
            st.session_state.customer_name = ""
            st.session_state.customer_address = ""
            st.session_state.customer_notes = ""
            st.session_state.nav_view = "catalogo"
            st.rerun()
    elif not st.session_state.cart:
        st.info("Tu carrito está vacío. Agrega productos desde el catálogo.")
    else:
        total_price = 0.0
        order_summary = []
        
        st.write("---")
        for item_id, qty in list(st.session_state.cart.items()):
            p = next((item for item in st.session_state.products if str(item.get("id")) == str(item_id)), None)
            if p:
                p_price = safe_float(p.get("price"), 0.0)
                subtotal = p_price * qty
                total_price += subtotal
                order_summary.append(f"- {qty}x {p.get('name')} - ${subtotal:.2f} MXN")
                
                col_c1, col_c2 = st.columns([3, 1], vertical_alignment="center")
                with col_c1:
                    st.markdown(f"**{p.get('name')}**")
                    st.caption(f"{qty} x ${p_price:.2f} = ${subtotal:.2f}")
                with col_c2:
                    if st.button("Quitar", key=f"del_cart_{item_id}", use_container_width=True):
                        del st.session_state.cart[item_id]
                        st.rerun()
                        
        st.write("---")
        st.markdown(f"""
        <div style="background: {card_bg}; border: 2px solid {PRICE_BLACK}; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 16px;">
            <span class="material-symbols-outlined" style="font-size: 28px; color: {PRICE_BLACK}; vertical-align: middle; margin-right: 6px;">receipt_long</span>
            <span style="font-size: 1rem; font-weight: 700; color: {sub_text_color}; display: inline-block;">TOTAL DEL PEDIDO:</span>
            <span style="font-size: 1.8rem; font-weight: 900; color: {PRICE_BLACK}; display: block; margin-top: 4px;">${total_price:.2f} MXN</span>
        </div>
        """, unsafe_allow_html=True)

        sugg_id = st.session_state.cart_suggestion.get("id")
        if sugg_id:
            sugg_prod = next((p for p in st.session_state.products if str(p.get("id")) == str(sugg_id)), None)
            if sugg_prod and str(sugg_id) not in st.session_state.cart:
                sugg_price = safe_float(sugg_prod.get("price"), 0.0)
                st.info(f"**¿Te hace falta algo más?** ¡Acompaña tu pedido con **{sugg_prod.get('name')}** por solo **${sugg_price:.2f} MXN**!")
                if st.button(f"Agregar {sugg_prod.get('name')} al carrito", key="add_sugg_btn"):
                    add_to_cart(str(sugg_id))
                    st.rerun()
        
        st.subheader("Datos de Entrega")
        st.text_input("Nombre del cliente (Obligatorio)", key="customer_name", placeholder="Ej. Juan Pérez")
        st.text_area("Dirección / Referencias (Obligatorio)", key="customer_address", placeholder="Calle, número, colonia...")
        st.text_input("Notas adicionales (Opcional)", key="customer_notes", placeholder="Ej. Cambio de $500")

        st.markdown("---")
        st.subheader("¡Juega y gana una sorpresa antes de enviar!")

        if not st.session_state.trivia_answered:
            if "current_trivia_idx" not in st.session_state:
                st.session_state.current_trivia_idx = random.randint(0, len(st.session_state.trivia_questions_db) - 1)
            
            if st.session_state.current_trivia_idx >= len(st.session_state.trivia_questions_db):
                st.session_state.current_trivia_idx = 0

            t_data = st.session_state.trivia_questions_db[st.session_state.current_trivia_idx]
            raw_options = str(t_data.get("opciones", "A | B | C"))
            opciones_list = [o.strip() for o in raw_options.split("|") if o.strip()]

            st.info(f"**Pregunta:** {t_data.get('pregunta')}")
            respuesta_usuario = st.radio("Elige tu respuesta:", opciones_list, key="trivia_selection")

            if st.button("Comprobar respuesta", key="check_trivia_btn"):
                st.session_state.trivia_answered = True
                correct_ans = str(t_data.get("respuesta")).strip()
                if str(respuesta_usuario).strip().lower() == correct_ans.lower():
                    st.session_state.trivia_won = True
                st.rerun()
        else:
            if st.session_state.trivia_won:
                st.success("¡Correcto! Has ganado una sorpresa en tu pedido.")
            else:
                st.warning("¡Casi la tienes! No te preocupes, tu pedido sigue en pie.")

            if st.button("Jugar otra pregunta", key="reset_trivia_btn"):
                st.session_state.trivia_answered = False
                st.session_state.trivia_won = False
                if "current_trivia_idx" in st.session_state:
                    del st.session_state.current_trivia_idx
                st.rerun()

        now = datetime.now()
        order_date = now.strftime("%d/%m/%Y %H:%M")
        date_tag = now.strftime("%m%d")
        verification_code = f"FRIMEX-OK-{date_tag}"

        change_text = ""
        current_notes_val = st.session_state.customer_notes
        if current_notes_val.strip():
            numbers_in_notes = re.findall(r'\d+(?:\.\d+)?', current_notes_val)
            if numbers_in_notes:
                amounts = [safe_float(n) for n in numbers_in_notes]
                valid_cash = [amt for amt in amounts if amt >= total_price]
                if valid_cash:
                    cash_given = valid_cash[0]
                    change = cash_given - total_price
                    change_text = f"Paga con: ${cash_given:.2f} MXN\nCambio: ${change:.2f} MXN\n"

        msg_header = "NUEVO PEDIDO FRIMEX\n"
        msg_date = f"Fecha: {order_date}\n"
        msg_customer = f"CLIENTE: {st.session_state.customer_name}\n"
        msg_address = f"DIRECCIÓN: {st.session_state.customer_address}\n"
        msg_notes = f"NOTAS: {current_notes_val}\n" if current_notes_val else ""
        msg_change = change_text
        msg_items_header = "\nDETALLE DE PRODUCTOS:\n" + "\n".join(order_summary) + "\n\n"
        msg_total = f"TOTAL: *${total_price:.2f} MXN*\n"
        msg_trivia = f"\nPREMIO GANADO: Sorpresa\n{verification_code}" if st.session_state.trivia_won else ""

        full_message = msg_header + msg_date + msg_customer + msg_address + msg_notes + msg_change + msg_items_header + msg_total + msg_trivia
        whatsapp_url = f"https://wa.me/{WHATSAPP_PHONE}?text={urllib.parse.quote(full_message)}"
        
        st.write("")
        is_form_valid = bool(st.session_state.customer_name.strip() and st.session_state.customer_address.strip())

        if is_form_valid:
            st.markdown(f"""
            <style>
                div[data-testid="stButton"]:has(button[kind="primary"]) > button {{
                    background: {WHATSAPP_GREEN} !important;
                    color: #ffffff !important;
                }}
                div[data-testid="stButton"]:has(button[kind="primary"]) > button p,
                div[data-testid="stButton"]:has(button[kind="primary"]) > button span {{
                    color: #ffffff !important;
                    -webkit-text-fill-color: #ffffff !important;
                }}
                div[data-testid="stButton"]:has(button[kind="primary"]) > button::before {{
                    content: "\\e0ca" !important;
                }}
            </style>
            """, unsafe_allow_html=True)

            if st.button("Enviar pedido por WhatsApp", type="primary", use_container_width=True, key="whatsapp_fab_btn"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={whatsapp_url}">', unsafe_allow_html=True)
                st.session_state.order_sent = True
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ya envié mi pedido, finalizar compra", use_container_width=True, key="finalize_order_safe_btn"):
                st.session_state.order_sent = True
                st.rerun()
        else:
            st.info("Completa Nombre y Dirección para activar el botón de WhatsApp.")

elif st.session_state.nav_view == "admin":
    if st.button("← Volver al Catálogo", use_container_width=False):
        st.session_state.nav_view = "catalogo"
        st.rerun()

    st.markdown(f"<h3 style='color: {text_color};'><span class='material-symbols-outlined' style='vertical-align: bottom; color: {BTN_RED};'>settings</span> Panel de Administración y Ajustes</h3>", unsafe_allow_html=True)
    
    if not st.session_state.admin_authenticated:
        st.subheader("Acceso Restringido")
        pass_input = st.text_input("Ingresa la contraseña de administrador", type="password", placeholder="Clave de 4 dígitos...")
        if st.button("Ingresar"):
            if pass_input == "7031":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.success("¡Acceso concedido!")
        tab_prod, tab_pop, tab_sugg, tab_banner, tab_upload, tab_trivia, tab_theme = st.tabs([
            "Productos (Carga CSV/Excel)", "Populares", "Sugerencia Carrito", "Banner", "Subir", "Trivia", "Apariencia"
        ])
        
        with tab_prod:
            st.markdown("### Inventario Permanente y Carga de Archivos (CSV / Excel)")
            st.info("Sube tu archivo CSV o Excel con columnas como: `id`, `name`, `category`, `price`, `description`, `image`. También puedes editar los productos directamente en la tabla de abajo y guardar los cambios de forma permanente.")
            
            uploaded_catalog = st.file_uploader("Cargar Catálogo (CSV, XLSX)", type=["csv", "xlsx", "xls"])
            if uploaded_catalog is not None:
                try:
                    if uploaded_catalog.name.endswith('.csv'):
                        df_uploaded = pd.read_csv(uploaded_catalog)
                    else:
                        df_uploaded = pd.read_excel(uploaded_catalog)
                    
                    new_imported_list = []
                    for idx, row in df_uploaded.iterrows():
                        r_id = str(row.get("id", f"prod_imp_{idx}")).strip()
                        r_name = str(row.get("name", "Producto")).strip()
                        r_cat = str(row.get("category", "Individual")).strip()
                        r_price = safe_float(row.get("price", 0.0), 0.0)
                        r_desc = str(row.get("description", "")).strip()
                        r_img = str(row.get("image", DEFAULT_PRODUCT_IMG)).strip()
                        if not r_img or r_img.lower() == "nan":
                            r_img = DEFAULT_PRODUCT_IMG
                            
                        new_imported_list.append({
                            "id": r_id,
                            "name": r_name,
                            "category": r_cat if r_cat in ["Individual", "Para compartir"] else "Individual",
                            "price": r_price,
                            "description": r_desc if r_desc.lower() != "nan" else "",
                            "image": r_img
                        })
                    if new_imported_list:
                        st.session_state.products = new_imported_list
                        save_products_to_file(new_imported_list)
                        st.success(f"¡Se han importado y guardado permanentemente {len(new_imported_list)} productos desde tu archivo!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar el archivo: {e}")

            st.markdown("---")
            st.markdown("#### Editar Inventario Actual")
            current_sorted_products = sorted(st.session_state.products, key=lambda x: str(x.get("name", "")).lower())
            df_current = pd.DataFrame(current_sorted_products)
            column_config = {
                "id": None,
                "category": st.column_config.SelectboxColumn("Categoría", options=["Individual", "Para compartir"], required=True)
            }
            edited_df = st.data_editor(df_current, num_rows="dynamic", key="editor_admin_table", column_config=column_config, hide_index=True, use_container_width=True)
            
            if st.button("Guardar Cambios de Productos Permanentemente"):
                updated_list = []
                for idx, row in edited_df.iterrows():
                    raw_id = row.get("id")
                    prod_id = str(raw_id).strip() if pd.notna(raw_id) and str(raw_id).strip() != "" else f"prod_{int(datetime.now().timestamp())}_{idx}"
                    raw_img = str(row.get("image", "")).strip()
                    prod_img = raw_img if raw_img != "" and raw_img.lower() != "nan" and "placeholder" not in raw_img else DEFAULT_PRODUCT_IMG
                    raw_desc = row.get("description")
                    prod_desc = str(raw_desc).strip() if pd.notna(raw_desc) and str(raw_desc).strip() != "nan" else ""
                    
                    updated_list.append({
                        "id": prod_id,
                        "name": str(row.get("name", "Nuevo producto")),
                        "category": str(row.get("category", "Individual")),
                        "price": safe_float(row.get("price"), 0.0),
                        "description": prod_desc,
                        "image": prod_img
                    })
                updated_list = sorted(updated_list, key=lambda x: str(x.get("name", "")).lower())
                st.session_state.products = updated_list
                save_products_to_file(updated_list)
                st.success("¡Productos guardados y persistidos correctamente!")
                st.rerun()

        with tab_pop:
            st.markdown("### Seleccionar productos Populares")
            current_pop_ids = [str(p.get("id")) for p in st.session_state.popular_items]
            selected_populares_new = []
            for prod in st.session_state.products:
                p_id = str(prod.get("id"))
                p_name = str(prod.get("name"))
                p_price = safe_float(prod.get("price"), 0.0)
                is_currently_pop = p_id in current_pop_ids
                if st.checkbox(f"{p_name} (${p_price:.2f} MXN)", value=is_currently_pop, key=f"check_pop_{p_id}"):
                    selected_populares_new.append({
                        "id": p_id,
                        "name": p_name,
                        "price": p_price,
                        "image": prod.get("image", DEFAULT_PRODUCT_IMG)
                    })
            if st.button("Guardar Populares"):
                st.session_state.popular_items = selected_populares_new
                save_populares_to_file(selected_populares_new)
                st.success("¡Populares actualizados con éxito!")
                st.rerun()

        with tab_sugg:
            st.markdown("### Producto Gancho Sugerido en el Carrito")
            prod_options = {p.get("name"): p.get("id") for p in st.session_state.products}
            current_sugg_id = st.session_state.cart_suggestion.get("id")
            current_sugg_name = next((name for name, pid in prod_options.items() if str(pid) == str(current_sugg_id)), list(prod_options.keys())[0] if prod_options else "")
            selected_sugg_name = st.selectbox("Producto sugerido", options=list(prod_options.keys()), index=list(prod_options.keys()).index(current_sugg_name) if current_sugg_name in prod_options else 0)
            
            if st.button("Guardar Sugerencia de Carrito"):
                chosen_id = prod_options.get(selected_sugg_name)
                st.session_state.cart_suggestion = {"id": chosen_id}
                save_suggestion_to_file(st.session_state.cart_suggestion)
                st.success("¡Sugerencia gancho guardada correctamente!")
                st.rerun()

        with tab_banner:
            st.markdown("### Imagen del Banner Principal")
            new_banner_url = st.text_input("URL de la imagen del banner", value=st.session_state.banner_url)
            if st.button("Guardar Banner"):
                if new_banner_url.strip():
                    st.session_state.banner_url = new_banner_url.strip()
                    with open(BANNER_FILE, "w", encoding="utf-8") as f:
                        json.dump({"url": new_banner_url.strip()}, f, ensure_ascii=False, indent=4)
                    st.success("¡Banner actualizado con éxito!")
                    st.rerun()

        with tab_upload:
            st.markdown("### Subir Imágenes al Servidor")
            uploaded_file = st.file_uploader("Elige una imagen", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_file is not None:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"¡Subida con éxito: `{uploaded_file.name}`!")
                st.image(file_path, width=200)
                st.text_input("Copia esta ruta:", value=f"/{UPLOAD_DIR}/{uploaded_file.name}")

        with tab_trivia:
            st.markdown("### Administrar Preguntas de la Trivia")
            df_trivia = pd.DataFrame(st.session_state.trivia_questions_db)
            edited_trivia_df = st.data_editor(df_trivia, num_rows="dynamic", key="editor_trivia_table", use_container_width=True)
            if st.button("Guardar Preguntas de Trivia"):
                updated_trivia_list = []
                for _, row in edited_trivia_df.iterrows():
                    p_text = str(row.get("pregunta", "")).strip()
                    o_text = str(row.get("opciones", "")).strip()
                    r_text = str(row.get("respuesta", "")).strip()
                    if p_text and o_text and r_text:
                        updated_trivia_list.append({"pregunta": p_text, "opciones": o_text, "respuesta": r_text})
                if updated_trivia_list:
                    st.session_state.trivia_questions_db = updated_trivia_list
                    with open(TRIVIA_FILE, "w", encoding="utf-8") as f:
                        json.dump(updated_trivia_list, f, ensure_ascii=False, indent=4)
                    st.success("¡Preguntas guardadas con éxito!")
                    st.rerun()

        with tab_theme:
            st.markdown("### Control de Apariencia (Modo Claro / Oscuro)")
            dark_toggle = st.toggle("Activar Modo Oscuro", value=st.session_state.dark_mode)
            if st.button("Aplicar y Guardar Tema"):
                st.session_state.dark_mode = dark_toggle
                save_dark_mode_setting(dark_toggle)
                st.success("¡Tema actualizado!")
                st.rerun()
        
        st.write("---")
        if st.button("Cerrar Sesión Admin", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.session_state.nav_view = "catalogo"
            st.rerun()

# PIE DE PÁGINA
st.write("---")
col_foot1, col_foot_admin, col_foot2 = st.columns(3)
with col_foot_admin:
    if st.button("Admin", use_container_width=True, key="admin_footer_btn"):
        st.session_state.nav_view = "admin"
        st.rerun()