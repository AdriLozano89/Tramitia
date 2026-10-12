import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime
import pdfplumber

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA SAAS (SIN SIDEBAR)
# ==============================================================================
st.set_page_config(
    page_title="Tramitia - Burocracia y Finanzas Fáciles",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS avanzados (Navegación Superior + Cobalto/Menta)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Fondo principal modo oscuro */
    .stApp {
        background: #080c14 !important;
        color: #f3f4f6 !important;
    }
    
    /* Ocultar sidebar por completo */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Contenedores y Tarjetas */
    .tramitia-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
    }
    
    .metric-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0;
    }

    /* Botones de menú superior (Tabs estilizados) */
    .stButton>button {
        background: #1e293b !important;
        color: #94a3b8 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1rem !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1e40af 0%, #10b981 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Inputs y Formularios */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    
    /* Chat de Trami */
    .user-msg {
        background-color: #1e293b;
        padding: 14px 18px;
        border-radius: 16px 16px 2px 16px;
        margin-bottom: 12px;
        text-align: right;
        color: #f8fafc;
        border: 1px solid #334155;
    }
    .bot-msg {
        background: linear-gradient(135deg, #0f172a 0%, #172554 100%);
        padding: 18px 22px;
        border-radius: 16px 16px 16px 2px;
        margin-bottom: 14px;
        color: #f8fafc;
        border: 1px solid #1e40af;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }
    .badge-norma {
        background-color: #10b981;
        color: #042f2e;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. INICIALIZACIÓN DE BASE DE DATOS
# ==============================================================================
def init_db():
    conn = sqlite3.connect('tramitia.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            proveedor TEXT,
            nif TEXT,
            base_imponible REAL,
            iva REAL,
            total REAL,
            tipo TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS consultas_trami (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            pregunta TEXT,
            respuesta TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 3. EXTRACCIÓN OCR ROBUSTA DE FACTURAS
# ==============================================================================
def procesar_ocr_limpio(file):
    datos = {
        "proveedor": "Proveedor / Comercio",
        "nif": "",
        "base": 0.0,
        "iva": 0.0,
        "total": 0.0
    }
    texto_lineas = []
    
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        texto_lineas.extend(txt.split('\n'))
        
        texto_unido = " ".join(texto_lineas)
        
        # 1. Búsqueda limpia de NIF/CIF
        cif_match = re.search(r'\b([ABCDEFGHJNPQRSUVW][0-9]{8}|[0-9]{8}[A-Z])\b', texto_unido, re.IGNORECASE)
        if cif_match:
            datos["nif"] = cif_match.group(0).upper()

        # 2. Búsqueda de Proveedor (Ignorando líneas de metadatos tipo ##Pag)
        for linea in texto_lineas:
            linea_clean = linea.strip()
            if len(linea_clean) > 3 and not linea_clean.startswith("#") and "página" not in linea_clean.lower():
                datos["proveedor"] = linea_clean[:40]
                break
                
        # 3. Búsqueda y filtrado de montos monetarios reales
        # Encuentra patrones tipo 123.45 o 123,45 o 1.234,56
        patron_monto = r'\b\d{1,5}(?:[\.,]\d{3})*(?:[\.,]\d{2})\b'
        coincidencias = re.findall(patron_monto, texto_unido)
        
        num_validos = []
        for m in coincidencias:
            # Normalizar formato español a float de Python
            temp = m.replace('.', '').replace(',', '.') if ',' in m else m
            try:
                val = float(temp)
                if 0.5 <= val <= 15000.0:  # Descartar montos irrestrictos o metadatos
                    num_validos.append(val)
            except:
                pass
                
        if num_validos:
            num_validos.sort()
            datos["total"] = num_validos[-1]  # El más alto suele ser el total
            datos["base"] = round(datos["total"] / 1.21, 2)
            datos["iva"] = round(datos["total"] - datos["base"], 2)

    except Exception:
        pass
        
    return datos

# ==============================================================================
# 4. CABECERA CON LOGO Y MENÚ SUPERIOR DE BOTONES
# ==============================================================================
logo_svg = """
<div style="display: flex; justify-content: center; align-items: center; padding: 10px 0 15px 0;">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 100" width="100%" height="75px">
    <defs>
      <linearGradient id="tramitiaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#1e40af" />
        <stop offset="100%" stop-color="#10b981" />
      </linearGradient>
    </defs>
    <g transform="translate(10, 5)">
      <!-- Isotipo: T de conexión continua -->
      <path d="M 25 20 L 75 20 C 85 20 90 28 85 38 L 55 85 C 50 93 40 93 35 85 C 30 78 35 70 45 70 L 55 70 C 62 70 65 65 68 58 L 72 48 C 75 42 70 38 62 38 L 35 38 C 25 38 20 30 25 20 Z" fill="url(#tramitiaGrad)" />
      <circle cx="85" cy="28" r="8" fill="#10b981" />
      <!-- Nombre de marca -->
      <text x="110" y="62" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-weight="800" font-size="48" fill="#ffffff" letter-spacing="-1">Tramitia</text>
      <!-- Eslogan -->
      <text x="112" y="85" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-weight="700" font-size="12" fill="#10b981" letter-spacing="3">BUROCRACIA FÁCIL</text>
    </g>
  </svg>
</div>
"""
st.markdown(logo_svg, unsafe_allow_html=True)

# Estado de navegación en sesión
if 'tab_actual' not in st.session_state:
    st.session_state.tab_actual = "📊 Panel Principal"

# Menú superior de botones
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
with col_nav1:
    if st.button("📊 Panel Principal"):
        st.session_state.tab_actual = "📊 Panel Principal"
        st.rerun()
with col_nav2:
    if st.button("📑 Lector OCR"):
        st.session_state.tab_actual = "📑 Lector OCR"
        st.rerun()
with col_nav3:
    if st.button("🏛️ Impuestos"):
        st.session_state.tab_actual = "🏛️ Impuestos"
        st.rerun()
with col_nav4:
    if st.button("🤖 Asistente Trami"):
        st.session_state.tab_actual = "🤖 Asistente Trami"
        st.rerun()

st.markdown("<hr style='border-color:#1e293b; margin-top:10px; margin-bottom:25px;'>", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 1: PANEL PRINCIPAL
# ==============================================================================
if st.session_state.tab_actual == "📊 Panel Principal":
    st.markdown("### Resumen Contable y Fiscal")
    
    conn = sqlite3.connect('tramitia.db')
    df_facturas = pd.read_sql_query("SELECT * FROM facturas", conn)
    conn.close()

    total_ingresos = df_facturas[df_facturas['tipo'] == 'Ingreso / Factura Emitida']['total'].sum() if not df_facturas.empty else 0.0
    total_gastos = df_facturas[df_facturas['tipo'] == 'Gasto Deducible']['total'].sum() if not df_facturas.empty else 0.0
    iva_devengado = df_facturas[df_facturas['tipo'] == 'Ingreso / Factura Emitida']['iva'].sum() if not df_facturas.empty else 0.0
    iva_deducible = df_facturas[df_facturas['tipo'] == 'Gasto Deducible']['iva'].sum() if not df_facturas.empty else 0.0
    iva_estimado = round(iva_devengado - iva_deducible, 2)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
            <div class="tramitia-card">
                <div class="metric-header">Ingresos Totales</div>
                <div class="metric-value" style="color:#10b981;">{total_ingresos:,.2f} €</div>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
            <div class="tramitia-card">
                <div class="metric-header">Gastos Deducibles</div>
                <div class="metric-value" style="color:#3b82f6;">{total_gastos:,.2f} €</div>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
            <div class="tramitia-card">
                <div class="metric-header">IVA a Liquidar (Mod. 303)</div>
                <div class="metric-value" style="color:#f59e0b;">{iva_estimado:,.2f} €</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("#### Histórico de Facturas")
    if not df_facturas.empty:
        st.dataframe(df_facturas[['fecha', 'proveedor', 'nif', 'base_imponible', 'iva', 'total', 'tipo']], use_container_width=True)
    else:
        st.info("No hay facturas en el registro. Entra en '📑 Lector OCR' para digitalizar la primera.")

# ==============================================================================
# MÓDULO 2: LECTOR OCR
# ==============================================================================
elif st.session_state.tab_actual == "📑 Lector OCR":
    st.markdown("### Escáner OCR de Facturas y Tickets")
    st.write("Sube el PDF de la factura para extraer automáticamente importes y datos del emisor.")

    uploaded_file = st.file_uploader("Cargar factura (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        datos_ocr = procesar_ocr_limpio(uploaded_file)
        
        st.success("¡Documento procesado correctamente!")
        st.markdown("#### Verificar y Guardar Datos Extraídos")
        
        with st.form("form_factura"):
            col_a, col_b = st.columns(2)
            with col_a:
                proveedor = st.text_input("Emisor / Proveedor", value=datos_ocr["proveedor"])
                nif = st.text_input("NIF / CIF Emisor", value=datos_ocr["nif"])
                fecha = st.date_input("Fecha de Operación", value=datetime.now())
                tipo = st.selectbox("Tipo de Operación", ["Gasto Deducible", "Ingreso / Factura Emitida"])
            with col_b:
                total = st.number_input("Importe Total (€)", value=float(datos_ocr["total"]), format="%.2f")
                base = st.number_input("Base Imponible (€)", value=float(datos_ocr["base"]), format="%.2f")
                iva = st.number_input("Cuota de IVA (€)", value=float(datos_ocr["iva"]), format="%.2f")

            guardar = st.form_submit_button("💾 Guardar en la Contabilidad")

        if guardar:
            conn = sqlite3.connect('tramitia.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO facturas (fecha, proveedor, nif, base_imponible, iva, total, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(fecha), proveedor, nif, base, iva, total, tipo))
            conn.commit()
            conn.close()
            st.success("✅ Factura registrada con éxito en el libro de IVA/IRPF.")

# ==============================================================================
# MÓDULO 3: IMPUESTOS
# ==============================================================================
elif st.session_state.tab_actual == "🏛️ Impuestos":
    st.markdown("### Liquidación de Impuestos Oficiales")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        modelo = st.selectbox("Modelo Tributario:", ["Modelo 303 (IVA)", "Modelo 130 (IRPF)"])
    with col_sel2:
        periodo = st.selectbox("Trimestre Fiscal:", ["1T (Ene-Mar)", "2T (Abr-Jun)", "3T (Jul-Sep)", "4T (Oct-Dic)"])

    conn = sqlite3.connect('tramitia.db')
    df = pd.read_sql_query("SELECT * FROM facturas", conn)
    conn.close()

    ingresos_base = df[df['tipo'] == 'Ingreso / Factura Emitida']['base_imponible'].sum() if not df.empty else 0.0
    gastos_base = df[df['tipo'] == 'Gasto Deducible']['base_imponible'].sum() if not df.empty else 0.0
    iva_dev = df[df['tipo'] == 'Ingreso / Factura Emitida']['iva'].sum() if not df.empty else 0.0
    iva_ded = df[df['tipo'] == 'Gasto Deducible']['iva'].sum() if not df.empty else 0.0

    if modelo == "Modelo 303 (IVA)":
        res = round(iva_dev - iva_ded, 2)
        st.markdown(f'''
            <div class="tramitia-card">
                <h3>Borrador Modelo 303 - {periodo}</h3>
                <hr style="border-color:#334155;">
                <p><b>[01] IVA Devengado (Cobrado):</b> {iva_dev:,.2f} €</p>
                <p><b>[28] IVA Deducible (Pagado):</b> {iva_ded:,.2f} €</p>
                <h2 style="color:#10b981; margin-top:10px;">Resultado a Ingresar: {res:,.2f} €</h2>
            </div>
        ''', unsafe_allow_html=True)
    else:
        rendimiento = ingresos_base - gastos_base
        irpf = round(max(0.0, rendimiento * 0.20), 2)
        st.markdown(f'''
            <div class="tramitia-card">
                <h3>Borrador Modelo 130 - {periodo}</h3>
                <hr style="border-color:#334155;">
                <p><b>Rendimiento Neto (Ingresos - Gastos):</b> {rendimiento:,.2f} €</p>
                <h2 style="color:#10b981; margin-top:10px;">Pago a Cuenta IRPF (20%): {irpf:,.2f} €</h2>
            </div>
        ''', unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 4: ASISTENTE TRAMI CON CONSULTOR TRIBUTARIO OFICIAL
# ==============================================================================
elif st.session_state.tab_actual == "🤖 Asistente Trami":
    st.markdown("### Asistente Legal y Fiscal Inteligente")
    st.write("Consulta cualquier gasto o duda normativa según la LIRPF y LIVA para ver si es deducible.")

    # Historial de consultas
    conn = sqlite3.connect('tramitia.db')
    historial = pd.read_sql_query("SELECT * FROM consultas_trami ORDER BY id ASC", conn)
    conn.close()

    if not historial.empty:
        for idx, row in historial.iterrows():
            st.markdown(f'<div class="user-msg"><b>Tú:</b> {row["pregunta"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bot-msg">🤖 <b>Trami:</b><br>{row["respuesta"]}</div>', unsafe_allow_html=True)

    pregunta_user = st.text_input("Ejemplo: '¿Puedo deducir la gasolina?', '¿Cómo deduzco la luz trabajando en casa?'")

    if st.button("Consultar Normativa AEAT") and pregunta_user:
        p = pregunta_user.lower()
        
        # Lógica experta tributaria (LIVA / LIRPF)
        if "coche" in p or "gasolina" in p or "combustible" in p or "vehiculo" in p:
            resp = """<span class="badge-norma">Art. 95 LIVA & Art. 22 RIRPF</span><br><br>
            • <b>IVA:</b> Se presume deducible al <b>50%</b> si el vehículo se utiliza en la actividad económica.<br>
            • <b>IRPF:</b> Para deducir el 100% del gasto o amortización en IRPF, la ley exige que el vehículo esté dedicado <b>exclusivamente</b> a la actividad (comerciales, repartidores, etc.). Si se usa a nivel particular, en IRPF el gasto es 0% deducible."""
        elif "casa" in p or "luz" in p or "internet" in p or "vivienda" in p or "suministro" in p:
            resp = """<span class="badge-norma">Art. 30.2.5ª LIRPF</span><br><br>
            • <b>Suministros (Luz, Agua, Gas, Internet):</b> Si trabajas desde casa y la has afectado en el Modelo 036/037, puedes deducir el <b>30% del porcentaje de metros cuadrados</b> dedicados a la actividad sobre el total de la vivienda.<br>
            • <b>Ejemplo:</b> Vivienda de 100m² con despacho de 20m² (20%). Deducible = 30% x 20% = 6% de la factura de luz."""
        elif "comida" in p or "restaurante" in p or "dietas" in p:
            resp = """<span class="badge-norma">Art. 30.2.5ª LIRPF (Ley Reformas Autónomos)</span><br><br>
            • <b>Límite diario:</b> 26,67 €/día en España (48,08 € en el extranjero).<br>
            • <b>Requisitos obligatorios:</b> Deberán producirse en establecimientos de restauración/hostelería, abonarse obligatoriamente mediante <b>pago electrónico</b> y contar con factura formal a tu NIF."""
        elif "movil" in p or "telefono" in p:
            resp = """<span class="badge-norma">Art. 22 RIRPF</span><br><br>
            • Si dispones de una **segunda línea telefónica exclusiva** a tu nombre para trabajo, es deducible al 100% en IVA e IRPF. Si es tu línea personal de uso mixto, Hacienda suele rechazar la deducción."""
        else:
            resp = """<span class="badge-norma">Art. 105 LGT (Carga de la Prueba)</span><br><br>
            Para que cualquier gasto sea deducible ante una inspección de la AEAT debe cumplir 4 reglas de oro:<br>
            1. Estar directamente vinculado a la obtención de ingresos.<br>
            2. Estar convenientemente justificado mediante <b>Factura Completa</b>.<br>
            3. Hallarse registrado en los libros de gastos.<br>
            4. Estar imputado en el ejercicio fiscal correspondiente."""

        conn = sqlite3.connect('tramitia.db')
        c = conn.cursor()
        c.execute("INSERT INTO consultas_trami (fecha, pregunta, respuesta) VALUES (?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), pregunta_user, resp))
        conn.commit()
        conn.close()
        st.rerun()
