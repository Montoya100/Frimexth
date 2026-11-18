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

# 1. Configuración de la página en modo wide
st.set_page_config(
    page_title="Frimex",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Función auxiliar robusta para precios
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
# LIGAS Y ARCHIVOS DE RESPALDO
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
    modal_bg = "#1e1e1e"
    modal_text = "#f3f4f6"
else:
    bg_color = "#f8fafc"
    card_bg = "#ffffff"
    text_color = "#0f172a"
    sub_text_color = "#64748b"
    border_color = "#e2e8f0"
    input_bg = "#ffffff"
    input_text = "#0f172a"
    modal_bg = "#ffffff"
    modal_text = "#0f172a"

HEADER_RED = "#cf291d"          
BTN_RED = "#b0271a"             
BTN_RED_HOVER = "#8f1f14"
PRICE_BLACK = "#000000" if not st.session_state.dark_mode else "#ffffff"        
FAB_YELLOW = "#facc15"          
WHATSAPP_GREEN = "#25D366"      

# ==========================================
# ESTILOS CSS GENERALES
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<style>
    header[data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    .stApp, body, html, [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 5.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }}
    @media (min-width: 768px) {{
        .block-container {{
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
    }}

    /* BARRA DE BÚSQUEDA CON FONDO BLANCO Y CONTORNO ROJO */
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
        border: 2px solid {HEADER_RED} !important;
        border-radius: 30px !important;
    }}

    /* MODAL */
    div[data-testid="stDialog"] > div {{
        background-color: {modal_bg} !important;
        color: {modal_text} !important;
        border-radius: 16px !important;
        border: 1px solid {border_color} !important;
    }}

    /* BOTÓN FLOTANTE (FAB) PRINCIPAL */
    div[data-testid="stButton"]:has(button[kind="primary"]) {{
        position: fixed !important;
        bottom: 20px !important;
        left: 20px !important;
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
    }}

    /* TARJETAS DE PRODUCTO Y PRECIOS */
    .product-card, .pop-card-box {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 12px;
        position: relative;
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
# ENCABEZADO SUPERIOR NATIVO (LOGO + BOTÓN CARRITO)
# ==========================================
header_container = st.container()
with header_container:
    st.markdown(f"""
    <div style="background-color: {HEADER_RED}; padding: 12px 20px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <img src="{LOGO_URL}" style="max-height: 40px; width: auto;" />
    </div>
    """, unsafe_allow_html=True)
    
    # Botón superior nativo para ir al carrito
    col_space, col_cart_btn = st.columns([10, 2])
    with col_cart_btn:
        cart_label = f"🛒 Carrito ({total_items})" if total_items > 0 else "🛒 Carrito"
        if st.button(cart_label, use_container_width=True, key="header_cart_btn"):
            st.session_state.nav_view = "carrito"
            st.rerun()

# ==========================================
# MODAL DE VARIANTES
# ==========================================
@st.dialog("Seleccionar Presentación")
def variants_modal_dialog(base_name, variants_list):
    st.markdown(f"<h3 style='color: {BTN_RED} !important; text-align: center; font-size: 1.3rem;'>{base_name}</h3>", unsafe_allow_html=True)
    for idx, var in enumerate(variants_list):
        v_id = str(var.get("id"))
        v_name = var.get("name")
        v_price = safe_float(var.get("price"), 0.0)
        v_img = str(var.get("image", DEFAULT_PRODUCT_IMG))
        qty_in_cart = st.session_state.cart.get(v_id, 0)
        
        st.markdown(f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 10px; margin-bottom: 8px;">
            <b>{v_name}</b><br><span style="color: {PRICE_BLACK}; font-weight: 900;">${v_price:.2f} MXN</span>
        </div>
        """, unsafe_allow_html=True)
        
        col_m, col_n, col_p = st.columns([1, 1.2, 1])
        with col_m:
            if st.button("-", key=f"m_minus_{v_id}_{idx}", use_container_width=True):
                remove_from_cart(v_id)
                st.rerun()
        with col_n:
            st.markdown(f"<div style='text-align: center; font-weight: 900;'>{qty_in_cart}</div>", unsafe_allow_html=True)
        with col_p:
            if st.button("+", key=f"m_plus_{v_id}_{idx}", use_container_width=True):
                add_to_cart(v_id)
                st.rerun()
                
    if st.button("Listo", use_container_width=True, key="close_modal_btn"):
        st.session_state.show_variants_modal = False
        st.rerun()

if st.session_state.show_variants_modal and st.session_state.nav_view == "catalogo":
    variants_modal_dialog(st.session_state.current_modal_base, st.session_state.current_modal_items)

# ==========================================
# VISTA: CATÁLOGO
# ==========================================
if st.session_state.nav_view == "catalogo":
    search_query = st.text_input("Buscar productos", placeholder="¿Qué estás buscando hoy?", key="main_search_input")

    # Banner Principal
    banner_to_show = str(st.session_state.banner_url).strip()
    if not banner_to_show or banner_to_show.lower() == "nan":
        banner_to_show = DEFAULT_BANNER

    st.markdown(f"""
    <div style="border: 1px solid {border_color}; border-radius: 16px; padding: 4px; margin-top: 10px; margin-bottom: 16px; background: {card_bg}; text-align: center;">
        <img src="{banner_to_show}" style="width: 100%; max-height: 260px; object-fit: cover; border-radius: 12px;" />
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="background: {BTN_RED}; color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: 700; margin-bottom: 16px;">¡Envíos directos en ruta Frimex! Pide fácil y rápido</div>', unsafe_allow_html=True)

    # Categorías
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

    # Filtrado de productos sin errores sintácticos
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
                        img_src = str(representative.get("image", DEFAULT_PRODUCT_IMG))
                        st.image(img_src, use_container_width=True)
                        st.markdown(f'<div style="font-weight: 800; font-size: 1rem; margin-top: 8px;">{base_name}</div>', unsafe_allow_html=True)
                        
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
                                sub_c1, sub_c2, sub_c3 = st.columns([1, 1.2, 1])
                                with sub_c1:
                                    if st.button("-", key=f"minus_{pid}", use_container_width=True):
                                        remove_from_cart(pid)
                                        st.rerun()
                                with sub_c2:
                                    st.markdown(f"<div style='font-weight: 900; text-align: center;'>{qty_in_cart}</div>", unsafe_allow_html=True)
                                with sub_c3:
                                    if st.button("+", key=f"plus_{pid}", use_container_width=True):
                                        add_to_cart(pid)
                                        st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    # FAB FLOTANTE INFERIOR
    if total_items > 0:
        if st.button(f"Ver Carrito • ${total_amount:.2f}", type="primary", key="native_floating_fab"):
            st.session_state.nav_view = "carrito"
            st.rerun()

# ==========================================
# VISTA: CARRITO / COMPRA
# ==========================================
elif st.session_state.nav_view == "carrito":
    if st.button("← Volver al Catálogo", use_container_width=False):
        st.session_state.nav_view = "catalogo"
        st.rerun()
        
    st.markdown(f"<h3><span class='material-symbols-outlined' style='color: {BTN_RED};'>shopping_cart</span> Carrito de Compras</h3>", unsafe_allow_html=True)
    st.caption(f"Artículos seleccionados: {total_items}")
    
    if st.session_state.get("order_sent", False):
        st.success("¡Muchas gracias por tu compra! Tu pedido ha sido enviado con éxito a través de WhatsApp.")
        if st.button("Hacer un nuevo pedido", type="primary", use_container_width=True):
            st.session_state.order_sent = False
            st.session_state.cart = {}
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
                
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.markdown(f"**{p.get('name')}** ({qty} x ${p_price:.2f})")
                with col_c2:
                    if st.button("Quitar", key=f"del_cart_{item_id}", use_container_width=True):
                        del st.session_state.cart[item_id]
                        st.rerun()
                        
        st.write("---")
        st.markdown(f"**TOTAL DEL PEDIDO: ${total_price:.2f} MXN**")

        st.subheader("Datos de Entrega")
        st.text_input("Nombre del cliente (Obligatorio)", key="customer_name", placeholder="Ej. Juan Pérez")
        st.text_area("Dirección / Referencias (Obligatorio)", key="customer_address", placeholder="Calle, número, colonia...")
        st.text_input("Notas adicionales (Opcional)", key="customer_notes", placeholder="Ej. Cambio de $500")

        now = datetime.now()
        order_date = now.strftime("%d/%m/%Y %H:%M")
        
        msg_header = "NUEVO PEDIDO FRIMEX\n"
        msg_date = f"Fecha: {order_date}\n"
        msg_customer = f"CLIENTE: {st.session_state.customer_name}\n"
        msg_address = f"DIRECCIÓN: {st.session_state.customer_address}\n"
        msg_items_header = "\nDETALLE DE PRODUCTOS:\n" + "\n".join(order_summary) + "\n\n"
        msg_total = f"TOTAL: *${total_price:.2f} MXN*\n"

        full_message = msg_header + msg_date + msg_customer + msg_address + msg_items_header + msg_total
        whatsapp_url = f"https://wa.me/{WHATSAPP_PHONE}?text={urllib.parse.quote(full_message)}"
        
        is_form_valid = bool(st.session_state.customer_name.strip() and st.session_state.customer_address.strip())

        if is_form_valid:
            if st.button("Enviar pedido por WhatsApp", type="primary", use_container_width=True, key="whatsapp_fab_btn"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={whatsapp_url}">', unsafe_allow_html=True)
                st.session_state.order_sent = True
                st.rerun()
        else:
            st.info("Completa Nombre y Dirección para activar el botón de WhatsApp.")

# Pie de página para administración
st.write("---")
if st.button("Panel de Administración", use_container_width=True):
    st.session_state.nav_view = "admin"
    st.rerun()