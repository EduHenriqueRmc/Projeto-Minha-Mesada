import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configurações
st.set_page_config(page_title="Allowance", page_icon="A")
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    /*Reduz o espaço no topo da página */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
    }
    /* Aplica a largura reduzida APENAS em telas maiores (Desktop/Tablet) */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)
registro_compras = conn.read(worksheet="Página1", ttl=0)

st.title("Minha Mesada")

meses_ano = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# Datas e fechamento do cartão
agora = datetime.now()
dia_atual = agora.day
mes_real = agora.month
ano_real = agora.year

if dia_atual > 22:
    mes_financeiro_idx = mes_real + 1
else:
    mes_financeiro_idx = mes_real

ano_financeiro = ano_real

# Virar o ano
if mes_financeiro_idx > 12:
    mes_financeiro_idx = 1
    ano_financeiro += 1

nome_mes_financeiro = meses_ano[mes_financeiro_idx - 1]

# Sidebar para registrar compra
st.sidebar.write("# Registrar Compra")
st.sidebar.info(f" **Data:** {agora.strftime('%d/%m/%Y')}\n\n **Fatura:** {nome_mes_financeiro}/{ano_financeiro}")

tipo = st.sidebar.selectbox("Tipo de Compra", ["Essencial", "Lazer", "Investimento"])
valor = st.sidebar.number_input("Valor",value=None, min_value=0.00, step=None, placeholder="valor")
confirmar = st.sidebar.button("Registrar")

if confirmar:
    nova_compra = pd.DataFrame([{
        "Data": agora.strftime("%d/%m/%Y"),
        "Mês": nome_mes_financeiro,     
        "Tipo da Compra": tipo, 
        "Valor": valor
    }])
    
    registro_compras = pd.concat([registro_compras, nova_compra], ignore_index=True)
    conn.update(worksheet="Página1", data=registro_compras)
    st.cache_data.clear()
    st.success("Compra Registrada!")

# Calcular saldo acumulado
MES_INICIO = 10  
ANO_INICIO = 2026 

# Calcular a diferença de meses entre a data de início e a data atual da fatura
meses_acumulados = ((ano_financeiro - ANO_INICIO) * 12) + (mes_financeiro_idx - MES_INICIO) + 1
limite_acumulado = meses_acumulados * 600.00
total_gasto = registro_compras["Valor"].sum()
saldo = limite_acumulado - total_gasto

st.metric(f"Saldo", f"R$ {saldo:.2f}")

# Histórico de compras
st.write("## Histórico")
if not registro_compras.empty:

    colunas_visiveis = ["Data", "Tipo da Compra", "Valor"]
    df_editor = registro_compras[colunas_visiveis].copy()
    df_editor.insert(0, "Excluir", False)

    tabela_editada = st.data_editor(
        df_editor,
        hide_index=True,
        use_container_width=True,
        key="editor_compras"
    )

    # Filtragem
    compras_para_excluir = tabela_editada[tabela_editada["Excluir"] == True]

    if not compras_para_excluir.empty:
        if st.button("Deletar", type="secondary"):
            indices_manter = tabela_editada[tabela_editada["Excluir"] == False].index
            
            registro_compras = registro_compras.iloc[indices_manter].reset_index(drop=True)
            conn.update(worksheet="Página1", data=registro_compras)
            st.cache_data.clear()            
            st.success("Compra(s) removida(s) com sucesso!")
            st.rerun()
else:
    st.info("Nenhuma compra registrada para exibir.")

# Dashboard
st.write("## Dashboard")
if not registro_compras.empty:
    grafico = px.bar(
        registro_compras, 
        x="Mês", 
        y="Valor",
        color="Mês",
        category_orders={"Mês": meses_ano},
        title="Gasto por Mês",
        labels={"Mês": "", "Valor": "Valor"}
    )  
    
    # Identifica quais meses possuem registros
    meses_com_registro = [m for m in meses_ano if m in registro_compras["Mês"].unique()]
    
    if len(meses_com_registro) > 3:
        ultimos_3_meses = meses_com_registro[-3:]
        idx_inicio = meses_ano.index(ultimos_3_meses[0]) - 0.5
        idx_fim = meses_ano.index(ultimos_3_meses[-1]) + 0.5
        
        grafico.update_xaxes(range=[idx_inicio, idx_fim])
    
    st.plotly_chart(grafico, use_container_width=True)
else:
    st.info("Nenhuma compra registrada ainda.")