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

# --- CÁLCULO DE MÉTRICAS SUPERIORES CON COMPARATIVA ANUAL ---
anos_seleccionados = sorted(sel_anos)

def calcular_metricas(sub_df):
    reg = len(sub_df)
    dev = sub_df['TOTAL DEVENGO'].sum()
    ss = sub_df['TOTAL SEGURIDAD SOCIAL'].sum()
    emp = sub_df['TOTAL EMPRESA'].sum()
    c_medio = (emp / reg) if reg > 0 else 0
    r_social = ((ss / dev) * 100) if dev > 0 else 0
    d_medio = (dev / reg) if reg > 0 else 0
    return c_medio, r_social, d_medio

# Métricas del total filtrado actual
c_medio_tot, r_social_tot, d_medio_tot = calcular_metricas(df_filtered)

# Si hay al menos dos años seleccionados, calculamos el último vs el anterior para la comparativa delta
delta_c_medio, delta_r_social, delta_d_medio = None, None, None
etiqueta_comparativa = ""

if len(anos_seleccionados) >= 2:
    ano_actual = anos_seleccionados[-1]
    ano_previo = anos_seleccionados[-2]
    etiqueta_comparativa = f"vs {ano_previo}"
    
    df_actual = df_filtered[df_filtered['AÑO'] == ano_actual]
    df_previo = df_filtered[df_filtered['AÑO'] == ano_previo]
    
    c_act, r_act, d_act = calcular_metricas(df_actual)
    c_prev, r_prev, d_prev = calcular_metricas(df_previo)
    
    delta_c_medio = f"{(c_act - c_prev):+,.2f} € ({etiqueta_comparativa})"
    delta_r_social = f"{(r_act - r_prev):+.2f}% ({etiqueta_comparativa})"
    delta_d_medio = f"{(d_act - d_prev):+,.2f} € ({etiqueta_comparativa})"

col1, col2, col3 = st.columns(3)
col1.metric("Coste Medio / Nómina", f"{c_medio_tot:,.2f} €", delta=delta_c_medio)
col2.metric("Ratio Carga Social", f"{r_social_tot:,.2f}%", delta=delta_r_social)
col3.metric("Devengo Medio", f"{d_medio_tot:,.2f} €", delta=delta_d_medio)


# =========================================================================
# 1. COMPARATIVA DE COSTES POR EMPRESA Y AÑO (Con Variaciones)
# =========================================================================
st.subheader("🏢 Comparativa de Costes por Empresa y Año (con Variaciones)")

pivot_empresa_ano = df_filtered.pivot_table(
    index='Empresa', 
    columns='AÑO', 
    values=['TOTAL DEVENGO', 'TOTAL SEGURIDAD SOCIAL', 'TOTAL EMPRESA'], 
    aggfunc='sum'
).fillna(0)

df_empresa_final = pd.DataFrame(index=pivot_empresa_ano.index)

for i, ano in enumerate(anos_seleccionados):
    df_empresa_final[(f'Devengos {ano}', '')] = pivot_empresa_ano[('TOTAL DEVENGO', ano)]
    df_empresa_final[(f'Seg. Social {ano}', '')] = pivot_empresa_ano[('TOTAL SEGURIDAD SOCIAL', ano)]
    df_empresa_final[(f'Total Empresa {ano}', '')] = pivot_empresa_ano[('TOTAL EMPRESA', ano)]
    
    if i > 0:
        ano_prev = anos_seleccionados[i-1]
        col_diff_abs = f'Dif. Abs. (€) {ano} vs {ano_prev}'
        col_diff_pct = f'Dif. % {ano} vs {ano_prev}'
        
        df_empresa_final[(col_diff_abs, '')] = df_empresa_final[(f'Total Empresa {ano}', '')] - df_empresa_final[(f'Total Empresa {ano_prev}', '')]
        df_empresa_final[(col_diff_pct, '')] = ((df_empresa_final[(f'Total Empresa {ano}', '')] - df_empresa_final[(f'Total Empresa {ano_prev}', '')]) / df_empresa_final[(f'Total Empresa {ano_prev}', '')].replace(0, 1)) * 100

st.dataframe(df_empresa_final.style.format(lambda v: f"{v:,.2f} €" if isinstance(v, (int, float)) and v > 100 else f"{v:,.2f}"), use_container_width=True)


# =========================================================================
# 2. EVOLUCIÓN MENSUAL DEL COSTE TOTAL EMPRESA (Con Variaciones)
# =========================================================================
st.subheader("📅 Evolución Mensual del Coste Total Empresa (con Variaciones)")

pivot_mes_ano = df_filtered.pivot_table(
    index='MES', 
    columns='AÑO', 
    values='TOTAL EMPRESA', 
    aggfunc='sum'
).reindex(meses_disponibles).fillna(0)

df_mes_final = pd.DataFrame(index=meses_disponibles)

for i, ano in enumerate(anos_seleccionados):
    df_mes_final[f'Coste {ano}'] = pivot_mes_ano[ano]
    
    if i > 0:
        ano_prev = anos_seleccionados[i-1]
        df_mes_final[f'Dif. Abs. (€) {ano} vs {ano_prev}'] = df_mes_final[f'Coste {ano}'] - df_mes_final[f'Coste {ano_prev}']
        df_mes_final[f'Dif. % {ano} vs {ano_prev}'] = ((df_mes_final[f'Coste {ano}'] - df_mes_final[f'Coste {ano_prev}']) / df_mes_final[f'Coste {ano_prev}'].replace(0, 1)) * 100

st.dataframe(df_mes_final.style.format("{:,.2f}"), use_container_width=True)


# =========================================================================
# 3. GRÁFICO COMPARATIVO
# =========================================================================
st.subheader("📈 Gráfico Comparativo de Costes Totales por Empresa")
chart_data = df_filtered.groupby(['MES', 'Empresa'])['TOTAL EMPRESA'].sum().unstack().reindex(meses_disponibles).fillna(0)
st.bar_chart(chart_data)
