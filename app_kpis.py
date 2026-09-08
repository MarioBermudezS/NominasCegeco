import streamlit as st
import pandas as pd

st.set_page_config(page_title="KPIs de Nóminas y Costes - Gerencia", layout="wide")
st.title("📊 Cuadro de Mando de KPIs: Empresa, Año y Meses")
st.markdown("Análisis avanzado y comparativo de costes laborales del grupo empresarial.")

@st.cache_data
def load_data():
    df = pd.read_excel("Nominas_Resumen_Tres_Empresas_Final.xlsx", sheet_name="Sheet1")
    df['TOTAL DEVENGO'] = pd.to_numeric(df['TOTAL DEVENGO'], errors='coerce').fillna(0)
    df['TOTAL SEGURIDAD SOCIAL'] = pd.to_numeric(df['TOTAL SEGURIDAD SOCIAL'], errors='coerce').fillna(0)
    df['TOTAL EMPRESA'] = pd.to_numeric(df['TOTAL EMPRESA'], errors='coerce').fillna(0)
    return df

df = load_data()

st.sidebar.header("Filtros de Análisis")
empresas_disponibles = df['Empresa'].unique().tolist()
anos_disponibles = sorted(df['AÑO'].unique().tolist())
meses_disponibles = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

sel_empresas = st.sidebar.multiselect("Seleccionar Empresa(s)", empresas_disponibles, default=empresas_disponibles)
sel_anos = st.sidebar.multiselect("Seleccionar Año(s)", anos_disponibles, default=anos_disponibles[-2:] if len(anos_disponibles)>=2 else anos_disponibles)
sel_meses = st.sidebar.multiselect("Seleccionar Mes(es)", meses_disponibles, default=meses_disponibles)

df_filtered = df[(df['Empresa'].isin(sel_empresas)) & (df['AÑO'].isin(sel_anos)) & (df['MES'].isin(sel_meses))]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Registros / Nóminas", f"{len(df_filtered):,}")
col2.metric("Total Devengos", f"{df_filtered['TOTAL DEVENGO'].sum():,.2f} €")
col3.metric("Total Seguridad Social", f"{df_filtered['TOTAL SEGURIDAD SOCIAL'].sum():,.2f} €")
col4.metric("Coste Total Empresa", f"{df_filtered['TOTAL EMPRESA'].sum():,.2f} €")

st.markdown("---")

st.subheader("🏢 Comparativa de Costes por Empresa y Año")
pivot_empresa_ano = df_filtered.pivot_table(
    index='Empresa', 
    columns='AÑO', 
    values=['TOTAL DEVENGO', 'TOTAL SEGURIDAD SOCIAL', 'TOTAL EMPRESA'], 
    aggfunc='sum'
).fillna(0)
st.dataframe(pivot_empresa_ano.style.format("{:,.2f} €"), use_container_width=True)

st.subheader("📅 Evolución Mensual del Coste Total Empresa")
pivot_mes_ano = df_filtered.pivot_table(
    index='MES', 
    columns='AÑO', 
    values='TOTAL EMPRESA', 
    aggfunc='sum'
).reindex(meses_disponibles).fillna(0)
st.dataframe(pivot_mes_ano.style.format("{:,.2f} €"), use_container_width=True)

st.subheader("📈 Gráfico Comparativo de Costes Totales por Empresa")
chart_data = df_filtered.groupby(['MES', 'Empresa'])['TOTAL EMPRESA'].sum().unstack().reindex(meses_disponibles).fillna(0)
st.bar_chart(chart_data)
