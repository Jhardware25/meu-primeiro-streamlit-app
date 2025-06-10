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
    # Garante duas casas decimais e troca ponto por vírgula e vírgula por ponto
    # Ex: 10000.00 -> '10,000.00' -> '10X000,00' -> '10.000,00'
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(value):
    """Formata um valor numérico para o padrão percentual brasileiro (X,XX%)."""
    # Formata com duas casas decimais e troca ponto por vírgula
    return f"{value:.2f}".replace(".", ",") + '%'

st.set_page_config(layout="wide")

# Função para formatar valores em Reais (R$) com padrão brasileiro
def format_brl(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "R$ --"
    
    formatted_value = f"{value:,.2f}"
    return f"R$ {formatted_value.replace(',', 'X').replace('.', ',').replace('X', '.')}"


st.title("💰 Simulador de Crédito Com Garantia de Aplicação Financeira")

# --- ENTRADAS DO USUÁRIO ---
st.header("Dados da Operação de Crédito:")

valor_credito = st.number_input(
    "Valor do Crédito (R$):",
    min_value=1000.0,
    value=100000.0,
    step=1000.0,
    format="%.2f"
)
prazo_credito_meses = st.slider(
    "Prazo do Crédito (meses):",
    min_value=1,
    max_value=60,
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

# --- NOVO BLOCO: SEGURO PRESTAMISTA ---
st.header("Seguro Prestamista:")
opcao_prestamista = st.radio(
    "Incluir Seguro Prestamista?",
    ("Não incluir", "Calcular por Percentual", "Informar Valor Manualmente"),
    index=0 # Padrão: Não incluir
)

percentual_prestamista = 0.0
valor_prestamista = 0.0

if opcao_prestamista == "Calcular por Percentual":
    percentual_prestamista = st.slider(
        "Percentual do Seguro Prestamista (% do valor do crédito):",
        min_value=5.0,
        max_value=10.0,
        value=7.5, # Um valor médio entre 5% e 10%
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
   #st.info("DEBUG: Botão 'Simular Operação' clicado e código começando a executar!") # Adicione esta linha AQUI

    try:
    # --- INÍCIO: SEÇÃO DE CÁLCULOS DA OPERAÇÃO DE CRÉDITO E APLICAÇÃO ---

    # 1. CÁLCULOS INICIAIS
        iof_total = valor_credito * (iof_percentual / 100)

        # --- INÍCIO DA ALTERAÇÃO PARA A TAC ---
        # Calcula o valor da TAC baseado no percentual
        tac_valor_calculado = valor_credito * (tac_percentual / 100)

        # Define o teto máximo para a TAC
        teto_tac = 10000.00

        # Aplica a regra: se o valor calculado for maior que o teto, usa o teto
        tac_valor = min(tac_valor_calculado, teto_tac)

        #st.info(f"DEBUG: IOF Total: {format_brl(iof_total)}")
        #st.info(f"DEBUG: TAC Valor: {format_brl(tac_valor)}")
        #st.info(f"DEBUG: Valor Prestamista: {format_brl(valor_prestamista)}")
        #st.info(f"DEBUG: Total Custos Operacionais: {format_brl(iof_total + tac_valor + valor_prestamista)}")

        # --- FIM DA ALTERAÇÃO PARA A TAC ---
        
        # --- LÓGICA DO SEGURO PRESTAMISTA E OUTROS CUSTOS (IOF, TAC, Prestamista) ---

    # Inicializa o valor que será a base para o cálculo das parcelas.
    # Por padrão, começa com o valor do crédito solicitado.
        valor_total_para_parcela_calculo = valor_credito 

        # Inicializa o valor líquido que o cliente receberá.
        # Por padrão, começa com o valor do crédito solicitado.
        valor_liquido_recebido = valor_credito

        # Soma todos os custos operacionais (IOF, TAC, Prestamista)
        total_de_custos_operacionais = iof_total + tac_valor + valor_prestamista
        #st.info(f"DEBUG: Total Custos Operacionais: {format_brl(total_de_custos_operacionais)}") # <--- Esta linha de DEBUG vem logo após.


        # *** AQUI ESTÁ A LÓGICA DE FINANCIAMENTO/DESCONTO ***
        if tipo_taxa_credito == "Prefixada": 
            # SE É PREFIXADA: Custos (IOF, TAC, Prestamista) são FINANCIADOS
            
            # 1. Base para as Parcelas: O valor que será parcelado é o crédito + todos os custos.
            valor_total_para_parcela_calculo += total_de_custos_operacionais 
            
            # 2. Valor Líquido Recebido: O cliente recebe o valor do crédito solicitado integralmente.
            #    Os custos são diluídos nas parcelas, NÃO descontados do valor inicial que ele recebe.
            #    valor_liquido_recebido já está com valor_credito, então não precisa de ajuste aqui.

        else: # SE É PÓS-FIXADA: Custos (IOF, TAC, Prestamista) são DESCONTADOS do valor inicial
            
            # 1. Base para as Parcelas: O valor que será parcelado é APENAS o valor do crédito.
            #    Os custos foram pagos à vista, não foram financiados.
            #    valor_total_para_parcela_calculo já está com valor_credito, então não precisa de ajuste aqui.
            
            # 2. Valor Líquido Recebido: O cliente recebe o crédito MENOS todos os custos.
            valor_liquido_recebido -= total_de_custos_operacionais

        # --- FIM DA LÓGICA DE FINANCIAMENTO/DESCONTO ---


        # *** PONTO CRUCIAL: Verifique onde as parcelas são calculadas! ***
        # A função ou o loop que calcula as parcelas (ex: calcular_amortizacao(valor_principal, ...))
        # deve OBRIGATORIAMENTE usar 'valor_total_para_parcela_calculo' como o valor principal,
        # e NÃO 'valor_credito' diretamente.
        # Exemplo:
        # tabela_amortizacao = calcular_amortizacao(valor_total_para_parcela_calculo, ...)

        #st.info(f"DEBUG: Tipo Taxa Crédito: {tipo_taxa_credito}")
        #st.info(f"DEBUG: Valor Total para Parcela (APÓS LÓGICA DE FINANCIAMENTO): {format_brl(valor_total_para_parcela_calculo)}")
        #st.info(f"DEBUG: Valor Líquido Recebido (APÓS LÓGICA DE FINANCIAMENTO): {format_brl(valor_liquido_recebido)}")

                # 2. CÁLCULO DA TAXA DE JUROS EFETIVA DO CRÉDITO
        if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
                    taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal + taxa_indexador_mensal
        else:
                    taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal
        #st.info(f"DEBUG: Taxa Juros Crédito Efetiva Mensal: {format_percent(taxa_juros_credito_efetiva_mensal * 100)}")
            
                
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
        #st.info(f"DEBUG: Parcela Mensal Crédito: {format_brl(parcela_mensal_credito)}")
        #st.info(f"DEBUG: Total Juros Pagos Crédito: {format_brl(total_juros_pagos_credito)}")
                

                # 4. CÁLCULOS DA APLICAÇÃO
        rendimento_bruto_total_aplicacao = valor_aplicacao * ((1 + taxa_rendimento_aplicacao_mensal)**prazo_credito_meses - 1)
        ir_total_aplicacao = rendimento_bruto_total_aplicacao * ir_aliquota
        rendimento_liquido_total_aplicacao = rendimento_bruto_total_aplicacao - ir_total_aplicacao
        capital_total_acumulado_aplicacao = valor_aplicacao + rendimento_liquido_total_aplicacao
        #st.info(f"DEBUG: Rendimento Líquido Total Aplicação: {format_brl(rendimento_liquido_total_aplicacao)}")

                # 5. CÁLCULO DO GANHO LÍQUIDO TOTAL
        ganho_liquido_total_operacao = rendimento_liquido_total_aplicacao - total_juros_pagos_credito

                # 6. CÁLCULO DO CET (Custo Efetivo Total)
                # Fluxo de caixa para o cálculo do CET deve incluir TODOS os custos iniciais e as parcelas
                # O valor_liquido_recebido já reflete os custos iniciais (IOF, TAC, Prestamista).
        fluxo_caixa_cet_cliente = [valor_liquido_recebido] + [-parcela_mensal_credito] * prazo_credito_meses

        try:
                    cet_mensal = npf.irr(fluxo_caixa_cet_cliente)
                    cet_anual = ((1 + cet_mensal)**12 - 1) * 100 # Em % ao ano
        except Exception:
                    cet_anual = float('nan') # Usar NaN para indicar que não foi possível calcular
        #st.info(f"DEBUG: CET Anual: {f'{format_percent(cet_anual)} a.a.' if not pd.isna(cet_anual) else 'Não Calculado'}")        

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
                    saldo_atual_aplicacao += rendimento_mes_bruto

                    historico.append({
                        'Mês': mes_idx,
                        'Saldo Devedor Credito (R$)': saldo_atual_credito,
                        'Parcela Mensal Credito (R$)': parcela_mensal_credito,
                        'Rendimento Liquido Mensal da Aplicacao': rendimento_mes_bruto * (1 - ir_aliquota),
                        'Saldo da Aplicacao Garantia': saldo_atual_aplicacao
                    })

        df_evolucao = pd.DataFrame(historico)
        df_fluxo_mensal = pd.DataFrame(historico)

        st.info(f"DEBUG: df_evolucao está vazia? {df_evolucao.empty}")
        st.info(f"DEBUG: df_evolucao.head(): {df_evolucao.head().to_string()}") # Mostra as primeiras linhas do DataFrame
        st.info(f"DEBUG: df_fluxo_mensal está vazia? {df_fluxo_mensal.empty}")
        st.dataframe(df_evolucao.head())
        st.dataframe(df_fluxo_mensal.head())
        
                # --- FIM DA SEÇÃO DE CÁLCULOS ---


                # --- INÍCIO: SEÇÃO DE EXIBIÇÃO DOS RESULTADOS ---
        st.header("Resultados da Simulação:")
        #st.info("DEBUG: Iniciando exibição dos resultados...")

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
                            if not pd.isna(cet_anual): # Só exibe se o CET foi calculado
                                st.metric("Custo Efetivo Total (CET) Anual",f"{format_percent(cet_anual)} a.a.")
                                
                            else: 
                                st.metric("Custo Efetivo Total (CET) Anual", "Não Calculado")


        st.subheader("Resumo Financeiro Detalhado:")
        st.write(f"- **Juros Totais Pagos no Crédito:** {format_brl(total_juros_pagos_credito)}")
        st.write(f"- **Rendimento Bruto Total da Aplicação:** {format_brl(rendimento_bruto_total_aplicacao)}")
        st.write(f"- **Imposto de Renda Retido na Aplicação:** {format_brl(ir_total_aplicacao)}")
        st.write(f"- **Rendimento Líquido Total da Aplicação:** {format_brl(rendimento_liquido_total_aplicacao)}")
        st.write(f"- **Capital Total Acumulado ao Final do Contrato:** **{format_brl(capital_total_acumulado_aplicacao)}**")
        st.write(f"- **Ganho Líquido Total da Operação (Rendimento Líquido - Juros Pagos):** **{format_brl(ganho_liquido_total_operacao)}**")
        st.write(f"- **Tarifa de Abertura de Crédito (TAC):** {format_brl(tac_valor)}")
                    
                    # Adiciona o seguro prestamista no resumo detalhado
        if valor_prestamista > 0:
                    st.write(f"- **Seguro Prestamista:** {format_brl(valor_prestamista)}")
                    
                    if not pd.isna(cet_anual):
                        st.write(f"- **Custo Efetivo Total (CET):** {format_percent(cet_anual)} a.a.")
                    else:
                        st.write("- **Custo Efetivo Total (CET) Anual:** Não foi possível calcular. Verifique os parâmetros da operação.")


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
                        fig_saldo = px.line(df_evolucao, x="Mês", y=["Saldo Devedor Credito", "Saldo Aplicacao Garantia"])
                        title='Evolução do Saldo Devedor do Crédito vs. Saldo da Aplicação em Garantia',
                        labels={
                        "value": "Valor (R$)",
                                "variable": "Ativo"
                            },
                        line_shape="spline",
                        height=400
                                            
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

                # --- NOVO BLOCO: GERAR RELATÓRIO PDF ---
                # ... (código antes do botão "Download Relatório PDF") ...

            

            # ... (restante do seu app.py) ...

                # st.subheader("Gerar Relatório Detalhado")
            # st.info("Status Atual: Pronto para gerar PDF. Clique no botão.") # Mensagem de status inicial

            # if st.button("Download Relatório PDF", key="btn_download_pdf"):
            #     st.info("Status Atual: Botão clicado. Iniciando tentativa de geração de PDF...") # Confirma clique
            #     try:
            #         from fpdf import FPDF

            #         pdf = FPDF() 
            #         pdf.add_page()

            #         # --- Tenta adicionar a fonte Noto Sans com tratamento de erro mais específico ---
            #         try:
            #             pdf.add_font('NotoSans', '', 'NotoSans-Regular.ttf', uni=True)
            #             pdf.set_font('NotoSans', '', 12)
            #             st.success("Status Atual: Fonte 'NotoSans' carregada com sucesso!") 
            #         except Exception as font_error:
            #             st.error(f"❌ Erro CRÍTICO ao carregar a fonte: {font_error}")
            #             st.exception(font_error)
            #             st.warning("O PDF não pode ser gerado sem a fonte. Verifique o nome do arquivo da fonte e se ele está no GitHub.")
            #             st.stop()

            #         # --- Conteúdo do PDF de teste ---
            #         pdf.cell(0, 10, 'Olá, este é um PDF de teste gerado pelo Streamlit!', 0, 1, 'C')
            #         pdf.cell(0, 10, 'Se você conseguir baixar, o fpdf2 está funcionando.', 0, 1, 'C')

            #         pdf_output_bytes = pdf.output(dest='S').encode('latin-1')
            #         st.success(f"Status Atual: PDF gerado como bytes. Tamanho: {len(pdf_output_bytes)} bytes.") 

            #         # --- Tenta com st.download_button ---
            #         st.download_button(
            #             label="Clique para Baixar o PDF (Botão Streamlit)",
            #             data=pdf_output_bytes,
            #             file_name="teste_pdf_streamlit.pdf",
            #             mime="application/pdf"
            #         )
            #         st.info("Status Atual: Botão de download do Streamlit criado.")

            #         # --- Tenta com link Base64 (Alternativo) ---
            #         b64_pdf = base64.b64encode(pdf_output_bytes).decode('latin-1')
            #         href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="teste_pdf_base64.pdf">Clique para Baixar o PDF (Link Alternativo - Mais confiável)</a>'
            #         st.markdown(href, unsafe_allow_html=True)
            #         st.info("Status Atual: Link de download alternativo criado.")

            #     except Exception as e:
            #         st.error("❌ Ocorreu um erro INESPERADO ao gerar o PDF!")
            #         st.exception(e)
            #         st.warning("Isso indica um problema mais fundamental. Por favor, entre em contato com o suporte ou verifique a aba 'Activity' no Streamlit Cloud.")

            #     st.success("Status: Processo de geração de PDF finalizado.")
        #st.success("DEBUG: Simulação concluída com sucesso! (Mensagem final)")
        
    except Exception as e: # <--- ADICIONE ESTE BLOCO AQUI, ALINHADO COM O 'try:'
                st.error(f"Ocorreu um erro durante a simulação: {e}")
                st.warning("Por favor, verifique os dados inseridos e tente novamente.")    

                # --- FIM DO BLOCO if st.button ---
                st.markdown("---")
                st.subheader("Observações Importantes:")
                st.write("""
                - Os cálculos são baseados na **Tabela Price** para o crédito.
                - O rendimento da aplicação é calculado com **juros compostos mensais**.
                - O **Imposto de Renda (IR)** na aplicação é aplicado sobre o rendimento bruto total ao final do período, conforme a alíquota informada.
                - A **TR (Taxa Referencial)** é uma taxa de juros que pode variar. Para simulações futuras, considere que seu valor pode mudar.
                - Esta é apenas uma simulação e os valores reais podem variar. Consulte sempre um profissional financeiro.
                """)
            