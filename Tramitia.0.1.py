import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==============================================================================
st.set_page_config(
    page_title="Tramitia - Burocracia y Finanzas Fáciles",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (Modo Oscuro Fintech: Azul Cobalto & Verde Menta)
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-card h4 {
        color: #9ca3af;
        margin-bottom: 8px;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-card h2 {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
    }

    /* Botones primarios */
    .stButton>button {
        background: linear-gradient(135deg, #1e40af 0%, #10b981 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    
    /* Cajas informativas */
    .stAlert {
        background-color: #111827;
        border: 1px solid #1f2937;
        color: #f3f4f6;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BASE DE DATOS SQLITE LOCAL
# ==============================================================================
def init_db():
    conn = sqlite3.connect('tramitia.db')
    c = conn.cursor()
    # Tabla de facturas
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
    # Tabla de historial del chat Trami
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
# 3. CABECERA CON LOGO OFICIAL SVG (Azul Cobalto & Verde Menta)
# ==============================================================================
logo_svg = """
<div style="display: flex; justify-content: center; padding: 10px 0 20px 0;">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="100%" height="80px">
    <defs>
      <linearGradient id="tramitiaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#1e40af" />
        <stop offset="100%" stop-color="#10b981" />
      </linearGradient>
    </defs>
    <g transform="translate(10, 10)">
      <!-- Isotipo: T de conexión continua -->
      <path d="M 25 20 L 75 20 C 85 20 90 28 85 38 L 55 85 C 50 93 40 93 35 85 C 30 78 35 70 45 70 L 55 70 C 62 70 65 65 68 58 L 72 48 C 75 42 70 38 62 38 L 35 38 C 25 38 20 30 25 20 Z" fill="url(#tramitiaGrad)" />
      <circle cx="85" cy="28" r="8" fill="#10b981" />
      <!-- Nombre de marca -->
      <text x="110" y="62" font-family="'Plus Jakarta Sans', system-ui, -apple-system, sans-serif" font-weight="800" font-size="46" fill="#ffffff" letter-spacing="-1">Tramitia</text>
      <!-- Eslogan -->
      <text x="112" y="85" font-family="'Plus Jakarta Sans', system-ui, -apple-system, sans-serif" font-weight="700" font-size="12" fill="#10b981" letter-spacing="2.5">BUROCRACIA FÁCIL</text>
    </g>
  </svg>
</div>
"""
st.markdown(logo_svg, unsafe_allow_html=True)

# ==============================================================================
# 4. NAVEGACIÓN Y MENÚ LATERAL
# ==============================================================================
st.sidebar.markdown("<h2 style='color:#10b981; font-size:1.2rem; text-align:center;'>Menú Principal</h2>", unsafe_allow_html=True)
opcion = st.sidebar.radio("", [
    "📊 Panel Principal",
    "📑 Lector de Facturas",
    "🏛️ Modelos de Hacienda",
    "🤖 Asistente Virtual (Trami)"
])

st.sidebar.markdown("---")
st.sidebar.caption("⚡ Tramitia v1.0 • Sistema de Gestión Inteligente")

# ==============================================================================
# MÓDULO 1: PANEL PRINCIPAL (DASHBOARD)
# ==============================================================================
if opcion == "📊 Panel Principal":
    st.markdown("### Resumen Fiscal Trimestral")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('''
            <div class="metric-card">
                <h4>Ingresos Totales</h4>
                <h2 style="color:#10b981;">12.450 €</h2>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown('''
            <div class="metric-card">
                <h4>Gastos Deducibles</h4>
                <h2 style="color:#3b82f6;">3.200 €</h2>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown('''
            <div class="metric-card">
                <h4>IVA a Pagar (Mod. 303)</h4>
                <h2 style="color:#f59e0b;">1.942 €</h2>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Últimas Facturas Registradas")
    
    conn = sqlite3.connect('tramitia.db')
    df = pd.read_sql_query("SELECT fecha, proveedor, nif, total, tipo FROM facturas ORDER BY id DESC LIMIT 5", conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no has registrado facturas. Ve al apartado 'Lector de Facturas' para añadir la primera.")

# ==============================================================================
# MÓDULO 2: LECTOR DE FACTURAS
# ==============================================================================
elif opcion == "📑 Lector de Facturas":
    st.markdown("### Procesador de Facturas y Tickets")
    st.write("Sube tus documentos en PDF o imagen para extraer los datos e integrarlos en tus impuestos.")

    uploaded_file = st.file_uploader("Arrastra tu archivo aquí o selecciónalo", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        st.success("Documento cargado correctamente. Datos extraídos por la IA:")
        
        # Simulación de extracción inteligente / OCR
        col_a, col_b = st.columns(2)
        with col_a:
            proveedor = st.text_input("Proveedor / Emisor", "Servicios Cloud S.L.")
            nif = st.text_input("NIF / CIF", "B12345678")
            fecha = st.date_input("Fecha de emisión")
        with col_b:
            base = st.number_input("Base Imponible (€)", value=100.0)
            iva = st.number_input("IVA 21% (€)", value=21.0)
            total = st.number_input("Total (€)", value=121.0)

        tipo = st.selectbox("Tipo de documento", ["Gasto Deducible", "Ingreso / Factura Emitida"])

        if st.button("Guardar Factura en Base de Datos"):
            conn = sqlite3.connect('tramitia.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO facturas (fecha, proveedor, nif, base_imponible, iva, total, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(fecha), proveedor, nif, base, iva, total, tipo))
            conn.commit()
            conn.close()
            st.success("¡Factura guardada correctamente en tu panel fiscal!")

# ==============================================================================
# MÓDULO 3: MODELOS DE HACIENDA
# ==============================================================================
elif opcion == "🏛️ Modelos de Hacienda":
    st.markdown("### Autogeneración de Impuestos")
    st.write("Calcula y prepara tus liquidaciones oficiales sin complicaciones.")

    modelo = st.selectbox("Selecciona el modelo que deseas calcular:", [
        "Modelo 303 - Liquidación Trimestral de IVA",
        "Modelo 130 - Pago Fraccionado del IRPF",
        "Modelo 390 - Resumen Anual de IVA"
    ])

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        trimestre = st.selectbox("Trimestre:", ["1T (Enero - Marzo)", "2T (Abril - Junio)", "3T (Julio - Septiembre)", "4T (Octubre - Diciembre)"])
    with col_m2:
        anyo = st.selectbox("Año Fiscal:", ["2026", "2025"])

    if st.button("Calcular Borrador Oficial"):
        st.markdown("---")
        st.markdown(f"#### Resultados para {modelo} ({trimestre} {anyo})")
        st.write("• **IVA Devengado (Ventas):** 2.614,50 €")
        st.write("• **IVA Deducible (Compras):** 672,50 €")
        st.markdown("### **Resultado a Ingresar:** <span style='color:#10b981;'>1.942,00 €</span>", unsafe_allow_html=True)
        
        st.button("📥 Descargar Archivo Oficial para Importar en la Web de Hacienda")

# ==============================================================================
# MÓDULO 4: ASISTENTE VIRTUAL (TRAMI)
# ==============================================================================
elif opcion == "🤖 Asistente Virtual (Trami)":
    st.markdown("### Consulta a Trami")
    st.write("Tu asistente inteligente para resolver dudas sobre gastos deducibles, plazos y burocracia.")

    pregunta = st.text_input("Escribe tu duda o consulta legal/fiscal:")

    if st.button("Consultar a Trami") and pregunta:
        # Lógica de respuesta inteligente simulada
        respuesta = f"Para deducir este gasto en tu actividad, la factura debe estar emitida a tu NIF, guardar relación directa con tus ingresos y estar adecuadamente registrada en la contabilidad."
        
        st.markdown(f"🤖 **Trami responde:**")
        st.info(respuesta)

        # Guardar en base de datos
        conn = sqlite3.connect('tramitia.db')
        c = conn.cursor()
        c.execute("INSERT INTO consultas_trami (fecha, pregunta, respuesta) VALUES (?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), pregunta, respuesta))
        conn.commit()
        conn.close()
