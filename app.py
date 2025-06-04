import streamlit as st
import pandas as pd
import numpy_financial as npf # Certifique-se de que numpy-financial está instalado: pip install numpy-financial
import plotly.express as px

# Função para formatar valores em Reais (R$) com padrão brasileiro
def format_brl(value):
    # Garante que o valor seja um número
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "R$ --" # Ou outra mensagem de erro

    # Formata o número com 2 casas decimais e separador de milhares americano (ponto como decimal)
    formatted_value = f"{value:,.2f}"

    # Inverte os separadores para o padrão brasileiro (vírgula como decimal, ponto como milhar)
    # 1. Troca vírgulas por um caractere temporário (ex: 'X')
    # 2. Troca pontos por vírgulas
    # 3. Troca o caractere temporário por pontos
    return f"R$ {formatted_value.replace(',', 'X').replace('.', ',').replace('X', '.')}"

st.set_page_config(layout="wide")

st.title("💰 Simulador de Crédito com Garantia de Aplicação")

# --- ENTRADAS DO USUÁRIO ---
st.header("Dados da Operação de Crédito:")

valor_credito = st.number_input(
    "Valor do Crédito (R$):",
    min_value=1000.0,
    value=100000.0,
    step=1000.0,
    format="%.2f"
)
# Prazo máximo limitado a 60 meses
prazo_credito_meses = st.slider(
    "Prazo do Crédito (meses):",
    min_value=1,
    max_value=60, # Prazo máximo alterado para 60 meses
    value=60,
    step=1
)

taxa_juros_pactuada_input = st.number_input(
    "Taxa de Juros Pactuada do Crédito (% ao mês):",
    min_value=0.01,
    value=0.8,
    step=0.01,
    format="%.2f"
)
taxa_juros_pactuada_mensal = taxa_juros_pactuada_input / 100

tipo_taxa_credito = st.radio(
    "Tipo de Taxa do Crédito:",
    ("Prefixada", "Pós-fixada (TR + Taxa)"),
    index=0,
    help="Escolha se a taxa do crédito será fixa ou terá um componente de TR."
)

taxa_indexador_anual = 0.0
if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
    taxa_indexador_anual = st.number_input(
        "Taxa do Indexador Anual (TR/ano - %):",
        min_value=0.0,
        value=3.0,
        step=0.01,
        format="%.2f",
        help="Taxa do indexador anual (como a TR) que será somada à taxa pactuada."
    )
    taxa_indexador_mensal = (1 + taxa_indexador_anual / 100)**(1/12) - 1
else:
    taxa_indexador_mensal = 0.0

iof_percentual = st.number_input(
    "IOF Total (% do valor do crédito):",
    min_value=0.0,
    value=0.38,
    step=0.01,
    format="%.2f"
)
tac_percentual = st.number_input(
    "TAC (% do valor do crédito):",
    min_value=0.0,
    value=0.0,
    step=0.01,
    format="%.2f"
)

st.header("Dados da Aplicação em Garantia:")
valor_aplicacao = st.number_input(
    "Valor da Aplicação em Garantia (R$):",
    min_value=1000.0,
    value=50000.0,
    step=1000.0,
    format="%.2f"
)

taxa_rendimento_aplicacao_input = st.number_input(
    "Taxa de Rendimento da Aplicação (% ao mês):",
    min_value=0.01,
    max_value=2.0,
    value=0.8,
    step=0.01,
    format="%.2f"
)
taxa_rendimento_aplicacao_mensal = taxa_rendimento_aplicacao_input / 100

ir_aliquota = st.slider(
    "Alíquota de Imposto de Renda sobre Rendimento da Aplicação (%):",
    min_value=0.0,
    max_value=22.5,
    value=15.0,
    step=0.5,
    format="%.1f",
    help="Alíquota de IR para o cálculo do rendimento líquido da aplicação."
) / 100


# --- BOTÃO DE SIMULAÇÃO ---
if st.button("Simular Operação", key="btn_simular_operacao"):
    # --- INÍCIO: SEÇÃO DE CÁLCULOS DA OPERAÇÃO DE CRÉDITO E APLICAÇÃO ---

    # 1. CÁLCULOS INICIAIS
    iof_total = valor_credito * (iof_percentual / 100)
    tac_valor = valor_credito * (tac_percentual / 100)
    valor_liquido_recebido = valor_credito - iof_total - tac_valor

    # 2. CÁLCULO DA TAXA DE JUROS EFETIVA DO CRÉDITO
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal + taxa_indexador_mensal
    else:
        taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal
    
    # 3. CÁLCULO DA PARCELA MENSAL E JUROS TOTAIS (BASE TABLE PRICE)
    if prazo_credito_meses == 0:
        parcela_mensal_credito = 0.0
        total_juros_pagos_credito = 0.0
    else:
        try:
            parcela_mensal_credito = npf.pmt(
                taxa_juros_credito_efetiva_mensal,
                prazo_credito_meses,
                -valor_credito
            )
            total_juros_pagos_credito = (parcela_mensal_credito * prazo_credito_meses) - valor_credito
        except Exception as e:
            st.error(f"Erro no cálculo da parcela do crédito: {e}. Verifique as taxas e prazos.")
            parcela_mensal_credito = 0.0
            total_juros_pagos_credito = 0.0

    # 4. CÁLCULOS DA APLICAÇÃO
    rendimento_bruto_total_aplicacao = valor_aplicacao * ((1 + taxa_rendimento_aplicacao_mensal)**prazo_credito_meses - 1)
    ir_total_aplicacao = rendimento_bruto_total_aplicacao * ir_aliquota
    rendimento_liquido_total_aplicacao = rendimento_bruto_total_aplicacao - ir_total_aplicacao
    capital_total_acumulado_aplicacao = valor_aplicacao + rendimento_liquido_total_aplicacao

    # 5. CÁLCULO DO GANHO LÍQUIDO TOTAL
    ganho_liquido_total_operacao = rendimento_liquido_total_aplicacao - total_juros_pagos_credito

    # 6. GERAÇÃO DOS DADOS MENSAIS PARA OS GRÁFICOS
    historico = []
    saldo_atual_credito = valor_credito
    saldo_atual_aplicacao = valor_aplicacao

    for mes_idx in range(1, prazo_credito_meses + 1):
        # Crédito
        juros_mes_credito = saldo_atual_credito * taxa_juros_credito_efetiva_mensal
        amortizacao_mes = parcela_mensal_credito - juros_mes_credito
        saldo_atual_credito -= amortizacao_mes

        # Aplicação
        rendimento_mes_bruto = saldo_atual_aplicacao * taxa_rendimento_aplicacao_mensal
        saldo_atual_aplicacao += rendimento_mes_bruto

        historico.append({
            'Mês': mes_idx,
            'Saldo Devedor do Crédito (R$)': max(0, saldo_atual_credito),
            'Parcela Mensal do Crédito (R$)': parcela_mensal_credito,
            'Rendimento Líquido Mensal da Aplicação (R$)': rendimento_mes_bruto * (1 - ir_aliquota),
            'Saldo da Aplicação em Garantia (R$)': saldo_atual_aplicacao
        })

    df_evolucao = pd.DataFrame(historico)
    df_fluxo_mensal = pd.DataFrame(historico)

    # --- FIM DA SEÇÃO DE CÁLCULOS ---


    # --- INÍCIO: SEÇÃO DE EXIBIÇÃO DOS RESULTADOS ---
    st.header("Resultados da Simulação:")

    st.subheader("Resumo Financeiro da Operação:")
    col1, col2, col3 = st.columns(3)
    with col1:
        # Alteração aqui: usando locale.currency
        st.metric("Valor Líquido Recebido", format_brl(valor_liquido_recebido, grouping=True))
        st.metric("Parcela Mensal do Crédito", format_brl(parcela_mensal_credito, grouping=True))
        st.metric("Total de Juros Pagos no Crédito", format_brl(total_juros_pagos_credito, grouping=True))

    with col2:
        st.metric("Rendimento Bruto Total da Aplicação", format_brl(rendimento_bruto_total_aplicacao, grouping=True))
        st.metric("Imposto de Renda Retido", format_brl(ir_total_aplicacao, grouping=True))
        st.metric("Rendimento Líquido Total", format_brl(rendimento_liquido_total_aplicacao, grouping=True))

    with col3:
        st.metric("Ganho Líquido Total da Operação", format_brl(ganho_liquido_total_operacao, grouping=True))

    st.subheader("Resumo Financeiro Detalhado:")
    # Alteração aqui: usando locale.currency
    st.write(f"- **Juros Totais Pagos no Crédito:** {format_brl(total_juros_pagos_credito, grouping=True)}")
    st.write(f"- **Rendimento Bruto Total da Aplicação:** {format_brl(rendimento_bruto_total_aplicacao, grouping=True)}")
    st.write(f"- **Imposto de Renda Retido na Aplicação:** {format_brl(ir_total_aplicacao, grouping=True)}")
    st.write(f"- **Rendimento Líquido Total da Aplicação:** {format_brl(rendimento_liquido_total_aplicacao, grouping=True)}")
    st.write(f"- **Capital Total Acumulado ao Final do Contrato:** **{format_brl(capital_total_acumulado_aplicacao, grouping=True)}**")
    st.write(f"- **Ganho Líquido Total da Operação (Rendimento Líquido - Juros Pagos):** **{format_brl(ganho_liquido_total_operacao, grouping=True)}**")
    # Lógica da Mensagem Final
    if ganho_liquido_total_operacao >= 0:
        st.success("🎉 Esta operação de crédito, considerando o rendimento da sua aplicação, resulta em um **ganho líquido total** para você!")
        st.info(f"""
        💡 Você não apenas cobriu os juros e custos do crédito com sua aplicação, como também obteve um **ganho de R$ {ganho_liquido_total_operacao:,.2f}**!
        Isso demonstra a **vantagem de usar sua aplicação como garantia** para otimizar seus custos de crédito ao máximo.
        """)
    else:
        st.warning("⚠️ Esta operação de crédito, mesmo com o rendimento da sua aplicação, resulta em um **custo líquido total**.")
        st.info("O rendimento gerado pela sua aplicação foi crucial! Ele cobriu parte dos juros do seu crédito, resultando em uma redução significativa no valor final que você pagou.")


    # --- Exibição dos Gráficos ---
    st.subheader("📊 Evolução Financeira ao Longo do Contrato")
    # Verificação se os DataFrames não estão vazios para evitar erros de Plotly
    if not df_evolucao.empty:
        fig_saldo = px.line(df_evolucao, x='Mês', y=['Saldo Devedor do Crédito (R$)', 'Saldo da Aplicação em Garantia (R$)'],
                            title='Evolução do Saldo Devedor do Crédito vs. Saldo da Aplicação em Garantia',
                            labels={
                                "value": "Valor (R$)",
                                "variable": "Ativo"
                            },
                            line_shape="spline",
                            height=400
                            )
        fig_saldo.update_layout(hovermode="x unified", legend_title_text='Tipo')
        fig_saldo.update_xaxes(showgrid=True, zeroline=True)
        fig_saldo.update_yaxes(showgrid=True, zeroline=True)
        st.plotly_chart(fig_saldo, use_container_width=True)
    else:
        st.info("Não é possível gerar gráficos para um prazo de contrato de 0 meses.")

    if not df_fluxo_mensal.empty:
        fig_fluxo = px.bar(df_fluxo_mensal, x='Mês', y=['Parcela Mensal do Crédito (R$)', 'Rendimento Líquido Mensal da Aplicação (R$)'],
                            title='Parcela Mensal do Crédito vs. Rendimento Líquido Mensal da Aplicação',
                            labels={
                                "value": "Valor (R$)",
                                "variable": "Tipo de Fluxo"
                            },
                            barmode='group',
                            height=400,
                            color_discrete_map={
                                'Parcela Mensal do Crédito (R$)': 'red',
                                'Rendimento Líquido Mensal da Aplicação (R$)': 'green'
                            }
                        )
        fig_fluxo.update_layout(hovermode="x unified", legend_title_text='Fluxo')
        fig_fluxo.update_xaxes(showgrid=True, zeroline=True)
        fig_fluxo.update_yaxes(showgrid=True, zeroline=True)
        st.plotly_chart(fig_fluxo, use_container_width=True)

    # --- FIM DA SEÇÃO DE EXIBIÇÃO DOS RESULTADOS ---

    st.markdown("---")
    st.subheader("Observações Importantes:")
    st.write("""
    - Os cálculos são baseados na **Tabela Price** para o crédito.
    - O rendimento da aplicação é calculado com **juros compostos mensais**.
    - O **Imposto de Renda (IR)** na aplicação é aplicado sobre o rendimento bruto total ao final do período, conforme a alíquota informada.
    - A **TR (Taxa Referencial)** é uma taxa de juros que pode variar. Para simulações futuras, considere que seu valor pode mudar.
    - Esta é uma simulação e os valores reais podem variar. Consulte sempre um profissional financeiro.
    """)

# --- FIM DO BLOCO if st.button ---