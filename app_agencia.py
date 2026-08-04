import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Portal Agencia - Recubrimientos", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f4f4; }
    h1 { color: #ffffff; text-align: center; background-color: #1E3A8A; padding: 10px; border-radius: 5px; }
    .stButton>button { background-color: #1E3A8A; color: #ffffff; font-weight: bold; width: 100%; border: none; }
    .stButton>button:hover { background-color: #172554; color: #ffffff; }
    .facturacion-header { background-color: #065F46; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.title("Solicitud de cerámicos V clean")
st.markdown("<h4 style='text-align: center;'>Solicitud de Recubrimientos Cerámicos</h4>", unsafe_allow_html=True)
st.write("---")

# --- FUNCIONES DE CORREO ---
def enviar_notificacion_vendedor(destinatario, vehiculo, id_sol):
    try:
        if "email_config" in st.secrets:
            remitente = st.secrets["email_config"]["correo"]
            password = st.secrets["email_config"]["clave"]
            
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = destinatario
            msg['Subject'] = f"✅ Vehículo Listo para Entrega: {vehiculo}"
            
            cuerpo = f"""Hola,
            
Te informamos que el vehículo {vehiculo} (Solicitud: {id_sol}) ya ha sido terminado por nuestro equipo V clean.

El auto está listo para que coordinen su entrega.

Saludos cordiales,
Equipo V clean"""
            
            msg.attach(MIMEText(cuerpo, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
            server.quit()
            return True
    except Exception as e:
        st.error(f"Error interno enviando correo: {e}")
        return False
    return False

def enviar_notificacion_admin(vehiculo, id_sol, fecha_req, solicitante, vendedor, notas):
    try:
        if "email_config" in st.secrets:
            remitente = st.secrets["email_config"]["correo"]
            password = st.secrets["email_config"]["clave"]
            destinatario = remitente # Se envía al mismo correo de Carshield configurado en los secrets
            
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = destinatario
            msg['Subject'] = f"🔔 Nueva Solicitud de Agencia: {vehiculo}"
            
            cuerpo = f"""Hola equipo,
            
Se ha registrado una nueva solicitud de servicio desde el portal de agencias B2B.

Detalles de la solicitud:
- ID: {id_sol}
- Vehículo: {vehiculo}
- Solicitante: {solicitante}
- Vendedor Asignado: {vendedor}
- Fecha Requerida: {fecha_req}
- Observaciones: {notas if notas else 'Ninguna'}

Por favor, revisen el portal de operaciones para actualizar el estatus cuando se reciba el vehículo.

Saludos,
Sistema Automático Carshield"""
            
            msg.attach(MIMEText(cuerpo, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
            server.quit()
            return True
    except Exception as e:
        # Se silencia el error para no asustar al cliente de la agencia si el correo falla
        return False
    return False

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def get_gspread_client():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    hoja_agencia = client.open("Carshield_BaseDatos_App").worksheet("Solicitudes_Agencia")
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

def load_data():
    records = hoja_agencia.get_all_records()
    if not records:
        return pd.DataFrame(columns=["ID_Solicitud", "Fecha_Solicitud", "Solicitante", "Vendedor", "Correo_Vendedor", "Vehiculo_Placa_VIN", "Fecha_Requerida", "Estado_Servicio", "Estado_Facturacion", "Num_Factura", "Observaciones"])
    return pd.DataFrame(records)

df = load_data()

# --- SISTEMA DE SEGURIDAD Y NAVEGACIÓN ---
st.sidebar.markdown("### Menú de Acceso")

PASSWORD_ADMIN = "Vclean1993"

clave_ingresada = st.sidebar.text_input("🔒 Acceso Administrativo", type="password", help="Solo para personal de Carshield")

if clave_ingresada == PASSWORD_ADMIN:
    st.sidebar.success("Acceso interno concedido")
    menu = ["1. Nueva Solicitud (Agencia)", "2. Operaciones (Taller)", "3. Control de Facturación"]
else:
    menu = ["1. Nueva Solicitud (Agencia)"]
    if clave_ingresada != "":
        st.sidebar.error("Clave incorrecta")

choice = st.sidebar.radio("Ir a:", menu)


# ==========================================
# 1. PERFIL: AGENCIA (NUEVA SOLICITUD)
# ==========================================
if choice == "1. Nueva Solicitud (Agencia)":
    st.header("Formulario de Solicitud de Servicio")
    st.info("Complete los datos del vehículo para programar el recubrimiento.")
    
    with st.form("form_solicitud"):
        col1, col2 = st.columns(2)
        with col1:
            solicitante = st.text_input("¿Quién solicita el servicio? (Nombre) *")
            vendedor = st.text_input("Nombre del vendedor asignado al auto *")
            correo_vendedor = st.text_input("Correo electrónico del vendedor (Para notificarle cuando esté listo) *")
        with col2:
            vehiculo = st.text_input("Marca, Modelo, Color y Placa/VIN *")
            fecha_req = st.date_input("Fecha para la que necesitan el auto listo *")
            
        notas = st.text_area("Servicios específicos u observaciones extra")
        
        submit = st.form_submit_button("Enviar Solicitud al Taller")
        
        if submit:
            if solicitante and vendedor and correo_vendedor and vehiculo:
                nuevo_id = "AG-" + str(len(df) + 1).zfill(4)
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                nueva_fila = [
                    nuevo_id, fecha_actual, solicitante, vendedor, correo_vendedor, vehiculo,
                    str(fecha_req), "Recibido / Pendiente", "Pendiente de Facturar", "", notas
                ]
                hoja_agencia.append_row(nueva_fila)
                
                # --- NUEVA FUNCIÓN: Enviar correo de notificación a administración ---
                enviar_notificacion_admin(vehiculo, nuevo_id, fecha_req, solicitante, vendedor, notas)
                
                st.success(f"✅ Solicitud {nuevo_id} enviada exitosamente. El taller ha sido notificado.")
            else:
                st.error("⚠️ Por favor, complete todos los campos marcados con asterisco (*).")

# ==========================================
# 2. PERFIL: OPERACIONES TALLER
# ==========================================
elif choice == "2. Operaciones (Taller)":
    st.header("Autos de Agencia en Proceso")
    
    if not df.empty:
        pendientes = df[df['Estado_Servicio'] != "Terminado y Entregado"]
        if not pendientes.empty:
            st.dataframe(pendientes[["ID_Solicitud", "Vehiculo_Placa_VIN", "Fecha_Requerida", "Estado_Servicio"]], use_container_width=True)
            
            st.write("---")
            st.subheader("Actualizar Estado del Auto")
            id_buscar = st.text_input("Ingrese el ID de Solicitud (Ej: AG-0001):").upper()
            
            if id_buscar:
                filtro = df[df['ID_Solicitud'] == id_buscar]
                if not filtro.empty:
                    idx = filtro.index[0]
                    fila_sheet = int(idx) + 2
                    estado_actual = filtro.loc[idx, "Estado_Servicio"]
                    
                    with st.form("form_taller"):
                        nuevo_estado = st.selectbox("Estado del Servicio", ["Recibido / Pendiente", "En Proceso", "Terminado y Entregado"], index=["Recibido / Pendiente", "En Proceso", "Terminado y Entregado"].index(estado_actual))
                        
                        if st.form_submit_button("Actualizar Taller"):
                            if nuevo_estado == "Terminado y Entregado" and estado_actual != "Terminado y Entregado":
                                correo_dest = filtro.loc[idx, "Correo_Vendedor"]
                                vehiculo_info = filtro.loc[idx, "Vehiculo_Placa_VIN"]
                                
                                hoja_agencia.update(range_name=f"H{fila_sheet}:H{fila_sheet}", values=[[nuevo_estado]])
                                
                                if correo_dest and "@" in correo_dest:
                                    enviado = enviar_notificacion_vendedor(correo_dest, vehiculo_info, id_buscar)
                                    if enviado:
                                        st.success("✅ Estado actualizado. Se ha enviado un correo automático al vendedor de la agencia indicando que el auto está listo.")
                                    else:
                                        st.warning("✅ Estado actualizado a 'Terminado'. (Hubo un problema enviando el correo al vendedor).")
                                else:
                                    st.success("✅ Estado actualizado a 'Terminado'. (No se envió correo por falta de dirección válida).")
                            else:
                                hoja_agencia.update(range_name=f"H{fila_sheet}:H{fila_sheet}", values=[[nuevo_estado]])
                                st.success("✅ Estado actualizado correctamente.")
                else:
                    st.warning("ID no encontrado.")
        else:
            st.success("No hay autos pendientes de la agencia.")
    else:
        st.info("No hay registros.")

# ==========================================
# 3. PERFIL: FACTURACIÓN
# ==========================================
elif choice == "3. Control de Facturación":
    st.markdown("<div class='facturacion-header'><h2>💰 Panel de Cuentas por Cobrar (Agencia)</h2></div>", unsafe_allow_html=True)
    
    if not df.empty:
        por_facturar = df[(df['Estado_Servicio'] == "Terminado y Entregado") & (df['Estado_Facturacion'] != "Facturado")]
        
        st.subheader("⚠️ Vehículos Listos Pendientes de Facturar")
        if not por_facturar.empty:
            st.dataframe(por_facturar[["ID_Solicitud", "Vehiculo_Placa_VIN", "Vendedor", "Estado_Facturacion"]], use_container_width=True)
            
            st.write("---")
            st.subheader("Registrar Factura Emitida")
            id_fac = st.selectbox("Seleccione el ID a facturar:", por_facturar['ID_Solicitud'].tolist())
            
            if id_fac:
                filtro_fac = df[df['ID_Solicitud'] == id_fac]
                idx_fac = filtro_fac.index[0]
                fila_sheet_fac = int(idx_fac) + 2
                
                with st.form("form_facturacion"):
                    num_factura = st.text_input("Ingrese el Número de Factura Electrónica *")
                    
                    if st.form_submit_button("Marcar como Facturado"):
                        if num_factura:
                            hoja_agencia.update(range_name=f"I{fila_sheet_fac}:J{fila_sheet_fac}", values=[["Facturado", num_factura]])
                            st.success(f"✅ El vehículo {id_fac} ha sido facturado correctamente con la factura {num_factura}.")
                        else:
                            st.error("⚠️ Debe ingresar el número de factura.")
        else:
            st.success("¡Excelente! Todos los autos terminados ya han sido facturados.")
            
        st.write("---")
        with st.expander("Ver Historial de Autos Facturados"):
            facturados = df[df['Estado_Facturacion'] == "Facturado"]
            st.dataframe(facturados[["ID_Solicitud", "Fecha_Solicitud", "Vehiculo_Placa_VIN", "Num_Factura"]], use_container_width=True)
    else:
        st.info("La base de datos está vacía.")
