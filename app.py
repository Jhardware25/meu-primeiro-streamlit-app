import streamlit as st
import numpy_financial as npf # Biblioteca para cálculos financeiros como PMT

# --- Configurações da Página ---
st.set_page_config(
    page_title="Simulador de Crédito com Garantia",
    page_icon="💰",
    layout="centered" # "wide" para tela cheia, "centered" para layout centralizado
)

# --- Título e Descrição ---
st.title("💰 Simulador de Crédito Empresarial com Garantia")
st.markdown("Preencha os campos abaixo para simular as vantagens de utilizar sua aplicação em renda fixa como garantia na operação de crédito.")
st.markdown("---")

# --- Seção de Entrada de Dados ---
st.header("Dados da Operação de Crédito")

valor_credito = st.number_input(
    "Valor do Crédito Desejado (R$):",
    min_value=1000.0,
    value=200000.0,
    step=1000.0,
    format="%.2f"
)

prazo_credito_meses = st.slider(
    "Prazo do Crédito (meses):",
    min_value=1,
    max_value=120, # Até 10 anos
    value=36,
    step=1
)
taxa_juros_credito_input = st.number_input(
    "Taxa de Juros do Crédito (com garantia) (% ao mês):", # Alterado para ao mês
    min_value=0.01, # Mínimo 0.01% para evitar divisão por zero/problemas
    max_value=5.0, # Ex: até 5% a.m. (ajuste conforme necessário)
    value=1.2, # Exemplo: 1.2% a.m.
    step=0.01,
    format="%.2f"
)
# Converte para decimal para cálculos
taxa_juros_credito_mensal = taxa_juros_credito_input / 100

iof_percentual = st.number_input(
    "IOF (% sobre o valor do crédito):",
    min_value=0.0,
    max_value=10.0,
    value=3.95, # Valor padrão sugerido: 3.95%
    step=0.01,
    format="%.2f"
)

tac_valor = st.number_input(
    "TAC - Tarifa de Abertura de Crédito (R$):",
    min_value=0.0,
    value=0.0, # Valor padrão sugerido: 0.00
    step=1.0,
    format="%.2f"
)
st.markdown("---")

st.header("Dados da Aplicação Financeira (Garantia)")

valor_aplicacao = st.number_input(
    "Valor da Aplicação em Renda Fixa (R$):",
    min_value=1000.0,
    value=400000.0,
    step=1000.0,
    format="%.2f"
)

taxa_rendimento_aplicacao_input = st.number_input(
    "Taxa de Rendimento da Aplicação (% ao mês):", # Alterado para ao mês
    min_value=0.01, # Mínimo 0.01%
    max_value=2.0, # Ex: até 2% a.m. (ajuste conforme necessário)
    value=0.8, # Exemplo: 0.8% a.m.
    step=0.01,
    format="%.2f"
)
# Converte para decimal para cálculos
taxa_rendimento_aplicacao_mensal = taxa_rendimento_aplicacao_input / 100

ir_aliquota = st.slider(
    "Alíquota de Imposto de Renda (IR) sobre Rendimento da Aplicação (%):",
    min_value=0.0,
    max_value=22.5, # Alíquota máxima comum para RF de longo prazo
    value=15.0, # Exemplo: para prazos acima de 720 dias
    step=0.5
) / 100 # Converte para decimal

st.markdown("---")

# --- Botão de Calcular ---
if st.button("Simular Operação"):
    # --- Cálculos da Operação de Crédito ---
    # Calcular IOF
    iof_total = valor_credito * (iof_percentual / 100)

    # Valor líquido recebido pelo cliente (após IOF e TAC)
    valor_liquido_recebido = valor_credito - iof_total - tac_valor

    # Calcular a parcela usando numpy_financial.pmt (pagamento mensal de uma anuidade)
    # npf.pmt(rate, nper, pv)
    # rate = taxa de juros por período
    # nper = número total de períodos (meses)
    # pv = valor presente (valor do crédito)
    # O resultado é negativo pois representa uma saída de dinheiro
    if taxa_juros_credito_mensal > 0:
        parcela_mensal_credito = -npf.pmt(
            taxa_juros_credito_mensal,
            prazo_credito_meses,
            valor_credito
        )
    else: # Se a taxa for 0, parcela é simplesmente Valor/Prazo
         parcela_mensal_credito = valor_credito / prazo_credito_meses if prazo_credito_meses > 0 else 0

    total_pago_credito = parcela_mensal_credito * prazo_credito_meses + iof_total + tac_valor
    total_juros_pagos_credito = total_pago_credito - valor_credito


    # --- Cálculos da Aplicação Financeira ---
    # Rendimento bruto mensal da aplicação
    rendimento_bruto_mensal_aplicacao = valor_aplicacao * taxa_rendimento_aplicacao_mensal

    # Rendimento bruto acumulado da aplicação
    # Montante final = PV * (1 + taxa)^nper
    montante_final_aplicacao_bruto = valor_aplicacao * ((1 + taxa_rendimento_aplicacao_mensal)**prazo_credito_meses)
    rendimento_bruto_total_aplicacao = montante_final_aplicacao_bruto - valor_aplicacao

    # Cálculo do IR sobre o rendimento bruto total
    ir_total_aplicacao = rendimento_bruto_total_aplicacao * ir_aliquota
    rendimento_liquido_total_aplicacao = rendimento_bruto_total_aplicacao - ir_total_aplicacao

    # Rendimento líquido mensal aproximado
    rendimento_liquido_mensal_aplicacao = (rendimento_liquido_total_aplicacao / prazo_credito_meses) if prazo_credito_meses > 0 else 0


    # --- Análise Comparativa ---
    # Parcela Líquida Efetiva (Parcela do Crédito - Rendimento Líquido Mensal da Aplicação)
    parcela_liquida_efetiva = parcela_mensal_credito - rendimento_liquido_mensal_aplicacao

    # Ganho Líquido Total da Operação para o Cliente
    # É o rendimento líquido que o cliente ganha com a aplicação MENOS os juros que ele paga no crédito.
    ganho_liquido_total_operacao = rendimento_liquido_total_aplicacao - total_juros_pagos_credito


    # --- Exibição dos Resultados ---
    st.header("Resultados da Simulação")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Valor do Crédito", f"R$ {valor_credito:,.2f}")
        st.metric("Prazo (meses)", f"{prazo_credito_meses}")
        st.metric("Taxa de Juros do Crédito (a.m.)", f"{taxa_juros_credito_input:,.2f}%") # Exibe o valor de entrada mensal
        st.metric("Parcela Mensal do Crédito", f"R$ {parcela_mensal_credito:,.2f}")

    with col2:
        st.metric("Valor da Aplicação em Garantia", f"R$ {valor_aplicacao:,.2f}")
        st.metric("Rendimento da Aplicação (a.m.)", f"{taxa_rendimento_aplicacao_input:,.2f}%") # Exibe o valor de entrada mensal
        st.metric("IR sobre Aplicação", f"{ir_aliquota*100:,.1f}%")
        st.metric("Rendimento Líquido Mensal da Aplicação", f"R$ {rendimento_liquido_mensal_aplicacao:,.2f}")

    st.markdown("---")

    st.subheader("O Grande Destaque para o Cliente:")
    st.success(f"**Sua Parcela Mensal Líquida Efetiva (já descontando o rendimento da aplicação) é de:**")
    st.success(f"**R$ {parcela_liquida_efetiva:,.2f}**")
    st.info("Isso significa que, parte do valor da sua parcela de crédito é coberta pelo rendimento líquido da sua aplicação!")

    st.markdown("---")

    st.subheader("Resumo Financeiro da Operação")

    st.write(f"- **Juros Totais Pagos no Crédito:** R$ {total_juros_pagos_credito:,.2f}")
    st.write(f"- **IOF Total:** R$ {iof_total:,.2f}")
    st.write(f"- **TAC:** R$ {tac_valor:,.2f}")
    st.write(f"- **Custo Total do Crédito:** R$ {total_pago_credito:,.2f}")
    st.write(f"- **Rendimento Bruto Total da Aplicação:** R$ {rendimento_bruto_total_aplicacao:,.2f}")
    st.write(f"- **Imposto de Renda Retido na Aplicação:** R$ {ir_total_aplicacao:,.2f}")
    st.write(f"- **Rendimento Líquido Total da Aplicação:** R$ {rendimento_liquido_total_aplicacao:,.2f}")
    st.write(f"- **Ganho Líquido Total da Operação (Rendimento Líquido - Juros Pagos):** R$ {ganho_liquido_total_operacao:,.2f}")

    if ganho_liquido_total_operacao >= 0:
        st.success("🎉 Esta operação de crédito, considerando o rendimento da sua aplicação, resulta em um ganho líquido total para você!")
    else:
        st.warning("⚠️ Esta operação de crédito, considerando o rendimento da sua aplicação, resulta em um custo líquido total para você.")


    # --- Observações importantes ---
    st.markdown("---")
    st.subheader("Observações Importantes:")
    st.info("""
        * Este simulador considera a **Tabela Price** para o cálculo da parcela do crédito.
        * As taxas e tarifas utilizadas são as inseridas na simulação.
        * O Imposto de Renda sobre a aplicação é calculado sobre o rendimento total, com base na alíquota informada.
        * Esta simulação não considera outros custos como seguros ou taxas de manutenção de conta.
        * O valor da aplicação serve como garantia, mas continua rendendo para você durante o prazo do crédito.
    """)