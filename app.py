import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import openai
import requests

# ---------------------------------------------------------
# 1. CONFIGURACIÓN INICIAL (NO TOCAR)
# ---------------------------------------------------------
st.set_page_config(page_title="J.A.R.V.I.S. Taller", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------
# 2. SISTEMA DE SEGURIDAD (Usuario y Contraseña)
# ---------------------------------------------------------
# Puedes cambiar esto por lo que tú quieras:
USUARIO_REAL = "raul"
CLAVE_REAL = "taller2026"

if 'acceso_concedido' not in st.session_state:
    st.session_state.acceso_concedido = False

def check_password():
    st.markdown("""<style>.stApp{background-color: #0b0f14;}</style>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 J.A.R.V.I.S. Security")
        user = st.text_input("Identidad", key="login_user")
        pwd = st.text_input("Clave de Acceso", type="password", key="login_pwd")
        
        if st.button("🔓 Acceder"):
            if user == USUARIO_REAL and pwd == CLAVE_REAL:
                st.session_state.acceso_concedido = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

if not st.session_state.acceso_concedido:
    check_password()
    st.stop()

# ---------------------------------------------------------
# 3. CONFIGURACIÓN DE IA (Opcional)
# ---------------------------------------------------------
# Intenta leer las claves de los "Secretos" de la nube
openai.api_key = st.secrets.get("OPENAI_API_KEY", None)
HUGGINGFACE_API_KEY = st.secrets.get("HUGGINGFACE_API_KEY", None)
HUGGINGFACE_MODEL = "microsoft/DialoGPT-medium"

# ---------------------------------------------------------
# 4. ESTILOS VISUALES (Modo Taller)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0b0f14; color: #c9d1d9; }
    h1, h2, h3 {color: #00d4ff !important;}
    
    /* Botones de OT */
    div.stButton > button:first-child {
        background: linear-gradient(145deg, #161b22, #21262d);
        color: #58a6ff;
        border: 2px solid #30363d;
        border-radius: 12px;
        font-size: 18px;
        padding: 18px;
        width: 100%;
        text-align: left;
        margin-bottom: 8px;
    }
    div.stButton > button:hover {
        border-color: #00d4ff;
        color: #00d4ff;
    }
    /* Botón Eliminar (Rojo) */
    .delete-btn > button {
        background: #2c1517 !important;
        color: #ff7b72 !important;
        border-color: #8c1b1f !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. FUNCIONES DEL SISTEMA
# ---------------------------------------------------------
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
OTS_FILE = os.path.join(DATA_FOLDER, "ots.json")

def load_ots():
    if os.path.exists(OTS_FILE):
        try:
            with open(OTS_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_ots(lista):
    with open(OTS_FILE, 'w') as f: json.dump(lista, f)

def ask_ai(pregunta, df, ot):
    if df is None: return "Sube un Excel primero."
    # Lógica simple de respuesta si no hay claves de IA
    if not openai.api_key and not HUGGINGFACE_API_KEY:
        return "⚠️ Configura las claves de IA en los ajustes de la web para que pueda pensar."
    return "Procesando respuesta inteligente..." # Aquí iría la conexión real

# ---------------------------------------------------------
# 6. INTERFAZ: PANTALLA PRINCIPAL
# ---------------------------------------------------------
if 'screen' not in st.session_state: st.session_state.screen = 'home'
if 'current_ot' not in st.session_state: st.session_state.current_ot = None

def render_home():
    st.title("🏭 Panel de Control")
    
    with st.expander("➕ AGREGAR NUEVA OT"):
        new_ot = st.text_input("Número de OT")
        if st.button("Crear Proyecto"):
            ots = load_ots()
            if new_ot and new_ot not in ots:
                ots.append(new_ot)
                save_ots(ots)
                st.rerun()

    st.divider()
    
    ots = load_ots()
    if not ots: st.info("No hay órdenes activas.")
    
    for ot in ots:
        c1, c2 = st.columns([5,1])
        with c1:
            if st.button(f"📂 {ot}", key=f"btn_{ot}"):
                st.session_state.current_ot = ot
                st.session_state.screen = 'detail'
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{ot}"):
                ots.remove(ot)
                save_ots(ots)
                st.rerun()

# ---------------------------------------------------------
# 7. INTERFAZ: DETALLE OT
# ---------------------------------------------------------
def render_detail():
    ot = st.session_state.current_ot
    if st.button("⬅️ VOLVER"):
        st.session_state.screen = 'home'
        st.rerun()
        
    st.title(f"🛠️ OT {ot}")
    
    uploaded = st.file_uploader("Subir Excel", type=['xlsx','csv'])
    path = os.path.join(DATA_FOLDER, f"{ot}.xlsx")
    
    if uploaded:
        if uploaded.name.endswith('.csv'): pd.read_csv(uploaded).to_excel(path)
        else:
            with open(path, "wb") as f: f.write(uploaded.getbuffer())
        st.success("Actualizado")
        st.rerun()
        
    df = pd.read_excel(path) if os.path.exists(path) else None
    
    # Buscador de Planos
    st.subheader("🔍 Buscador")
    if df is not None:
        df = df.astype(str) # Convertir todo a texto para evitar errores
        search = st.text_input("Escribe sufijo (ej: A62)")
        if search:
            res = df[df['plano'].str.contains(search, case=False, na=False)]
            st.table(res[['plano','seccion','operario','estado']].head(5))
            
    # Chat
    st.divider()
    st.subheader("🤖 J.A.R.V.I.S.")
    q = st.chat_input("Pregunta algo...")
    if q:
        st.write(f"**Tú:** {q}")
        st.info(ask_ai(q, df, ot))

# CONTROL DE NAVEGACIÓN
if st.session_state.screen == 'home': render_home()
else: render_detail()
