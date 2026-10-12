import streamlit as st
from streamlit_calendar import calendar
import sqlite3
import datetime
import pandas as pd
import hashlib
import os
import base64
import urllib.parse

st.set_page_config(
    page_title="Judit Domingo - Centre d'Estètica",
    page_icon="💆‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "gestion_estetica_v2.db"
GASTOS_DIR = "facturas_gastos"

if not os.path.exists(GASTOS_DIR):
    os.makedirs(GASTOS_DIR)

def cargar_logo_base64():
    directorio = os.path.dirname(os.path.abspath(__file__))
    nombres = ["imagen_2026-10-08_205258476.jpg", "images.jpg", "logo.jpg", "logo.png", "images.png"]
    for n in nombres:
        ruta = os.path.join(directorio, n)
        if os.path.exists(ruta):
            try:
                with open(ruta, "rb") as f:
                    enc = base64.b64encode(f.read()).decode()
                    mime = "image/png" if n.endswith(".png") else "image/jpeg"
                    return f"data:{mime};base64,{enc}"
            except Exception: pass
    return None

logo_data_uri = cargar_logo_base64()

css_logo = f"""
.stApp::before {{
    content: ""; position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%); width: 100vw; height: 100vh;
    background-image: url("{logo_data_uri}"); background-repeat: no-repeat;
    background-position: center; background-size: contain; opacity: 0.12 !important;
    pointer-events: none !important; z-index: 0 !important;
}}
""" if logo_data_uri else ""

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Great+Vibes&family=Quicksand:wght@400;500;600;700&display=swap');
    {css_logo}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 100 !important; }}
    .stApp {{ background-color: #0b0a0f !important; color: #f7f5fd !important; font-family: 'Quicksand', sans-serif !important; }}
    .block-container {{ padding: 0.5rem 0.5rem 5rem 0.5rem !important; max-width: 100% !important; z-index: 1 !important; }}
    .brand-title {{ font-family: 'Great Vibes', cursive !important; color: #e6c566 !important; font-size: 40px !important; line-height: 0.9 !important; }}
    .brand-subtext {{ font-family: 'Quicksand', sans-serif; font-size: 10px; color: #d4af37; letter-spacing: 3px; text-transform: uppercase; font-weight: 700; }}
    .card-metric {{ background: rgba(22, 19, 32, 0.9); border: 1px solid #3d3550; border-left: 4px solid #e6c566; border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 10px; }}
    .stButton>button {{ background: linear-gradient(135deg, #e6c566 0%, #ba9530 100%) !important; color: #1a1600 !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; width: 100% !important; }}
    .stLinkButton>a {{ background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important; color: #ffffff !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; text-decoration: none !important; display: block !important; text-align: center !important; width: 100% !important; }}
    
    @keyframes botSaludo {{
        0% {{ transform: rotate(0deg) scale(1); }}
        15% {{ transform: rotate(14deg) scale(1.1); }}
        30% {{ transform: rotate(-12deg) scale(1.1); }}
        45% {{ transform: rotate(10deg) scale(1.05); }}
        60% {{ transform: rotate(0deg) scale(1); }}
        100% {{ transform: rotate(0deg) scale(1); }}
    }}
    div[data-testid="stPopover"] {{ position: fixed !important; bottom: 25px !important; right: 25px !important; z-index: 999999 !important; }}
    div[data-testid="stPopover"] > button {{ animation: botSaludo 3.2s infinite ease-in-out !important; background: linear-gradient(135deg, #ba9530 0%, #e6c566 100%) !important; color: #0d0c12 !important; font-weight: 800 !important; font-size: 15px !important; border-radius: 50px !important; padding: 12px 22px !important; box-shadow: 0 6px 20px rgba(230, 197, 102, 0.5) !important; border: 2px solid #fff3c4 !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 10px 10px 0 0 !important; padding: 10px 16px !important; background-color: rgba(18, 16, 26, 0.95) !important; color: #bfa8db !important; font-weight: 700 !important; }}
    .stTabs [aria-selected="true"] {{ background-color: rgba(38, 32, 54, 0.95) !important; color: #e6c566 !important; border-bottom: 3px solid #e6c566 !important; }}
    .fc {{ font-size: 12px !important; font-family: 'Quicksand', sans-serif !important; background-color: rgba(15, 14, 22, 0.88) !important; border-radius: 12px; padding: 6px; }}
    .fc-timegrid-slot {{ height: 40px !important; }}
    .fc-timegrid-slot-label-frame {{ text-align: center !important; font-size: 11px !important; font-weight: 600 !important; color: #d4af37 !important; }}
    </style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, primer_apellido TEXT, segundo_apellido TEXT, sexo TEXT, telefono TEXT, telefono_fijo TEXT, email TEXT, dni TEXT, direccion TEXT, ciudad TEXT, cp TEXT, fecha_nacimiento TEXT, notas TEXT, info_clinica TEXT, monedero REAL DEFAULT 0.0, rgpd INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS servicios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, duracion_min INTEGER NOT NULL, precio REAL NOT NULL, color TEXT DEFAULT '#9b59b6')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS citas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL, cliente_id INTEGER, servicio_id INTEGER, notas TEXT, estado_cobro TEXT DEFAULT 'Pendiente', metodo_pago TEXT, monto_cobrado REAL DEFAULT 0.0, FOREIGN KEY(cliente_id) REFERENCES clientes(id), FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cajas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT UNIQUE NOT NULL, abonos_efectivo REAL DEFAULT 0.0, abonos_tarjeta REAL DEFAULT 0.0, abonos_bizum REAL DEFAULT 0.0, ingresos REAL DEFAULT 0.0, extracciones REAL DEFAULT 0.0, descuadre REAL DEFAULT 0.0, total_caja REAL DEFAULT 0.0, estado TEXT DEFAULT 'Cerrada')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY AUTOINCREMENT, num_factura TEXT UNIQUE, fecha_hora TEXT, concepto TEXT, total REAL, metodo_pago TEXT, hash_registro TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS lista_espera (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, servicio_id INTEGER NOT NULL, preferencia_horario TEXT, fecha_registro TEXT, estado TEXT DEFAULT 'Pendiente', FOREIGN KEY(cliente_id) REFERENCES clientes(id), FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS consentimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, tipo_tratamiento TEXT NOT NULL, fecha_firma TEXT NOT NULL, acepta_rgpd INTEGER DEFAULT 1, firma_texto TEXT, FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, proveedor TEXT NOT NULL, concepto TEXT NOT NULL, categoria TEXT NOT NULL, base_imponible REAL NOT NULL, iva_porcentaje REAL DEFAULT 21.0, total REAL NOT NULL, ruta_factura TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, categoria TEXT DEFAULT 'Producto Venta', precio_coste REAL NOT NULL, pvp REAL NOT NULL, unidades INTEGER NOT NULL, minimo_alerta INTEGER DEFAULT 2)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarjetas_regalo (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, comprador TEXT NOT NULL, beneficiario TEXT NOT NULL, concepto TEXT NOT NULL, saldo_inicial REAL NOT NULL, saldo_actual REAL NOT NULL, fecha_emision TEXT NOT NULL, fecha_caducidad TEXT, estado TEXT DEFAULT 'Activa')''')
    
    # MIGRACIÓN AUTOMÁTICA DE COLUMNAS PARA EVITAR ERRORES DE BASE DE DATOS
    cursor.execute("PRAGMA table_info(clientes)")
    cols_cli = [row[1] for row in cursor.fetchall()]
    if "info_clinica" not in cols_cli:
        try: cursor.execute("ALTER TABLE clientes ADD COLUMN info_clinica TEXT")
        except: pass

    cursor.execute("SELECT COUNT(*) FROM servicios")
    if cursor.fetchone()[0] == 0:
        servicios_def = [("Manicura Semipermanente", 45, 25.0, "#e74c3c"), ("Acrylgel uñas largas", 60, 40.0, "#9b59b6"), ("Higiene Facial Profunda", 60, 45.0, "#3498db"), ("Maderoterapia Corporal", 60, 50.0, "#2ecc71")]
        cursor.executemany("INSERT INTO servicios (nombre, duracion_min, precio, color) VALUES (?,?,?,?)", servicios_def)
    conn.commit()
    conn.close()

init_db()

def generar_link_whatsapp(telefono, texto):
    tel = "".join(filter(str.isdigit, str(telefono or "")))
    if len(tel) == 9 and not tel.startswith("34"): tel = f"34{tel}"
    return f"https://api.whatsapp.com/send?phone={tel}&text={urllib.parse.quote(texto)}"

def renderizar_tarjeta_regalo_html(codigo, comprador, beneficiario, concepto, importe):
    logo_html = f'<img src="{logo_data_uri}" style="max-width:300px; max-height:200px; opacity:0.25; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1;">' if logo_data_uri else ''
    return f"""
    <div style="position:relative; width:100%; max-width:650px; margin:0 auto; background:#0f0e15; border:3px solid #e6c566; border-radius:18px; padding:25px; color:#fff; font-family:'Quicksand', sans-serif;">
        {logo_html}
        <div style="position:relative; z-index:2;">
            <div style="text-align:center; margin-bottom:15px;">
                <div style="font-family:'Great Vibes', cursive; font-size:46px; color:#e6c566; line-height:1;">Judit Domingo</div>
                <div style="font-size:11px; color:#d4af37; letter-spacing:3px; font-weight:700;">CENTRE D'ESTÈTICA — TARJETA REGALO</div>
            </div>
            <div style="background:rgba(22,19,32,0.85); border:1px solid #3d3550; border-radius:12px; padding:15px; margin-bottom:15px;">
                <div style="font-size:17px; margin-bottom:6px;"><b>Para:</b> {beneficiario}</div>
                <div style="font-size:15px; color:#dcd6f7; margin-bottom:6px;"><b>De:</b> {comprador}</div>
                <div style="font-size:15px; color:#e6c566;"><b>Tratamiento:</b> {concepto}</div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size:13px; color:#a29bfe; font-weight:600;">Código: {codigo}</div>
                <div style="background:linear-gradient(135deg, #e6c566 0%, #ba9530 100%); color:#1a1600; font-weight:800; font-size:22px; padding:8px 20px; border-radius:10px;">{importe:.2f} €</div>
            </div>
        </div>
    </div>
    """
# MODALES Y GESTIÓN DE CITAS (CON HORA EXACTA Y SIN DESFASE)
@st.dialog("➕ Agendar Nueva Cita")
def modal_crear_cita(fecha_por_defecto=None, hora_por_defecto=None):
    conn = sqlite3.connect(DB_NAME)
    df_c = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes ORDER BY nombre ASC", conn)
    df_s = pd.read_sql_query("SELECT id, nombre, duracion_min, precio FROM servicios ORDER BY nombre ASC", conn)
    conn.close()

    if df_c.empty or df_s.empty:
        st.warning("Debes dar de alta al menos 1 cliente y 1 servicio antes de agendar.")
        return

    f_init = datetime.date.today()
    if fecha_por_defecto:
        try: f_init = datetime.date.fromisoformat(fecha_por_defecto)
        except: pass

    h_init = datetime.time(10, 0)
    if hora_por_defecto:
        try:
            parts = hora_por_defecto.split(":")
            h_init = datetime.time(int(parts[0]), int(parts[1]))
        except: pass

    col1, col2 = st.columns(2)
    with col1: fecha_cita = st.date_input("Fecha Cita", value=f_init)
    with col2: hora_cita = st.time_input("Hora Inicio", value=h_init)

    opciones_cli = [0] + list(df_c["id"])
    dict_cli = {0: "--- Selecciona Clienta ---"}
    for _, r in df_c.iterrows(): dict_cli[r["id"]] = r["nom"]

    c_sel = st.selectbox("Clienta *", options=opciones_cli, format_func=lambda x: dict_cli[x])
    s_sel = st.selectbox("Servicio / Tratamiento *", options=df_s["id"], format_func=lambda x: df_s[df_s["id"]==x]["nombre"].values[0])
    obs = st.text_input("Observaciones / Notas")

    if st.button("💾 Confirmar y Guardar Cita", type="primary", use_container_width=True):
        if c_sel == 0:
            st.error("Por favor, selecciona una clienta.")
            return

        dur_min = int(df_s[df_s["id"] == s_sel]["duracion_min"].values[0])
        dt_ini = datetime.datetime.combine(fecha_cita, hora_cita)
        dt_fin = dt_ini + datetime.timedelta(minutes=dur_min)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO citas (fecha_inicio, fecha_fin, cliente_id, servicio_id, notas) VALUES (?,?,?,?,?)",
                       (dt_ini.strftime("%Y-%m-%dT%H:%M:%S"), dt_fin.strftime("%Y-%m-%dT%H:%M:%S"), c_sel, s_sel, obs))
        conn.commit()
        conn.close()
        st.success("¡Cita agendada correctamente!")
        st.rerun()

@st.dialog("⚙️ Detalle de Cita")
def modal_editar_cita(cita_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.precio, c.estado_cobro, c.metodo_pago, c.monto_cobrado, c.notas
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id WHERE c.id = ?""", (cita_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("No se encontró la cita.")
        return

    f_i, f_f, cl_n, cl_ap, cl_tel, s_n, s_pre, est_c, met_p, monto_c, obs = row
    nom_cli = f"{cl_n} {cl_ap or ''}".strip()
    dt_i = datetime.datetime.fromisoformat(f_i.replace("Z", ""))

    st.markdown(f"### 💆‍♀️ {s_n}")
    st.markdown(f"👤 **Cliente:** {nom_cli}")
    st.markdown(f"📅 **Fecha:** {dt_i.strftime('%d/%m/%Y')} a las {dt_i.strftime('%H:%M')}h")
    if obs: st.info(f"📝 **Notas:** {obs}")

    st.markdown("---")
    if est_c == "Cobrado":
        st.success(f"✅ **Cobrado:** {monto_c:.2f}€ en {met_p}")
    else:
        st.warning(f"⏳ **Cobro Pendiente:** {s_pre:.2f}€")
        if st.button("💶 Cobrar Servicio Ahora", use_container_width=True):
            modal_cobrar_cita(cita_id, nom_cli, s_n, s_pre)

    st.markdown("#### 💬 Recordatorio WhatsApp")
    tel_destino = cl_tel if (cl_tel and str(cl_tel).strip() != "") else st.text_input("Número WhatsApp", placeholder="Ej. 612345678", key=f"tel_m_{cita_id}")
    if tel_destino:
        txt_wa = f"Hola {nom_cli}! ✨ Te recordamos tu cita en *Judit Domingo - Centre d'Estètica* para *{s_n}* el día *{dt_i.strftime('%d/%m/%Y')}* a las *{dt_i.strftime('%H:%M')}h*. ¡Te esperamos! 💆‍♀️"
        st.link_button("📲 Enviar Recordatorio por WhatsApp", generar_link_whatsapp(tel_destino, txt_wa), use_container_width=True)

    st.markdown("---")
    if st.button("🗑️ Eliminar Cita", use_container_width=True):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
        conn.commit()
        conn.close()
        st.success("Cita eliminada.")
        st.rerun()

@st.dialog("💶 Cobrar Servicio")
def modal_cobrar_cita(cita_id, cliente_nom, servicio_nom, precio_def):
    st.markdown(f"**Cliente:** {cliente_nom} | **Servicio:** {servicio_nom}")
    c1, c2 = st.columns(2)
    with c1: monto = st.number_input("Importe (€)", value=float(precio_def), step=1.0)
    with c2: metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Bizum", "Monedero Clienta", "Tarjeta Regalo"])

    if st.button("✅ Confirmar Cobro", type="primary", use_container_width=True):
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE citas SET estado_cobro='Cobrado', metodo_pago=?, monto_cobrado=? WHERE id=?", (metodo, monto, cita_id))
        
        if metodo not in ["Tarjeta Regalo", "Monedero Clienta"]:
            cursor.execute("SELECT id, abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja FROM cajas WHERE fecha=?", (hoy_str,))
            row_caja = cursor.fetchone()
            if row_caja:
                c_id, ef, tar, biz, ing, tot = row_caja
                cursor.execute("UPDATE cajas SET abonos_efectivo=?, abonos_tarjeta=?, abonos_bizum=?, ingresos=?, total_caja=?, estado='Abierta' WHERE id=?",
                               (ef + (monto if metodo == "Efectivo" else 0), tar + (monto if metodo == "Tarjeta" else 0),
                                biz + (monto if metodo == "Bizum" else 0), ing + monto, tot + monto, c_id))
            else:
                cursor.execute("INSERT INTO cajas (fecha, abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja, estado) VALUES (?,?,?,?,?,?,'Abierta')",
                               (hoy_str, monto if metodo == "Efectivo" else 0, monto if metodo == "Tarjeta" else 0, monto if metodo == "Bizum" else 0, monto, monto))

        num_f = f"F{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        fecha_h = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("SELECT hash_registro FROM facturas ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        hash_ant = last_row[0] if last_row else "0"*32
        hash_reg = hashlib.sha256(f"{num_f}|{fecha_h}|{monto:.2f}|{hash_ant}".encode()).hexdigest()
        
        cursor.execute("INSERT INTO facturas (num_factura, fecha_hora, concepto, total, metodo_pago, hash_registro) VALUES (?,?,?,?,?,?)",
                       (num_f, fecha_h, f"{servicio_nom} - {cliente_nom}", monto, metodo, hash_reg))

        conn.commit()
        conn.close()
        st.success("¡Cobro y factura registrados!")
        st.rerun()
# 4. INTERFAZ EN 5 BLOQUES COMPLETOS
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("""
        <div>
            <div class="brand-title">Judit Domingo</div>
            <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
        </div>
    """, unsafe_allow_html=True)

bloques = st.tabs([
    "📅 Agenda & Citas", 
    "💶 Caja & Finanzas", 
    "👤 Gestión Centro", 
    "📣 Marketing & Regalos", 
    "📊 Analítica & Legal"
])

# BLOQUE 1: AGENDA (CON ZONA HORARIA LOCAL CORREGIDA)
with bloques[0]:
    col_a1, col_a2 = st.columns([7, 3])
    with col_a1: st.subheader("Agenda de Citas")
    with col_a2:
        if st.button("➕ Agendar Nueva Cita", use_container_width=True, type="primary"):
            modal_crear_cita()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.id, c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, s.nombre, s.color, c.estado_cobro 
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id""")
    citas_db = cursor.fetchall()
    conn.close()

    events = [{
        "id": f"cita_{r[0]}",
        "title": f"{'✅ ' if r[7]=='Cobrado' else ''}[{r[3]} {r[4] or ''}] {r[5]}",
        "start": r[1], "end": r[2],
        "backgroundColor": "#2ecc71" if r[7]=="Cobrado" else r[6],
        "borderColor": r[6]
    } for r in citas_db]

    cal_opts = {
        "timeZone": "local",
        "locale": "es", "initialView": "timeGridWeek", "firstDay": 1,
        "slotMinTime": "08:30:00", "slotMaxTime": "20:30:00", "slotDuration": "00:30:00", "height": 700, "selectable": True,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "timeGridWeek,timeGridDay"}
    }

    st_cal = calendar(events=events, options=cal_opts, key="app_cal_pro_v5")

    if st_cal.get("eventClick"):
        raw_id = st_cal["eventClick"]["event"]["id"]
        if raw_id.startswith("cita_"):
            modal_editar_cita(int(raw_id.replace("cita_", "")))

    if st_cal.get("dateClick"):
        click_str = st_cal["dateClick"]["date"]
        clean_str = click_str.replace("Z", "").split("+")[0]
        f_def = clean_str[:10]
        h_def = clean_str[11:16] if len(clean_str) >= 16 else "10:00"
        modal_crear_cita(f_def, h_def)

# BLOQUE 2: CAJA & FINANZAS
with bloques[1]:
    tab_f1, tab_f2 = st.tabs(["💳 Caja del Día", "🏛️ Fiscal & Gastos"])

    with tab_f1:
        st.subheader("Arqueo de Caja del Día")
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja FROM cajas WHERE fecha = ?", (hoy_str,))
        caja_hoy = cursor.fetchone() or (0.0, 0.0, 0.0, 0.0, 0.0)
        conn.close()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("💵 Efectivo", f"{caja_hoy[0]:.2f} €")
        with col2: st.metric("💳 Tarjeta", f"{caja_hoy[1]:.2f} €")
        with col3: st.metric("📲 Bizum", f"{caja_hoy[2]:.2f} €")
        with col4: st.metric("🏆 Total Hoy", f"{caja_hoy[3]:.2f} €")

        st.markdown("### 📋 Citas Agendadas Hoy")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""SELECT c.id, c.fecha_inicio, cl.nombre, cl.primer_apellido, s.nombre, s.precio, c.estado_cobro, c.metodo_pago, c.monto_cobrado
                          FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id
                          WHERE DATE(c.fecha_inicio) = ? ORDER BY c.fecha_inicio ASC""", (hoy_str,))
        citas_hoy = cursor.fetchall()
        conn.close()

        for cita_h in citas_hoy:
            c_id, f_i, c_nom, c_p_ap, s_nom, s_precio, est_cobro, met_pago, monto_cob = cita_h
            hora_cita = datetime.datetime.fromisoformat(f_i.replace("Z", "")).strftime("%H:%M")
            nom_cliente = f"{c_nom} {c_p_ap or ''}".strip()

            col_a, col_b, col_c = st.columns([4, 3, 2])
            with col_a: st.markdown(f"**⏰ {hora_cita}h** — {nom_cliente} (*{s_nom}*)")
            with col_b:
                if est_cobro == "Cobrado": st.success(f"✅ Cobrado: {monto_cob:.2f}€ ({met_pago})")
                else: st.warning(f"⏳ Pendiente: {s_precio:.2f}€")
            with col_c:
                if est_cobro != "Cobrado":
                    if st.button("💶 Cobrar", key=f"cobrar_hoy_{c_id}"):
                        modal_cobrar_cita(c_id, nom_cliente, s_nom, s_precio)

    with tab_f2:
        st.subheader("🏛️ Control Fiscal Trimestral")
        conn = sqlite3.connect(DB_NAME)
        df_f_ing = pd.read_sql_query("SELECT total FROM facturas", conn)
        df_f_gas = pd.read_sql_query("SELECT base_imponible, total FROM gastos", conn)
        conn.close()

        total_ventas = df_f_ing['total'].sum() if not df_f_ing.empty else 0.0
        iva_repercutido = total_ventas * 0.21
        total_gastos_base = df_f_gas['base_imponible'].sum() if not df_f_gas.empty else 0.0
        total_gastos_iva = (df_f_gas['total'] - df_f_gas['base_imponible']).sum() if not df_f_gas.empty else 0.0

        iva_a_pagar = iva_repercutido - total_gastos_iva
        rendimiento_neto = total_ventas - (total_gastos_base + total_gastos_iva)

        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1: st.markdown(f"<div class='card-metric'><h4>📊 IVA a Liquidar (Mod 303)</h4><h2 style='color:#e6c566;'>{iva_a_pagar:.2f} €</h2></div>", unsafe_allow_html=True)
        with c_m2: st.markdown(f"<div class='card-metric'><h4>📈 IRPF Estimado (Mod 130)</h4><h2 style='color:#74b9ff;'>{max(0.0, rendimiento_neto*0.2):.2f} €</h2></div>", unsafe_allow_html=True)
        with c_m3: st.markdown(f"<div class='card-metric'><h4>💵 Rendimiento Neto</h4><h2 style='color:#55efc4;'>{rendimiento_neto:.2f} €</h2></div>", unsafe_allow_html=True)

# BLOQUE 3: GESTIÓN DE CENTRO (CON COMPROBACIÓN SEGURA DE COLUMNAS)
with bloques[2]:
    tab_g1, tab_g2, tab_g3 = st.tabs(["👤 Fichero Clientes", "💆‍♀️ Tratamientos", "📦 Control Stock"])

    with tab_g1:
        st.subheader("👤 Fichero de Clientes")
        with st.expander("➕ Dar de Alta Nueva Clienta"):
            col_cli1, col_cli2 = st.columns(2)
            with col_cli1:
                c_n = st.text_input("Nombre *")
                c_a = st.text_input("Primer Apellido")
                c_a2 = st.text_input("Segundo Apellido")
                c_t = st.text_input("Móvil (WhatsApp) *")
            with col_cli2:
                c_e = st.text_input("Email")
                c_dni = st.text_input("DNI / NIE")
                c_fnac = st.text_input("Fecha Nacimiento (AAAA-MM-DD)")
                c_obs = st.text_input("Notas Clínicas / Alergias")

            if st.button("💾 Guardar Ficha Clienta", type="primary", use_container_width=True):
                if c_n and c_t:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""INSERT INTO clientes (nombre, primer_apellido, segundo_apellido, telefono, email, dni, fecha_nacimiento, info_clinica)
                                      VALUES (?,?,?,?,?,?,?,?)""", (c_n, c_a, c_a2, c_t, c_e, c_dni, c_fnac, c_obs))
                    conn.commit()
                    conn.close()
                    st.success("¡Clienta registrada!")
                    st.rerun()

        conn = sqlite3.connect(DB_NAME)
        cols = [info[1] for info in conn.execute("PRAGMA table_info(clientes)").fetchall()]
        col_med = "info_clinica" if "info_clinica" in cols else "notas"
        df_cli = pd.read_sql_query(f"SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as 'Nombre', telefono as 'Móvil', email as 'Email', COALESCE({col_med},'') as 'Notas Médicas' FROM clientes ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_cli, use_container_width=True)

    with tab_g2:
        st.subheader("💆‍♀️ Catálogo de Tratamientos")
        conn = sqlite3.connect(DB_NAME)
        df_serv = pd.read_sql_query("SELECT nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)' FROM servicios", conn)
        conn.close()
        st.dataframe(df_serv, use_container_width=True)

    with tab_g3:
        st.subheader("📦 Control de Stock")
        conn = sqlite3.connect(DB_NAME)
        df_st = pd.read_sql_query("SELECT nombre as 'Producto', categoria as 'Tipo', pvp as 'PVP (€)', unidades as 'Stock', minimo_alerta as 'Alerta Mínima' FROM stock", conn)
        conn.close()
        st.dataframe(df_st, use_container_width=True)

# BLOQUE 4: MARKETING & REGALOS
with bloques[3]:
    tab_m1, tab_m2, tab_m3 = st.tabs(["🎁 Tarjetas Regalo", "🎂 Cumpleaños", "💬 Promociones"])

    with tab_m1:
        st.markdown("### 🎁 Crear Nueva Tarjeta Regalo")
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            tr_comprador = st.text_input("Comprador/a *")
            tr_beneficiario = st.text_input("Beneficiario/a *")
            tr_concepto = st.text_input("Concepto / Tratamiento *", value="Tratamiento Facial VIP / Maderoterapia")
        with col_tr2:
            tr_importe = st.number_input("Importe (€) *", value=50.0, step=5.0)
            tr_tel_envio = st.text_input("Móvil Beneficiaria")

        if st.button("🎁 Emitir y Guardar Tarjeta Regalo", use_container_width=True, type="primary"):
            if tr_comprador and tr_beneficiario:
                cod_tr = f"TR-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO tarjetas_regalo (codigo, comprador, beneficiario, concepto, saldo_inicial, saldo_actual, fecha_emision, estado)
                                  VALUES (?,?,?,?,?,?,?,'Activa')""",
                               (cod_tr, tr_comprador, tr_beneficiario, tr_concepto, tr_importe, tr_importe, datetime.date.today().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success(f"¡Tarjeta Regalo {cod_tr} Emitida!")
                st.components.v1.html(renderizar_tarjeta_regalo_html(cod_tr, tr_comprador, tr_beneficiario, tr_concepto, tr_importe), height=320)

                if tr_tel_envio:
                    msg_tr = f"¡Hola {tr_beneficiario}! 🎁 Te han regalado una Tarjeta Regalo por valor de {tr_importe:.2f}€ en Judit Domingo Centre d'Estètica. ¡Llámanos para agendar!"
                    st.link_button("📲 Notificar por WhatsApp", generar_link_whatsapp(tr_tel_envio, msg_tr), use_container_width=True)

    with tab_m2:
        st.markdown("### 🎂 Cumpleaños del Mes")
        mes_actual = datetime.date.today().strftime("%m")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre || ' ' || COALESCE(primer_apellido,''), telefono, fecha_nacimiento FROM clientes WHERE fecha_nacimiento LIKE ?", (f"%-{mes_actual}-%",))
        cump_rows = cursor.fetchall()
        conn.close()

        for nom_c, tel_c, fnac_c in cump_rows:
            col1, col2 = st.columns([3, 1])
            with col1: st.markdown(f"🎉 **{nom_c}** ({fnac_c})")
            with col2:
                if tel_c:
                    msg_cump = f"¡Feliz Cumpleaños {nom_c}! 🥳✨ Tienes un regalo esperándote en Judit Domingo Centre d'Estètica."
                    st.link_button("📲 Felicitar", generar_link_whatsapp(tel_c, msg_cump), use_container_width=True)

    with tab_m3:
        st.markdown("### 💬 Difusión y Promociones")
        st.text_area("Texto Promocional para WhatsApp", value="Hola! ✨ Novedad en Judit Domingo Centre d'Estètica. Hemos abierto agenda para el nuevo tratamiento. ¡Reserva tu plaza!", height=100)

# BLOQUE 5: ANALÍTICA & LEGAL
with bloques[4]:
    tab_a1, tab_a2, tab_a3 = st.tabs(["📈 Estadísticas", "✍️ RGPD & Firmas", "⏳ Lista Espera"])

    with tab_a1:
        st.subheader("📈 Centro de Analítica")
        conn = sqlite3.connect(DB_NAME)
        df_citas_cob = pd.read_sql_query("""SELECT c.monto_cobrado, s.nombre as servicio
                                            FROM citas c JOIN servicios s ON c.servicio_id = s.id WHERE c.estado_cobro='Cobrado'""", conn)
        conn.close()

        if not df_citas_cob.empty:
            c1, c2 = st.columns(2)
            with c1: st.metric("💶 Facturación Acumulada", f"{df_citas_cob['monto_cobrado'].sum():.2f} €")
            with c2: st.metric("🎟️ Ticket Medio", f"{df_citas_cob['monto_cobrado'].mean():.2f} €")
            st.bar_chart(df_citas_cob["servicio"].value_counts())

    with tab_a2:
        st.subheader("✍️ Firma Digital RGPD")
        conn = sqlite3.connect(DB_NAME)
        df_cli_sel = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
        conn.close()

        if not df_cli_sel.empty:
            c_sel = st.selectbox("Clienta *", options=df_cli_sel["id"], format_func=lambda x: df_cli_sel[df_cli_sel["id"]==x]["nom"].values[0])
            tipo_t = st.selectbox("Tratamiento", ["Maderoterapia Corporal", "Higiene Facial Profunda", "Acrylgel"])
            nombre_f = st.text_input("Nombre Completo (Firma Digital) *")

            if st.button("✍️ Guardar Firma Consentimiento", use_container_width=True):
                if nombre_f:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO consentimientos (cliente_id, tipo_tratamiento, fecha_firma, acepta_rgpd, firma_texto) VALUES (?,?,?,?,?)",
                                   (c_sel, tipo_t, datetime.date.today().strftime("%Y-%m-%d"), 1, nombre_f))
                    conn.commit()
                    conn.close()
                    st.success("¡Consentimiento guardado con éxito!")

    with tab_a3:
        st.subheader("⏳ Lista de Espera")
        conn = sqlite3.connect(DB_NAME)
        df_le = pd.read_sql_query("""SELECT le.id, cl.nombre || ' ' || COALESCE(cl.primer_apellido,'') as 'Clienta', cl.telefono as 'Móvil', s.nombre as 'Tratamiento'
                                     FROM lista_espera le JOIN clientes cl ON le.cliente_id = cl.id JOIN servicios s ON le.servicio_id = s.id WHERE le.estado='Pendiente'""", conn)
        conn.close()
        st.dataframe(df_le, use_container_width=True)

# BOT ASISTENTE FLOTANTE
with st.popover("🤖 Bot Asistente (👋)", help="Haz clic para chatear con el asistente"):
    st.markdown("### 🤖 Asistente del Centro")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [{"role": "assistant", "content": "¡Hola Judit y Adri! 💆‍♀️ ¿En qué puedo ayudaros hoy?"}]

    for m in st.session_state["chat_history"]:
        st.chat_message(m["role"]).write(m["content"])

    if user_p := st.chat_input("Escribe tu duda..."):
        st.session_state["chat_history"].append({"role": "user", "content": user_p})
        st.chat_message("user").write(user_p)
        
        p = user_p.lower()
        if "caja" in p or "cobrar" in p:
            resp = "Para cobrar una cita, pulsa directamente sobre ella en la agenda o en la lista de citas de '💶 Caja & Finanzas'."
        elif "maderoterapia" in p:
            resp = "La Maderoterapia corporal drena líquidos y remodela la figura. Se recomiendan sesiones de 60 minutos."
        elif "llamo" in p or "nombre" in p or "quien soy" in p:
            resp = "¡Sois Judit y Adri! Esta aplicación es vuestro gestor personalizado para Judit Domingo - Centre d'Estètica."
        elif "iva" in p or "impuesto" in p:
            resp = "En '💶 Caja & Finanzas' > '🏛️ Fiscal & Gastos' tienes el cálculo del Modelo 303 (IVA) y Modelo 130 (IRPF)."
        else:
            resp = f"Entendido, he procesado tu consulta sobre '{user_p}'. ¿Necesitas ayuda con la agenda o la contabilidad?"

        st.session_state["chat_history"].append({"role": "assistant", "content": resp})
        st.chat_message("assistant").write(resp)
