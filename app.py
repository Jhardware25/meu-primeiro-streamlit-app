import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
import base64

# INICIALIZAÇÃO GARANTIDA DE VARIÁVEIS DE CUSTO
iof_total = 0.0
tac_valor = 0.0
valor_prestamista = 0.0

def format_brl(value):
    """Formata um valor numérico para o padrão monetário brasileiro (R$ X.XXX,XX)."""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "R$ --"
    
    formatted_value = f"{value:,.2f}"
    return f"R$ {formatted_value.replace(',', 'X').replace('.', ',').replace('X', '.')}"

def format_percent(value):
    """Formata um valor numérico para o padrão percentual brasileiro (X,XX%)."""
    return f"{value:.2f}".replace(".", ",") + '%'

# --- NOVO: Configuração da página e ícone ---
st.set_page_config(layout="wide", page_title="Simulador de Crédito e Aplicação", page_icon="💰")

st.title("💰 Simulador de Crédito Com Garantia de Aplicação Financeira")

# --- ENTRADAS DO USUÁRIO ---
# --- Container para Dados da Operação de Crédito ---
st.header("Dados da Operação de Crédito:")
with st.container(border=True): # Adiciona uma borda visual para agrupar
    col_valor, col_prazo = st.columns(2)
    with col_valor:
        valor_credito = st.number_input(
            "Valor do Crédito (R$):",
            min_value=1000.0,
            value=100000.0,
            step=1000.0,
            format="%.2f"
        )
    with col_prazo:
        prazo_credito_meses = st.slider(
            "Prazo do Crédito (meses):",
            min_value=1,
            max_value=60,
            value=60,
            step=1
        )

    col_taxa, col_tipo_taxa = st.columns(2)
    with col_taxa:
        taxa_juros_pactuada_input = st.number_input(
            "Taxa de Juros Pactuada do Crédito (% ao mês):",
            min_value=0.01,
            value=0.8,
            step=0.01,
            format="%.2f"
        )
        taxa_juros_pactuada_mensal = taxa_juros_pactuada_input / 100
    with col_tipo_taxa:
        st.write(" ") # Adiciona um espaço para alinhar os rádios
        tipo_taxa_credito = st.radio(
            "Tipo de Taxa do Crédito:",
            ("Prefixada", "Pós-fixada (TR + Taxa)"),
            index=0,
            horizontal=True, # Deixa os botões de rádio na horizontal
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

# --- Expander para Custos Operacionais ---
with st.expander("Custos Operacionais do Crédito (IOF e TAC)"):
    col_iof, col_tac = st.columns(2)
    with col_iof:
        iof_percentual = st.number_input(
            "IOF Total (% do valor do crédito):",
            min_value=0.0,
            value=0.38,
            step=0.01,
            format="%.2f"
        )
    with col_tac:
        tac_percentual = st.number_input(
            "TAC (% do valor do crédito):",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f"
        )

# --- NOVO BLOCO: SEGURO PRESTAMISTA ---
# --- Container para Seguro Prestamista ---
st.header("Seguro Prestamista:")
with st.container(border=True):
    opcao_prestamista = st.radio(
        "Incluir Seguro Prestamista?",
        ("Não incluir", "Calcular por Percentual", "Informar Valor Manualmente"),
        index=0, # Padrão: Não incluir
        horizontal=True
    )

    percentual_prestamista = 0.0
    valor_prestamista = 0.0 # Garante que valor_prestamista seja inicializado

    if opcao_prestamista == "Calcular por Percentual":
        percentual_prestamista = st.slider(
            "Percentual do Seguro Prestamista (% do valor do crédito):",
            min_value=5.0,
            max_value=10.0,
            value=7.5,
            step=0.1,
            format="%.1f",
            help="Percentual do seguro prestamista sobre o valor do crédito, ajustado pela idade dos sócios."
        )
        valor_prestamista = valor_credito * (percentual_prestamista / 100)
        st.info(f"Valor do Seguro Prestamista (estimado): **{format_brl(valor_prestamista)}**")
    elif opcao_prestamista == "Informar Valor Manualmente":
        valor_prestamista = st.number_input(
            "Valor do Seguro Prestamista (R$):",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f"
        )
# --- FIM NOVO BLOCO: SEGURO PRESTAMISTA ---


# --- Container para Dados da Aplicação em Garantia ---
st.header("Dados da Aplicação em Garantia:")
with st.container(border=True):
    col_aplicacao_valor, col_aplicacao_taxa = st.columns(2)
    with col_aplicacao_valor:
        valor_aplicacao = st.number_input(
            "Valor da Aplicação em Garantia (R$):",
            min_value=1000.0,
            value=50000.0,
            step=1000.0,
            format="%.2f"
        )
    with col_aplicacao_taxa:
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

st.divider() # Adiciona um divisor visual para separar as entradas do botão


# --- BOTÃO DE SIMULAÇÃO ---
if st.button("🚀 Simular Operação", key="btn_simular_operacao", use_container_width=True): # Ícone e largura total
    # Feedback visual durante o cálculo
    with st.spinner("Calculando a simulação..."):
        import time
        time.sleep(1) # Simula um tempo de cálculo. Pode remover ou ajustar o tempo.

    # st.info("DEBUG: Botão 'Simular Operação' clicado e código começando a executar!") # Comentado

    try:
        # --- INÍCIO: SEÇÃO DE CÁLCULOS DA OPERAÇÃO DE CRÉDITO E APLICAÇÃO ---

        # 1. CÁLCULOS INICIAIS
        iof_total = valor_credito * (iof_percentual / 100)

        # --- CÁLCULO DA TAC ---
        tac_valor_calculado = valor_credito * (tac_percentual / 100)
        teto_tac = 10000.00
        tac_valor = min(tac_valor_calculado, teto_tac)

        # st.info(f"DEBUG: IOF Total: {format_brl(iof_total)}") # Comentado
        # st.info(f"DEBUG: TAC Valor: {format_brl(tac_valor)}") # Comentado
        # st.info(f"DEBUG: Valor Prestamista: {format_brl(valor_prestamista)}") # Comentado

        # --- LÓGICA DO SEGURO PRESTAMISTA E OUTROS CUSTOS (IOF, TAC, Prestamista) ---
        valor_total_para_parcela_calculo = valor_credito 
        valor_liquido_recebido = valor_credito

        custos_operacionais_totais = iof_total + tac_valor + valor_prestamista
        # st.info(f"DEBUG: Total Custos Operacionais: {format_brl(custos_operacionais_totais)}") # Comentado

        # *** LÓGICA DE FINANCIAMENTO/DESCONTO ***
        if tipo_taxa_credito == "Prefixada": 
            # SE É PREFIXADA: Custos (IOF, TAC, Prestamista) são FINANCIADOS
            valor_total_para_parcela_calculo += custos_operacionais_totais
            # valor_liquido_recebido permanece igual a valor_credito

        else: # SE É PÓS-FIXADA: Custos (IOF, TAC, Prestamista) são DESCONTADOS do valor inicial
            # valor_total_para_parcela_calculo permanece igual a valor_credito
            valor_liquido_recebido -= custos_operacionais_totais

        # st.info(f"DEBUG: Tipo Taxa Crédito: {tipo_taxa_credito}") # Comentado
        # st.info(f"DEBUG: Valor Total para Parcela (APÓS LÓGICA DE FINANCIAMENTO): {format_brl(valor_total_para_parcela_calculo)}") # Comentado
        # st.info(f"DEBUG: Valor Líquido Recebido (APÓS LÓGICA DE FINANCIAMENTO): {format_brl(valor_liquido_recebido)}") # Comentado

        # 2. CÁLCULO DA TAXA DE JUROS EFETIVA DO CRÉDITO
        if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
            taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal + taxa_indexador_mensal
        else:
            taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal
        # st.info(f"DEBUG: Taxa Juros Crédito Efetiva Mensal: {format_percent(taxa_juros_credito_efetiva_mensal * 100)}") # Comentado
                
        # 3. CÁLCULO DA PARCELA MENSAL E JUROS TOTAIS (BASE TABLE PRICE)
        if prazo_credito_meses == 0:
            parcela_mensal_credito = 0.0
            total_juros_pagos_credito = 0.0
        else:
            try:
                parcela_mensal_credito = npf.pmt(
                    taxa_juros_credito_efetiva_mensal,
                    prazo_credito_meses,
                    -valor_total_para_parcela_calculo # Usa o valor ajustado para cálculo da parcela
                )
                total_juros_pagos_credito = (parcela_mensal_credito * prazo_credito_meses) - valor_total_para_parcela_calculo
            except Exception as e:
                st.error(f"Erro no cálculo da parcela do crédito: {e}. Verifique as taxas e prazos.")
                parcela_mensal_credito = 0.0
                total_juros_pagos_credito = 0.0
        # st.info(f"DEBUG: Parcela Mensal Crédito: {format_brl(parcela_mensal_credito)}") # Comentado
        # st.info(f"DEBUG: Total Juros Pagos Crédito: {format_brl(total_juros_pagos_credito)}") # Comentado
                
        # 4. CÁLCULOS DA APLICAÇÃO
        rendimento_bruto_total_aplicacao = valor_aplicacao * ((1 + taxa_rendimento_aplicacao_mensal)**prazo_credito_meses - 1)
        ir_total_aplicacao = rendimento_bruto_total_aplicacao * ir_aliquota
        rendimento_liquido_total_aplicacao = rendimento_bruto_total_aplicacao - ir_total_aplicacao
        capital_total_acumulado_aplicacao = valor_aplicacao + rendimento_liquido_total_aplicacao
        # st.info(f"DEBUG: Rendimento Líquido Total Aplicação: {format_brl(rendimento_liquido_total_aplicacao)}") # Comentado

        # 5. CÁLCULO DO GANHO LÍQUIDO TOTAL
        ganho_liquido_total_operacao = rendimento_liquido_total_aplicacao - total_juros_pagos_credito

        # 6. CÁLCULO DO CET (Custo Efetivo Total)
        fluxo_caixa_cet_cliente = [valor_liquido_recebido] + [-parcela_mensal_credito] * prazo_credito_meses

        try:
            cet_mensal = npf.irr(fluxo_caixa_cet_cliente)
            cet_anual = ((1 + cet_mensal)**12 - 1) * 100 # Em % ao ano
        except Exception:
            cet_anual = float('nan') # Usar NaN para indicar que não foi possível calcular
            # ... (SEUS CÁLCULOS EXISTENTES TERMINAM AQUI, COMO juros_totais_credito, valor_total_pago_credito, rendimento_liquido_total_aplicacao, custo_total_operacao, ganho_liquido_total_operacao) ...

        

        # 7. GERAÇÃO DOS DADOS MENSAIS PARA OS GRÁFICOS
        historico = []
        
        saldo_atual_credito = valor_total_para_parcela_calculo # <-- USE AQUI O VALOR AJUSTADO
        saldo_atual_aplicacao = valor_aplicacao

        for mes_idx in range(1, prazo_credito_meses + 1):
            # Crédito
            juros_mes_credito = saldo_atual_credito * taxa_juros_credito_efetiva_mensal
            amortizacao_mes = parcela_mensal_credito - juros_mes_credito
            
            saldo_atual_credito = max(0, saldo_atual_credito - amortizacao_mes)

            # Aplicação
            rendimento_mes_bruto = saldo_atual_aplicacao * taxa_rendimento_aplicacao_mensal
            rendimento_liquido_mensal_aplicacao = rendimento_mes_bruto * (1 - ir_aliquota)
            saldo_atual_aplicacao += rendimento_mes_bruto # Adiciona o rendimento bruto para compor o saldo
            

            historico.append({
                'Mês': mes_idx,
                'Saldo Devedor Credito': saldo_atual_credito,
                'Parcela Mensal Credito': parcela_mensal_credito,
                'Rendimento Liquido Mensal da Aplicacao': rendimento_liquido_mensal_aplicacao, # Limpo
                'Saldo Aplicacao Garantia': saldo_atual_aplicacao
            })

        df_evolucao = pd.DataFrame(historico)
        df_fluxo_mensal = pd.DataFrame(historico) # df_fluxo_mensal é uma cópia de df_evolucao, ok.

        # st.info(f"DEBUG: df_evolucao está vazia? {df_evolucao.empty}") # Comentado
        # st.info(f"DEBUG: df_evolucao.head():\n{df_evolucao.head().to_string()}") # Comentado
        # st.info(f"DEBUG: df_fluxo_mensal está vazia? {df_fluxo_mensal.empty}") # Comentado
        # st.dataframe(df_evolucao.head()) # Comentado
        # st.dataframe(df_fluxo_mensal.head()) # Comentado

        # --- NOVO CÁLCULO DO CET ---
        # 1. Fluxo de Caixa para CET Bruto (sem descontar a aplicação)
        # Início: Valor do crédito líquido de custos iniciais
        fluxo_bruto = [valor_credito - custos_operacionais_totais]
        # Meses seguintes: Parcelas do crédito
        fluxo_bruto.extend([-p for p in df_evolucao["Parcela Mensal Credito"].tolist()])

        # Calcula a TIR (Taxa Interna de Retorno)
        try:
            cet_mensal_bruto = npf.irr(fluxo_bruto)
            # Para evitar erros de calculo com valores muito baixos ou zeros
            if isinstance(cet_mensal_bruto, (int, float)) and cet_mensal_bruto > -1:
                cet_anual_bruto = (1 + cet_mensal_bruto)**12 - 1
            else:
                cet_mensal_bruto = 0.0 # Define como zero se o resultado não for numérico válido
                cet_anual_bruto = 0.0
        except ValueError: # npf.irr retorna ValueError se não encontrar solução
            cet_mensal_bruto = 0.0
            cet_anual_bruto = 0.0


        # 2. Fluxo de Caixa para CET Líquido (descontando o rendimento da aplicação)
        # Início: Valor do crédito líquido de custos iniciais
        fluxo_liquido = [valor_credito - custos_operacionais_totais]
        # Meses seguintes: (Parcela do Crédito - Rendimento Líquido da Aplicação)
        # Se a parcela for menor que o rendimento, o fluxo é positivo para o cliente
        for i in range(prazo_credito_meses):
            fluxo_liquido.append(-(df_evolucao.loc[i, "Parcela Mensal Credito"] - df_evolucao.loc[i, "Rendimento Liquido Mensal da Aplicacao"]))

        try:
            cet_mensal_liquido = npf.irr(fluxo_liquido)
            # Para evitar erros de calculo com valores muito baixos ou zeros
            if isinstance(cet_mensal_liquido, (int, float)) and cet_mensal_liquido > -1:
                cet_anual_liquido = (1 + cet_mensal_liquido)**12 - 1
            else:
                cet_mensal_liquido = 0.0 # Define como zero se o resultado não for numérico válido
                cet_anual_liquido = 0.0
        except ValueError:
            cet_mensal_liquido = 0.0
            cet_anual_liquido = 0.0

        # ... (O restante do seu código de exibição dos resultados e gráficos virá logo abaixo) ...
        # st.info(f"DEBUG: CET Anual: {f'{format_percent(cet_anual)} a.a.' if not pd.isna(cet_anual) else 'Não Calculado'}") # Comentado

        # --- FIM DA SEÇÃO DE CÁLCULOS ---

        # --- INÍCIO: SEÇÃO DE EXIBIÇÃO DOS RESULTADOS ---
        st.header("Resultados da Simulação:")
        # st.info("DEBUG: Iniciando exibição dos resultados...") # Comentado

        st.subheader("Resumo Financeiro da Operação:")
        col1, col2, col3 = st.columns(3)
                            
        with col1:      
            st.metric("Valor Líquido Recebido", format_brl(valor_liquido_recebido))
            st.metric("Parcela Mensal do Crédito", format_brl(parcela_mensal_credito))
            st.metric("Total de Juros Pagos no Crédito", format_brl(total_juros_pagos_credito))

        with col2:
            st.metric("Rendimento Bruto Total da Aplicação", format_brl(rendimento_bruto_total_aplicacao))
            st.metric("Imposto de Renda Retido", format_brl(ir_total_aplicacao))
            st.metric("Rendimento Líquido Total", format_brl(rendimento_liquido_total_aplicacao))

        with col3:
            st.metric("Ganho Líquido Total da Operação", format_brl(ganho_liquido_total_operacao))
            
        st.subheader("Resumo Financeiro Detalhado:")
        st.write(f"- **Valor do Crédito Liberado:** {format_brl(valor_credito)}") # Adicionado para clareza

        # Exibição dos Custos Iniciais
        if iof_total > 0: # Assumindo que iof_total é calculado
            st.write(f"- **Imposto sobre Operações Financeiras (IOF):** {format_brl(iof_total)}")
        if tac_valor > 0:
            st.write(f"- **Tarifa de Abertura de Crédito (TAC):** {format_brl(tac_valor)}")
        if valor_prestamista > 0: # Assumindo que valor_prestamista é calculado/obtido
            st.write(f"- **Seguro Prestamista:** {format_brl(valor_prestamista)}")

        # Outras Informações Importantes (mantidas ou reorganizadas)
        st.write(f"- **Juros Totais Pagos no Crédito:** {format_brl(total_juros_pagos_credito)}")
        st.write(f"- **Rendimento Bruto Total da Aplicação:** {format_brl(rendimento_bruto_total_aplicacao)}")
        st.write(f"- **Imposto de Renda Retido na Aplicação:** {format_brl(ir_total_aplicacao)}")
        st.write(f"- **Rendimento Líquido Total da Aplicação:** {format_brl(rendimento_liquido_total_aplicacao)}")
        st.write(f"- **Capital Total Acumulado ao Final do Contrato:** **{format_brl(capital_total_acumulado_aplicacao)}**")
        st.write(f"- **Ganho Líquido Total da Operação (Rendimento Líquido - Juros Pagos):** **{format_brl(ganho_liquido_total_operacao)}**")

# ... (Seu bloco de CET Bruto/Líquido virá logo após este bloco, como já está) ...

        # ... (SEUS RESUMOS FINANCEIROS ATUAIS TERMINAM AQUI, como st.write(f"**Rendimento Líquido Total da Aplicação:** {format_brl(rendimento_liquido_total_aplicacao)}") ) ...

        # --- NOVO: Exibição dos CETs ---
        st.markdown("---") # Separador para o CET
        st.subheader("Custo Efetivo Total (CET):")
        
        # Exibindo o CET Bruto
        if cet_anual_bruto != 0.0: # Validação simples para IRR válido
            st.write(f"**Custo Efetivo Total (CET) Bruto Anual:** {format_percent(cet_anual_bruto * 100)} a.a.")
            st.write(f"**Custo Efetivo Total (CET) Bruto Mensal:** {format_percent(cet_mensal_bruto * 100)} a.m.")
        else:
            st.warning("Não foi possível calcular o CET Bruto. Verifique os valores de entrada ou o fluxo de caixa.")

        # Exibindo o CET Líquido (descontado o juros da aplicação)
        if cet_anual_liquido != 0.0: # Validação simples para IRR válido
            st.write(f"**Custo Efetivo Total (CET) Líquido (com ganho da aplicação) Anual:** {format_percent(cet_anual_liquido * 100)} a.a.")
            st.write(f"**Custo Efetivo Total (CET) Líquido (com ganho da aplicação) Mensal:** {format_percent(cet_mensal_liquido * 100)} a.m.")
        else:
            st.warning("Não foi possível calcular o CET Líquido. Verifique os valores de entrada ou o fluxo de caixa.")
        st.markdown("---") # Separador

        # ... (A "Lógica da Mensagem Final" e os gráficos vêm logo abaixo) ...
                            
        # Adiciona o seguro prestamista no resumo detalhado
        if valor_prestamista > 0:
            st.write(f"- **Seguro Prestamista:** {format_brl(valor_prestamista)}")
                            
        # Lógica da Mensagem Final
        if ganho_liquido_total_operacao >= 0:
            st.success("🎉 Esta operação de crédito, considerando o rendimento da sua aplicação, resulta em um **ganho líquido total** para você!")
            st.info(f"""
                💡 Você não apenas cobriu os juros e custos do crédito com sua aplicação, como também obteve um **ganho de {format_brl(ganho_liquido_total_operacao)}**!
                Isso demonstra a **vantagem de usar sua aplicação como garantia** para otimizar seus custos de crédito ao máximo.
                """)
        
        else:
            st.warning("⚠️ Esta operação de crédito, mesmo com o rendimento da sua aplicação, resulta em um **custo líquido total**.")
            st.info("O rendimento gerado pela sua aplicação foi crucial! Ele cobriu parte dos juros do seu crédito, resultando em uma redução significativa no valor final que você pagou.")


        # --- Exibição dos Gráficos ---
        st.subheader("📊 Evolução Financeira ao Longo do Contrato")
        if not df_evolucao.empty:
            fig_saldo = px.line(df_evolucao, x="Mês", y=["Saldo Devedor Credito", "Saldo Aplicacao Garantia"], # CORRIGIDO O FECHAMENTO DO PARÊNTESE E NOMES
                                title='Evolução do Saldo Devedor do Crédito vs. Saldo da Aplicação em Garantia',
                                labels={
                                    "value": "Valor (R$)",
                                    "variable": "Ativo"
                                },
                                line_shape="spline",
                                height=400
                                ) # <-- Parenteses final adicionado AQUI
                                            
            fig_saldo.update_layout(hovermode="x unified", legend_title_text='Tipo')
            fig_saldo.update_xaxes(showgrid=True, zeroline=True)
            fig_saldo.update_yaxes(showgrid=True, zeroline=True)
            st.plotly_chart(fig_saldo, use_container_width=True)
        else:
            st.info("Não é possível gerar gráficos para um prazo de contrato de 0 meses.")

        # CORRIGIDO O 'y' PARA USAR NOMES DE COLUNA LIMPOS
        if not df_fluxo_mensal.empty:
            fig_fluxo = px.bar(df_fluxo_mensal, x='Mês', y=['Parcela Mensal Credito', 'Rendimento Liquido Mensal da Aplicacao'], # <--- NOMES DE COLUNAS CORRIGIDOS AQUI
                                title='Parcela Mensal do Crédito vs. Rendimento Líquido Mensal da Aplicação',
                                labels={
                                    "value": "Valor (R$)",
                                    "variable": "Tipo de Fluxo"
                                },
                                barmode='group',
                                height=400,
                                color_discrete_map={
                                    'Parcela Mensal Credito': 'red', # <--- NOMES DE COLUNAS CORRIGIDOS AQUI
                                    'Rendimento Liquido Mensal da Aplicacao': 'green' # <--- NOMES DE COLUNAS CORRIGIDOS AQUI
                                }
                            )
            fig_fluxo.update_layout(hovermode="x unified", legend_title_text='Fluxo')
            fig_fluxo.update_xaxes(showgrid=True, zeroline=True)
            fig_fluxo.update_yaxes(showgrid=True, zeroline=True)
            st.plotly_chart(fig_fluxo, use_container_width=True)

        # st.success("DEBUG: Simulação concluída com sucesso! (Mensagem final)") # Comentado
        
    except Exception as e: # <--- ESTE EXCEPT ESTÁ ALINHADO CORRETAMENTE COM O 'try:'
        st.error(f"Ocorreu um erro durante a simulação: {e}")
        st.warning("Por favor, verifique os dados inseridos e tente novamente.") 

# --- SEÇÃO DE OBSERVAÇÕES IMPORTANTES (FORA DO if st.button) ---
# --- Observações Importantes (fora do botão, sempre visíveis) ---
st.divider() # Outro divisor
st.subheader("💡 Observações Importantes:")
st.write("""
- Os cálculos são baseados na **Tabela Price** para o crédito.
- O rendimento da aplicação é calculado com **juros compostos mensais**.
- O **Imposto de Renda (IR)** na aplicação é aplicado sobre o rendimento bruto total ao final do período, conforme a alíquota informada.
- A **TR (Taxa Referencial)** é uma taxa de juros que pode variar. Para simulações futuras, considere que seu valor pode mudar.
- Esta é apenas uma simulação e os valores reais podem variar. Consulte sempre um profissional financeiro.
""")

# O bloco de código para geração de PDF foi mantido comentado como no seu original.
# Se for ativar, a biblioteca fpdf2 precisa ser instalada e o arquivo da fonte 'NotoSans-Regular.ttf'
# precisa estar no mesmo diretório do app.py no GitHub.
            