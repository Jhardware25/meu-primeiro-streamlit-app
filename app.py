import streamlit as st
import pandas as pd
from fpdf import FPDF
import locale
import numpy_financial as npf

# --- CONFIGURAÇÃO INICIAL E HELPERS ---
st.set_page_config(
    page_title="Simulador de Operações de Crédito",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuração de locale para formatação monetária
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

def format_brl(value):
    return locale.currency(value, grouping=True, symbol=True)

def format_percent(value):
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return "N/A"

# --- CLASSE PDF (para a geração do relatório) ---
class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(50, 50, 150)
        self.cell(0, 10, "Simulador Financeiro Empresarial", ln=True, align="C")
        self.set_font("helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, "Desenvolvido por: José Costa Neto/IA Google Gemini", ln=True, align="C")
        self.ln(5)
        self.set_draw_color(150, 150, 150)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

# --- FUNÇÃO DE GERAÇÃO DO PDF (versão anterior e funcional) ---
def create_simulation_pdf(
    valor_credito, prazo_credito_meses, taxa_juros_pactuada_mensal,
    tipo_taxa_credito, taxa_indexador_mensal,
    valor_prestamista, iof_percentual, tac_percentual,
    valor_aplicacao, taxa_rendimento_aplicacao_mensal, ir_aliquota,
    df_evolucao, custos_operacionais_totais, rendimento_liquido_total_aplicacao,
    cet_anual_bruto, cet_mensal_bruto, cet_anual_liquido, cet_mensal_liquido,
    total_juros_pagos_credito, ir_total_aplicacao, capital_total_acumulado_aplicacao, ganho_liquido_total_operacao
):
    pdf = PDF(unit="mm", format="A4")
    pdf.add_page()
    try:
        pdf.add_font('DejaVuSans', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font("DejaVuSans", "", 12)
    except RuntimeError:
        pdf.set_font("helvetica", "", 12)
    
    # --- Seção 1: Detalhes do Crédito e Aplicação ---
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Resumo da Simulação Financeira", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Data da Simulação: {pd.to_datetime('today').strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detalhes do Crédito", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_credito = pdf.get_y()
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"Valor do Crédito: {format_brl(valor_credito)}", ln=True)
    pdf.cell(0, 7, f"Prazo: {prazo_credito_meses} meses", ln=True)
    pdf.cell(0, 7, f"Taxa de Juros Pactuada: {format_percent(taxa_juros_pactuada_mensal * 100)} a.m.", ln=True)
    pdf.cell(0, 7, f"Tipo de Taxa: {tipo_taxa_credito}", ln=True)
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        pdf.cell(0, 7, f"Taxa do Indexador Mensal: {format_percent(taxa_indexador_mensal * 100)} a.m.", ln=True)
    valor_liquido_recebido_final = valor_credito
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        valor_liquido_recebido_final = valor_credito - (valor_credito * (iof_percentual / 100) + min(valor_credito * (tac_percentual / 100), 10000.00) + valor_prestamista)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, f"Valor Líquido Recebido pelo Cliente: {format_brl(valor_liquido_recebido_final)}", ln=True, align="L")
    pdf.set_font("helvetica", "", 12)
    y_end_credito = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_credito - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_credito - y_start_credito + 4)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Custos Iniciais da Operação", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_custos = pdf.get_y()
    pdf.set_font("helvetica", "", 12)
    iof_total = valor_credito * (iof_percentual / 100)
    tac_valor_calculado = valor_credito * (tac_percentual / 100)
    teto_tac = 10000.00
    tac_valor = min(tac_valor_calculado, teto_tac)
    if iof_percentual > 0:
        pdf.cell(0, 7, f"IOF: {format_percent(iof_percentual)} ({format_brl(iof_total)})", ln=True, align="L")
    if tac_percentual > 0:
        pdf.cell(0, 7, f"TAC: {format_percent(tac_percentual)} ({format_brl(tac_valor)})", ln=True, align="L")
    if valor_prestamista > 0:
        pdf.cell(0, 7, f"Seguro Prestamista: {format_brl(valor_prestamista)}", ln=True)
    custos_operacionais_totais_pdf = iof_total + tac_valor + valor_prestamista
    pdf.cell(0, 7, f"Total de Custos Iniciais: {format_brl(custos_operacionais_totais_pdf)}", ln=True)
    y_end_custos = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_custos - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_custos - y_start_custos + 4)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detalhes da Aplicação", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_aplicacao = pdf.get_y()
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"Valor da Aplicação: {format_brl(valor_aplicacao)}", ln=True)
    pdf.cell(0, 7, f"Taxa de Rendimento: {format_percent(taxa_rendimento_aplicacao_mensal * 100)} a.m.", ln=True)
    pdf.cell(0, 7, f"Alíquota de Imposto de Renda: {format_percent(ir_aliquota * 100)}", ln=True)
    pdf.cell(0, 7, f"Rendimento Líquido Total da Aplicação: {format_brl(rendimento_liquido_total_aplicacao)}", ln=True)
    y_end_aplicacao = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_aplicacao - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_aplicacao - y_start_aplicacao + 4)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Resumo Financeiro Detalhado", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_resumo = pdf.get_y()
    pdf.set_font("helvetica", "", 12)
    parcela_mensal_credito_media = df_evolucao.loc[1:, 'Parcela Mensal Credito'].mean()
    parcela_mensal_liquida_media = (df_evolucao.loc[1:, 'Parcela Mensal Credito'] - df_evolucao.loc[1:, 'Rendimento Liquido Mensal da Aplicacao']).mean()
    
    pdf.cell(0, 7, f"Parcela Mensal do Crédito: {format_brl(parcela_mensal_credito_media)}", ln=True)
    pdf.cell(0, 7, f"Parcela Mensal do Crédito (com desconto da Aplicação): {format_brl(parcela_mensal_liquida_media)}", ln=True)
    pdf.cell(0, 7, f"Juros Totais Pagos no Crédito: {format_brl(total_juros_pagos_credito)}", ln=True)
    pdf.cell(0, 7, f"Imposto de Renda Retido na Aplicação: {format_brl(ir_total_aplicacao)}", ln=True)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, f"Capital Total Acumulado ao Final do Contrato: {format_brl(capital_total_acumulado_aplicacao)}", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.set_font("helvetica", "B", 12)
    if ganho_liquido_total_operacao >= 0:
        pdf.set_text_color(0, 0, 200)
        pdf.cell(0, 7, f"Ganho Líquido Total da Operação: {format_brl(ganho_liquido_total_operacao)}", ln=True)
    else:
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 7, f"Custo Líquido Total da Operação: {format_brl(abs(ganho_liquido_total_operacao))}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 12)
    y_end_resumo = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_resumo - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_resumo - y_start_resumo + 4)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Custo Efetivo Total (CET)", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_cet = pdf.get_y()
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"CET Bruto Anual: {format_percent(cet_anual_bruto * 100)} a.a.", ln=True, align="L")
    pdf.cell(0, 7, f"CET Bruto Mensal: {format_percent(cet_mensal_bruto * 100)} a.m.", ln=True, align="L")
    if cet_anual_liquido != 0.0:
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 7, f"CET Líquido (com ganho da aplicação) Anual: {format_percent(cet_anual_liquido * 100)} a.a.", ln=True, align="L")
        pdf.cell(0, 7, f"CET Líquido (com ganho da aplicação) Mensal: {format_percent(cet_mensal_liquido * 100)} a.m.", ln=True, align="L")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 12)
    else:
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 7, "CET Líquido: Não foi possível calcular.", ln=True, align="L")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 12)
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 10)
    current_x = pdf.l_margin + 5
    cell_width = pdf.w - pdf.l_margin - pdf.r_margin - 10
    pdf.set_x(current_x)
    pdf.cell(cell_width, 7, "O CET inclui:", ln=True, align="L")
    pdf.set_font("DejaVuSans", "", 10)
    pdf.set_x(current_x)
    pdf.multi_cell(cell_width, 6, "• Juros (taxa de juros do crédito) \n• Tarifas (como a TAC - Tarifa de Abertura de Crédito) \n• Impostos (como o IOF - Imposto sobre Operações Financeiras) \n• Seguros (como o Seguro Prestamista, se aplicável) \n• Outras despesas cobradas na operação", align="L")
    y_end_cet = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_cet - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_cet - y_start_cet + 4)
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Observações Importantes", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)
    y_start_observacoes = pdf.get_y()
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, "1. A simulação de crédito utiliza o sistema de amortização Tabela Price. \n2. Os cálculos de juros e rendimentos são baseados no regime de juros compostos. \n3. O Imposto de Renda (IR) incide apenas sobre o rendimento bruto da aplicação, conforme alíquota informada. \n4. Para taxas pós-fixadas, a Taxa Referencial (TR) ou outro indexador pode influenciar os valores das parcelas e rendimentos da aplicação. \n5. Os valores apresentados são estimativas e podem variar conforme as condições de mercado e políticas da instituição financeira. ", align="L")
    y_end_observacoes = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_observacoes - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_observacoes - y_start_observacoes + 4)
    pdf.ln(5)
    
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Evolução Mensal da Operação", ln=True, align="C")
    pdf.ln(5)
    
    def draw_table_header():
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(20, 10, "Mês", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Parcela Crédito (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Saldo Devedor (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Rendimento Aplic. (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Saldo Aplic. (R$)", 1, 1, 'C', 1)
    
    draw_table_header()
    
    pdf.set_font("helvetica", "", 8)
    for _, row in df_evolucao.iterrows():
        if pdf.get_y() > 250:
            pdf.add_page()
            draw_table_header()
            pdf.set_font("helvetica", "", 8)
        
        pdf.cell(20, 8, str(row['Mês']), 1, 0, 'C')
        pdf.cell(40, 8, format_brl(row['Parcela Mensal Credito']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Saldo Devedor Credito']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Rendimento Liquido Mensal da Aplicacao']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Saldo Aplicacao Garantia']), 1, 1, 'R')
    
    return bytes(pdf.output(dest='S'))

# --- INTERFACE E LÓGICA DO STREAMLIT ---
st.title("Simulador de Operações de Crédito")
st.markdown("Preencha os dados abaixo para simular uma operação de crédito com garantia financeira.")

with st.sidebar:
    st.header("Detalhes do Crédito")
    valor_credito = st.number_input("Valor do Crédito (R$)", min_value=1.0, value=200000.0, step=1000.0)
    prazo_credito_meses = st.number_input("Prazo do Crédito (meses)", min_value=1, value=60, step=1)
    taxa_juros_pactuada_mensal = (
        st.number_input("Taxa de Juros Pactuada (% a.m.)", min_value=0.0, value=1.56, step=0.01, format="%.2f") / 100
    )
    tipo_taxa_credito = st.selectbox(
        "Tipo de Taxa", ("Prefixada", "Pós-fixada (TR + Taxa)")
    )
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        taxa_indexador_mensal = (
            st.number_input("Taxa do Indexador (% a.m.)", min_value=0.0, value=0.1, step=0.01, format="%.2f") / 100
        )
    else:
        taxa_indexador_mensal = 0.0

    st.header("Custos do Crédito")
    iof_percentual = st.number_input("IOF (% sobre o valor)", min_value=0.0, value=3.77, step=0.01, format="%.2f")
    tac_percentual = st.number_input("TAC (% sobre o valor)", min_value=0.0, value=3.00, step=0.01, format="%.2f")
    valor_prestamista = st.number_input("Seguro Prestamista (R$)", min_value=0.0, value=20000.0, step=100.0)

    st.header("Detalhes da Aplicação (Garantia)")
    valor_aplicacao = st.number_input("Valor da Aplicação (R$)", min_value=0.0, value=100000.0, step=1000.0)
    taxa_rendimento_aplicacao_mensal = (
        st.number_input("Taxa de Rendimento da Aplicação (% a.m.)", min_value=0.0, value=0.92, step=0.01, format="%.2f") / 100
    )
    ir_aliquota = (
        st.number_input("Alíquota de Imposto de Renda (% sobre o rendimento)", min_value=0.0, value=0.0, step=0.01, format="%.2f") / 100
    )
    
# --- BOTÃO DE SIMULAÇÃO E LÓGICA PRINCIPAL ---
if st.button("🚀 **Simular Operação**", key="btn_simular_nova_operacao", use_container_width=True):
    with st.spinner("Calculando a simulação..."):
        import time
        time.sleep(1)

    try:
        # 1. CÁLCULOS INICIAIS
        iof_percentual_adicional = 0.0038
        iof_total = valor_credito * (iof_percentual / 100)
        tac_valor_calculado = valor_credito * (tac_percentual / 100)
        teto_tac = 10000.00
        tac_valor = min(tac_valor_calculado, teto_tac)
        custos_operacionais_totais = iof_total + tac_valor + valor_prestamista
        valor_liquido_recebido = valor_credito - custos_operacionais_totais
        
        # 2. CÁLCULO DA EVOLUÇÃO DO CRÉDITO E DA APLICAÇÃO
        df_evolucao = pd.DataFrame(
            {
                "Mês": range(prazo_credito_meses + 1),
                "Saldo Devedor Credito": 0.0,
                "Juros Mensal Credito": 0.0,
                "Amortizacao Mensal": 0.0,
                "Parcela Mensal Credito": 0.0,
                "Saldo Aplicacao Garantia": 0.0,
                "Rendimento Bruto Mensal da Aplicacao": 0.0,
                "IR Mensal da Aplicacao": 0.0,
                "Rendimento Liquido Mensal da Aplicacao": 0.0,
            }
        )
        df_evolucao.loc[0, "Saldo Devedor Credito"] = valor_credito
        df_evolucao.loc[0, "Saldo Aplicacao Garantia"] = valor_aplicacao
        
        # Calcula a parcela fixa para a Tabela Price
        parcela_mensal_credito_fixa = npf.pmt(taxa_juros_pactuada_mensal, prazo_credito_meses, -valor_credito)

        for mes in range(1, prazo_credito_meses + 1):
            juros_mensal_credito = df_evolucao.loc[mes - 1, "Saldo Devedor Credito"] * taxa_juros_pactuada_mensal
            amortizacao_mensal = parcela_mensal_credito_fixa - juros_mensal_credito
            saldo_devedor_credito = df_evolucao.loc[mes - 1, "Saldo Devedor Credito"] - amortizacao_mensal

            saldo_aplicacao_garantia = df_evolucao.loc[mes - 1, "Saldo Aplicacao Garantia"]
            rendimento_bruto_mensal_aplicacao = saldo_aplicacao_garantia * taxa_rendimento_aplicacao_mensal
            ir_mensal_aplicacao = rendimento_bruto_mensal_aplicacao * ir_aliquota
            rendimento_liquido_mensal_aplicacao = rendimento_bruto_mensal_aplicacao - ir_mensal_aplicacao
            saldo_aplicacao_garantia += rendimento_liquido_mensal_aplicacao

            df_evolucao.loc[mes, "Saldo Devedor Credito"] = saldo_devedor_credito
            df_evolucao.loc[mes, "Juros Mensal Credito"] = juros_mensal_credito
            df_evolucao.loc[mes, "Amortizacao Mensal"] = amortizacao_mensal
            df_evolucao.loc[mes, "Parcela Mensal Credito"] = parcela_mensal_credito_fixa
            df_evolucao.loc[mes, "Saldo Aplicacao Garantia"] = saldo_aplicacao_garantia
            df_evolucao.loc[mes, "Rendimento Bruto Mensal da Aplicacao"] = rendimento_bruto_mensal_aplicacao
            df_evolucao.loc[mes, "IR Mensal da Aplicacao"] = ir_mensal_aplicacao
            df_evolucao.loc[mes, "Rendimento Liquido Mensal da Aplicacao"] = rendimento_liquido_mensal_aplicacao

        total_juros_pagos_credito = df_evolucao['Juros Mensal Credito'].sum()
        rendimento_liquido_total_aplicacao = df_evolucao['Rendimento Liquido Mensal da Aplicacao'].sum()
        ir_total_aplicacao = df_evolucao['IR Mensal da Aplicacao'].sum()
        capital_total_acumulado_aplicacao = df_evolucao.loc[prazo_credito_meses, "Saldo Aplicacao Garantia"]

        # 3. CÁLCULO DO GANHO LÍQUIDO E CET
        ganho_liquido_total_operacao = (
            capital_total_acumulado_aplicacao - valor_aplicacao
        ) - (total_juros_pagos_credito + custos_operacionais_totais - (valor_aplicacao * iof_percentual_adicional))

        cet_mensal_bruto = -npf.rate(
            nper=prazo_credito_meses,
            pmt=parcela_mensal_credito_fixa,
            pv=valor_liquido_recebido,
            fv=0
        )
        cet_anual_bruto = ((1 + cet_mensal_bruto) ** 12) - 1
        
        cet_mensal_liquido = -npf.rate(
            nper=prazo_credito_meses,
            pmt=parcela_mensal_credito_fixa - df_evolucao.loc[1:, 'Rendimento Liquido Mensal da Aplicacao'].mean(),
            pv=valor_liquido_recebido,
            fv=-capital_total_acumulado_aplicacao
        )
        cet_anual_liquido = ((1 + cet_mensal_liquido) ** 12) - 1

        st.success("Simulação realizada com sucesso!")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        st.subheader("Resumo Financeiro da Operação")
        st.write(f"**Valor Líquido Recebido pelo Cliente:** {format_brl(valor_liquido_recebido)}")
        st.write(f"**Ganho Líquido Total com a Aplicação:** {format_brl(rendimento_liquido_total_aplicacao)}")
        st.write(f"**Total de Impostos (IR) sobre a Aplicação:** {format_brl(ir_total_aplicacao)}")
        st.write(f"**Total de Juros Pagos no Crédito:** {format_brl(total_juros_pagos_credito)}")
        st.write(f"**Total de Custos Iniciais (IOF, TAC, Seguro):** {format_brl(custos_operacionais_totais)}")
        
        st.write("---")
        if ganho_liquido_total_operacao > 0:
            st.markdown(f"<h3 style='color:green;'>Ganho Líquido Total da Operação: {format_brl(ganho_liquido_total_operacao)}</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='color:red;'>Custo Líquido Total da Operação: {format_brl(abs(ganho_liquido_total_operacao))}</h3>", unsafe_allow_html=True)
        st.write("---")
        
        # --- TABELA E GRÁFICO (RESTAURADOS) ---
        st.subheader("Evolução Mensal da Operação")
        df_display = df_evolucao.loc[1:, ['Mês', 'Parcela Mensal Credito', 'Saldo Devedor Credito', 'Rendimento Liquido Mensal da Aplicacao', 'Saldo Aplicacao Garantia']].copy()
        
        # Formatação para exibição
        df_display['Parcela Mensal Credito'] = df_display['Parcela Mensal Credito'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_display['Saldo Devedor Credito'] = df_display['Saldo Devedor Credito'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_display['Rendimento Liquido Mensal da Aplicacao'] = df_display['Rendimento Liquido Mensal da Aplicacao'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_display['Saldo Aplicacao Garantia'] = df_display['Saldo Aplicacao Garantia'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.dataframe(df_display, use_container_width=True)

        st.line_chart(df_evolucao.set_index('Mês')[['Saldo Devedor Credito', 'Saldo Aplicacao Garantia']])
        
        # --- BOTÃO PARA GERAR O PDF ---
        with st.spinner("Gerando PDF..."):
            pdf_bytes = create_simulation_pdf(
                valor_credito, prazo_credito_meses, taxa_juros_pactuada_mensal,
                tipo_taxa_credito, taxa_indexador_mensal,
                valor_prestamista, iof_percentual, tac_percentual,
                valor_aplicacao, taxa_rendimento_aplicacao_mensal, ir_aliquota,
                df_evolucao, custos_operacionais_totais, rendimento_liquido_total_aplicacao,
                cet_anual_bruto, cet_mensal_bruto, cet_anual_liquido, cet_mensal_liquido,
                total_juros_pagos_credito, ir_total_aplicacao, capital_total_acumulado_aplicacao, ganho_liquido_total_operacao
            )
        
        st.download_button(
            label="Download PDF da Simulação",
            data=pdf_bytes,
            file_name="simulacao_completa.pdf",
            mime="application/pdf"
        )
            
    except Exception as e:
        st.error(f"Ocorreu um erro durante a simulação: {e}")