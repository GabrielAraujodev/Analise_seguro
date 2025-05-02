import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configurações da página
st.set_page_config(
    page_title="Análise de Produção de Seguros",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para carregar dados com cache
@st.cache_data
def load_data():
    # Carrega os dados do arquivo Excel
    try:
        df = pd.read_excel("dados_producao_completos.xlsx", sheet_name="Sheet1")
        
        # Limpeza e transformação dos dados
        df['Data Proposta'] = pd.to_datetime(df['Data Proposta'], errors='coerce')
        df['Prêmio'] = pd.to_numeric(df['Prêmio'], errors='coerce')
        df['Comissão'] = pd.to_numeric(df['Comissão'], errors='coerce')
        
        # Criar colunas adicionais para análise
        df['Mês'] = df['Data Proposta'].dt.to_period('M').dt.to_timestamp()
        df['Dia'] = df['Data Proposta'].dt.date
        df['Dia da Semana'] = df['Data Proposta'].dt.day_name()
        
        # Padronizar nomes de colunas
        df = df.rename(columns={
            'Nº Apólice': 'Apólice',
            'Região': 'Regiao'
        })
        
        return df.dropna(subset=['Data Proposta'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Carregar os dados
df = load_data()

# Verificar se os dados foram carregados corretamente
if df.empty:
    st.warning("Nenhum dado foi carregado. Verifique o arquivo de dados.")
    st.stop()

# Título do dashboard
st.title("📊 Dashboard de Análise de Produção de Seguros")
st.markdown("---")

# Sidebar com filtros
with st.sidebar:
    st.header("🔍 Filtros")
    
    # Filtro por período
    min_date = df['Data Proposta'].min().date()
    max_date = df['Data Proposta'].max().date()
    date_range = st.date_input(
        "Selecione o período:",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtro por situação
    situacoes = st.multiselect(
        "Situação:",
        options=df['Situação'].unique(),
        default=df['Situação'].unique()
    )
    
    # Filtro por região
    regioes = st.multiselect(
        "Região:",
        options=df['Regiao'].unique(),
        default=df['Regiao'].unique()
    )
    
    # Filtro por produtor
    produtores = st.multiselect(
        "Produtor:",
        options=df['PRODUTOR'].unique(),
        default=df['PRODUTOR'].unique()
    )

# Aplicar filtros
filtered_df = df[
    (df['Data Proposta'].dt.date >= date_range[0]) &
    (df['Data Proposta'].dt.date <= date_range[1]) &
    (df['Situação'].isin(situacoes)) &
    (df['Regiao'].isin(regioes)) &
    (df['PRODUTOR'].isin(produtores))
]

# Seção de métricas principais
st.subheader("📈 Métricas Principais")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Apólices", len(filtered_df))
with col2:
    st.metric("Prêmio Total", f"R$ {filtered_df['Prêmio'].sum():,.2f}")
with col3:
    st.metric("Comissão Total", f"R$ {filtered_df['Comissão'].sum():,.2f}")
with col4:
    ticket_medio = filtered_df['Prêmio'].mean()
    st.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}" if not np.isnan(ticket_medio) else "R$ 0,00")

st.markdown("---")

# Abas para diferentes visualizações
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Produção Temporal", 
    "🌎 Análise Geográfica", 
    "👥 Performance por Produtor", 
    "📉 Cancelamentos", 
    "🔍 Dados Detalhados"
])

with tab1:
    st.subheader("Produção ao Longo do Tempo")
    
    # Agrupar dados por período (diário/mensal)
    freq = st.radio("Frequência:", ["Diária", "Mensal"], horizontal=True)
    
    if freq == "Diária":
        grouped = filtered_df.groupby('Dia').agg({
            'Prêmio': 'sum',
            'Comissão': 'sum',
            'PRODUTOR': 'count'
        }).rename(columns={'PRODUTOR': 'Apólices'}).reset_index()
        x_axis = 'Dia'
    else:
        grouped = filtered_df.groupby('Mês').agg({
            'Prêmio': 'sum',
            'Comissão': 'sum',
            'PRODUTOR': 'count'
        }).rename(columns={'PRODUTOR': 'Apólices'}).reset_index()
        x_axis = 'Mês'
    
    # Gráfico de linhas
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=grouped[x_axis],
        y=grouped['Apólices'],
        name='Número de Apólices',
        line=dict(color='#1f77b4'),
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        x=grouped[x_axis],
        y=grouped['Prêmio'],
        name='Prêmio Total (R$)',
        line=dict(color='#ff7f0e'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f"Produção {freq.lower()}",
        xaxis_title='Data',
        yaxis_title='Número de Apólices',
        yaxis2=dict(
            title='Prêmio Total (R$)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Produção por dia da semana
    st.subheader("Produção por Dia da Semana")
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_df = filtered_df.groupby('Dia da Semana').agg({
        'PRODUTOR': 'count',
        'Prêmio': 'mean'
    }).rename(columns={'PRODUTOR': 'Apólices', 'Prêmio': 'Prêmio Médio'}).reindex(weekday_order)
    
    fig = px.bar(
        weekday_df,
        x=weekday_df.index,
        y='Apólices',
        color='Prêmio Médio',
        color_continuous_scale='Blues',
        labels={'x': 'Dia da Semana', 'Apólices': 'Número de Apólices'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Distribuição Geográfica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição por região
        regiao_df = filtered_df.groupby('Regiao').agg({
            'PRODUTOR': 'count',
            'Prêmio': 'sum'
        }).rename(columns={'PRODUTOR': 'Apólices'}).reset_index()
        
        fig = px.pie(
            regiao_df,
            values='Apólices',
            names='Regiao',
            title='Distribuição de Apólices por Região',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Prêmio médio por região
        fig = px.bar(
            regiao_df.sort_values('Prêmio', ascending=False),
            x='Regiao',
            y='Prêmio',
            title='Prêmio Total por Região',
            color='Regiao',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Performance por Produtor")
    
    top_n = st.slider("Selecione o número de produtores para mostrar:", 5, 20, 10)
    
    # Top produtores por número de apólices
    produtor_df = filtered_df.groupby('PRODUTOR').agg({
        'PRODUTOR': 'count',
        'Prêmio': ['sum', 'mean'],
        'Comissão': 'sum'
    })
    produtor_df.columns = ['Apólices', 'Prêmio Total', 'Prêmio Médio', 'Comissão Total']
    produtor_df = produtor_df.reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            produtor_df.sort_values('Apólices', ascending=False).head(top_n),
            x='PRODUTOR',
            y='Apólices',
            title=f'Top {top_n} Produtores por Número de Apólices',
            color='Prêmio Total',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            produtor_df.sort_values('Prêmio Total', ascending=False).head(top_n),
            x='PRODUTOR',
            y='Prêmio Total',
            title=f'Top {top_n} Produtores por Prêmio Total',
            color='Apólices',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Relação entre número de apólices e prêmio médio
    st.subheader("Relação entre Volume e Valor")
    fig = px.scatter(
        produtor_df,
        x='Apólices',
        y='Prêmio Médio',
        size='Prêmio Total',
        color='PRODUTOR',
        hover_name='PRODUTOR',
        title='Relação entre Número de Apólices e Prêmio Médio',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Análise de Cancelamentos")
    
    if 'Cancelada' in filtered_df['Situação'].unique():
        cancelamentos_df = filtered_df[filtered_df['Situação'] == 'Cancelada']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cancelamentos por região
            cancel_regiao_df = cancelamentos_df['Regiao'].value_counts().reset_index()
            cancel_regiao_df.columns = ['Regiao', 'Cancelamentos']
            
            fig = px.pie(
                cancel_regiao_df,
                values='Cancelamentos',
                names='Regiao',
                title='Cancelamentos por Região',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cancelamentos por produtor
            cancel_prod_df = cancelamentos_df['PRODUTOR'].value_counts().reset_index()
            cancel_prod_df.columns = ['Produtor', 'Cancelamentos']
            
            fig = px.bar(
                cancel_prod_df.head(10),
                x='Produtor',
                y='Cancelamentos',
                title='Top 10 Produtores com Mais Cancelamentos',
                color='Cancelamentos',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Evolução temporal de cancelamentos
        st.subheader("Evolução Temporal dos Cancelamentos")
        cancel_time_df = cancelamentos_df.groupby('Dia').size().reset_index(name='Cancelamentos')
        
        fig = px.line(
            cancel_time_df,
            x='Dia',
            y='Cancelamentos',
            title='Cancelamentos ao Longo do Tempo',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum cancelamento encontrado com os filtros atuais.")

with tab5:
    st.subheader("Dados Detalhados")
    
    # Mostrar dataframe com opções de filtro
    cols_to_show = st.multiselect(
        "Selecione as colunas para mostrar:",
        options=filtered_df.columns,
        default=['PRODUTOR', 'CLIENTE', 'Apólice', 'Situação', 'Data Proposta', 'Prêmio', 'Comissão', 'Regiao']
    )
    
    st.dataframe(
        filtered_df[cols_to_show].sort_values('Data Proposta', ascending=False),
        height=600,
        use_container_width=True
    )
    
    # Opção para download
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar para CSV",
        data=csv,
        file_name="dados_seguros_filtrados.csv",
        mime="text/csv"
    )

# Rodapé
st.markdown("---")
st.markdown("Dashboard desenvolvido com Streamlit | Dados atualizados em " + datetime.now().strftime("%d/%m/%Y %H:%M"))