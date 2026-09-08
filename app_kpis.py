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

c_medio_tot, r_social_tot, d_medio_tot = calcular_metricas(df_filtered)

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
col1.metric("Coste Medio / Nómina", f"{c_medio_tot:,.2f} €", delta=delta_c_medio, delta_color="inverse")
col2.metric("Ratio Carga Social", f"{r_social_tot:,.2f}%", delta=delta_r_social, delta_color="inverse")
col3.metric("Devengo Medio", f"{d_medio_tot:,.2f} €", delta=delta_d_medio, delta_color="inverse")


# =========================================================================
# 1. COMPARATIVA DE COSTES POR EMPRESA Y AÑO (Con Fila de Totales)
# =========================================================================
st.subheader("🏢 Comparativa de Costes por Empresa y Año (con Totales y Variaciones)")

pivot_empresa_ano = df_filtered.pivot_table(
    index='Empresa', 
    columns='AÑO', 
    values=['TOTAL DEVENGO', 'TOTAL SEGURIDAD SOCIAL', 'TOTAL EMPRESA'], 
    aggfunc='sum'
).fillna(0)

df_empresa_final = pd.DataFrame(index=pivot_empresa_ano.index)
formatos_empresa = {}

for i, ano in enumerate(anos_seleccionados):
    col_dev = f'Devengos {ano}'
    col_ss = f'Seg. Social {ano}'
    col_emp = f'Total Empresa {ano}'
    
    df_empresa_final[col_dev] = pivot_empresa_ano[('TOTAL DEVENGO', ano)]
    df_empresa_final[col_ss] = pivot_empresa_ano[('TOTAL SEGURIDAD SOCIAL', ano)]
    df_empresa_final[col_emp] = pivot_empresa_ano[('TOTAL EMPRESA', ano)]
    
    formatos_empresa[col_dev] = "{:,.2f} €"
    formatos_empresa[col_ss] = "{:,.2f} €"
    formatos_empresa[col_emp] = "{:,.2f} €"
    
    if i > 0:
        ano_prev = anos_seleccionados[i-1]
        col_diff_abs = f'Dif. Abs. (€) {ano} vs {ano_prev}'
        col_diff_pct = f'Dif. % {ano} vs {ano_prev}'
        
        df_empresa_final[col_diff_abs] = df_empresa_final[col_emp] - df_empresa_final[f'Total Empresa {ano_prev}']
        df_empresa_final[col_diff_pct] = ((df_empresa_final[col_emp] - df_empresa_final[f'Total Empresa {ano_prev}']) / df_empresa_final[f'Total Empresa {ano_prev}'].replace(0, 1)) * 100
        
        formatos_empresa[col_diff_abs] = "{:+,.2f} €"
        formatos_empresa[col_diff_pct] = "{:+.2f}%"

# Añadir fila de TOTALES empresa
if not df_empresa_final.empty:
    fila_totales_empresa = pd.DataFrame(index=['TOTAL GRUPO'])
    for col in df_empresa_final.columns:
        if 'Dif. %' in col:
            # Recalcular % total global
            ano_actual_str = col.split(' ')[-3] # Extraer año actual
            ano_prev_str = col.split(' ')[-1]  # Extraer año previo
            col_tot_act = f'Total Empresa {ano_actual_str}'
            col_tot_prev = f'Total Empresa {ano_prev_str}'
            tot_act = df_empresa_final[col_tot_act].sum()
            tot_prev = df_empresa_final[col_tot_prev].sum()
            fila_totales_empresa[col] = ((tot_act - tot_prev) / tot_prev * 100) if tot_prev != 0 else 0
        elif 'Dif. Abs.' in col:
            ano_actual_str = col.split(' ')[-3]
            ano_prev_str = col.split(' ')[-1]
            col_tot_act = f'Total Empresa {ano_actual_str}'
            col_tot_prev = f'Total Empresa {ano_prev_str}'
            fila_totales_empresa[col] = df_empresa_final[col_tot_act].sum() - df_empresa_final[col_tot_prev].sum()
        else:
            fila_totales_empresa[col] = df_empresa_final[col].sum()
            
    df_empresa_final = pd.concat([df_empresa_final, fila_totales_empresa])

def color_diferencias(val):
    if isinstance(val, (int, float)):
        if val < 0:
            return 'color: green;'
        elif val > 0:
            return 'color: red;'
    return ''

cols_colorear_empresa = [c for c in df_empresa_final.columns if 'Dif.' in str(c)]
st.dataframe(
    df_empresa_final.style.format(formatos_empresa)
                      .map(color_diferencias, subset=cols_colorear_empresa), 
    use_container_width=True
)


# =========================================================================
# 2. EVOLUCIÓN MENSUAL DEL COSTE TOTAL EMPRESA (Con Fila de Totales)
# =========================================================================
st.subheader("📅 Evolución Mensual del Coste Total Empresa (con Totales y Variaciones)")

pivot_mes_ano = df_filtered.pivot_table(
    index='MES', 
    columns='AÑO', 
    values='TOTAL EMPRESA', 
    aggfunc='sum'
).reindex(meses_disponibles).fillna(0)

df_mes_final = pd.DataFrame(index=meses_disponibles)
formatos_meses = {}

for i, ano in enumerate(anos_seleccionados):
    col_coste = f'Coste {ano}'
    df_mes_final[col_coste] = pivot_mes_ano[ano]
    formatos_meses[col_coste] = "{:,.2f} €"
    
    if i > 0:
        ano_prev = anos_seleccionados[i-1]
        col_diff_abs = f'Dif. Abs. (€) {ano} vs {ano_prev}'
        col_diff_pct = f'Dif. % {ano} vs {ano_prev}'
        
        df_mes_final[col_diff_abs] = df_mes_final[col_coste] - df_mes_final[f'Coste {ano_prev}']
        df_mes_final[col_diff_pct] = ((df_mes_final[col_coste] - df_mes_final[f'Coste {ano_prev}']) / df_mes_final[f'Coste {ano_prev}'].replace(0, 1)) * 100
        
        formatos_meses[col_diff_abs] = "{:+,.2f} €"
        formatos_meses[col_diff_pct] = "{:+.2f}%"

# Añadir fila de TOTALES mensuales (suma de los 12 meses)
if not df_mes_final.empty:
    fila_totales_mes = pd.DataFrame(index=['TOTAL ANUAL'])
    for col in df_mes_final.columns:
        if 'Dif. %' in col:
            ano_actual_str = col.split(' ')[-3]
            ano_prev_str = col.split(' ')[-1]
            col_tot_act = f'Coste {ano_actual_str}'
            col_tot_prev = f'Coste {ano_prev_str}'
            tot_act = df_mes_final[col_tot_act].sum()
            tot_prev = df_mes_final[col_tot_prev].sum()
            fila_totales_mes[col] = ((tot_act - tot_prev) / tot_prev * 100) if tot_prev != 0 else 0
        elif 'Dif. Abs.' in col:
            ano_actual_str = col.split(' ')[-3]
            ano_prev_str = col.split(' ')[-1]
            col_tot_act = f'Coste {ano_actual_str}'
            col_tot_prev = f'Coste {ano_prev_str}'
            fila_totales_mes[col] = df_mes_final[col_tot_act].sum() - df_mes_final[col_tot_prev].sum()
        else:
            fila_totales_mes[col] = df_mes_final[col].sum()
            
    df_mes_final = pd.concat([df_mes_final, fila_totales_mes])

cols_colorear_mes = [c for c in df_mes_final.columns if 'Dif.' in str(c)]
st.dataframe(
    df_mes_final.style.format(formatos_meses)
                      .map(color_diferencias, subset=cols_colorear_mes), 
    use_container_width=True
)


# =========================================================================
# 3. GRÁFICO COMPARATIVO
# =========================================================================
st.subheader("📈 Gráfico Comparativo de Costes Totales por Empresa")
chart_data = df_filtered.groupby(['MES', 'Empresa'])['TOTAL EMPRESA'].sum().unstack().reindex(meses_disponibles).fillna(0)
st.bar_chart(chart_data)
