import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
import base64
from fpdf import FPDF
# Defina uma subclasse para personalizar o rodapé
class PDF(FPDF):
    def footer(self):
        # Defina a fonte para o rodapé
        self.set_y(-15) # Posição a 1.5 cm do final da página
        self.set_font('helvetica', 'I', 8) # 'I' para itálico, 8 para tamanho menor
        
        # O texto do rodapé
        footer_text = "Simulador financeiro desenvolvido com Streamlit e Python"
        
        # Calcular a largura do texto para alinhar à direita
        text_width = self.get_string_width(footer_text)
        
        # Definir a posição X para alinhamento à direita
        # Largura da página - margem direita - largura do texto
        x_position = self.w - self.r_margin - text_width
        
        self.set_x(x_position) # Define a posição X para o alinhamento
        self.cell(0, 10, footer_text, 0, 0, 'R') # 'R' para alinhar o texto à direita da célula
        
        # Opcional: Adicionar número da página, se desejar
        # self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C') # Para centralizar o número da página

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


# --- NOVA FUNÇÃO PARA GERAR O PDF ---
def create_simulation_pdf(
    valor_credito, prazo_credito_meses, taxa_juros_pactuada_mensal,
    tipo_taxa_credito, taxa_indexador_mensal,
    valor_prestamista, iof_percentual, tac_percentual,
    valor_aplicacao, taxa_rendimento_aplicacao_mensal, ir_aliquota,
    df_evolucao, custos_operacionais_totais, rendimento_liquido_total_aplicacao,
    cet_anual_bruto, cet_mensal_bruto, cet_anual_liquido, cet_mensal_liquido,
    total_juros_pagos_credito, ir_total_aplicacao, capital_total_acumulado_aplicacao, ganho_liquido_total_operacao,
    usar_carencia, meses_carencia, valor_liquido_recebido, custos_financiados
):
    pdf = PDF(unit="mm", format="A4")
    pdf.add_page()
    pdf.add_font('DejaVuSans', '', 'DejaVuSans.ttf', uni=True)
    y_start_header = pdf.get_y()
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(50, 50, 150)
    pdf.cell(0, 10, "Simulador Financeiro Empresarial", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, "Desenvolvido por: José Costa Neto/IA Google Gemini", ln=True, align="C")
    pdf.ln(5)
    pdf.set_draw_color(150, 150, 150)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
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
    pdf.cell(0, 7, f"Custos Financiados: {'Sim' if custos_financiados else 'Não'}", ln=True)
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        pdf.cell(0, 7, f"Taxa do Indexador Mensal: {format_percent(taxa_indexador_mensal * 100)} a.m.", ln=True)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, f"Valor Líquido Recebido pelo Cliente: {format_brl(valor_liquido_recebido)}", ln=True, align="L")
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
    if iof_percentual > 0:
        pdf.cell(0, 7, f"IOF: {format_percent(iof_percentual)} ({format_brl(iof_total)})", ln=True, align="L")
    if tac_percentual > 0:
        pdf.cell(0, 7, f"TAC: {format_percent(tac_percentual)} ({format_brl(tac_valor)})", ln=True, align="L")
    if valor_prestamista > 0:
        pdf.cell(0, 7, f"Seguro Prestamista: {format_brl(valor_prestamista)}", ln=True)
    pdf.cell(0, 7, f"Total de Custos Iniciais: {format_brl(custos_operacionais_totais)}", ln=True)
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
    # Calcule a parcela média de forma segura
    if not df_evolucao.empty:
      parcela_mensal_credito_media = df_evolucao['Parcela Mensal Credito'].mean()
      parcela_mensal_liquida_media = (df_evolucao['Parcela Mensal Credito'] - df_evolucao['Rendimento Liquido Mensal da Aplicacao']).mean()
    else:
      parcela_mensal_credito_media = 0.0
      parcela_mensal_liquida_media = 0.0

    if usar_carencia:
        pdf.cell(0, 7, f"Parcela Mensal do Crédito (durante a carência): {format_brl(df_evolucao.loc[1, 'Juros Mensal Credito'])}", ln=True)
        pdf.cell(0, 7, f"Parcela Mensal do Crédito (após a carência): {format_brl(df_evolucao.loc[meses_carencia + 1, 'Parcela Mensal Credito'])}", ln=True)
    else:
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
        if cet_anual_liquido > 0:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 7, f"CET Líquido (com ganho da aplicação) Anual: {format_percent(cet_anual_liquido * 100)} a.a.", ln=True, align="L")
            pdf.cell(0, 7, f"CET Líquido (com ganho da aplicação) Mensal: {format_percent(cet_mensal_liquido * 100)} a.m.", ln=True, align="L")
        else:
            pdf.set_text_color(0, 100, 0)
            pdf.cell(0, 7, f"Ganho Líquido (com ganho da aplicação) Anual: {format_percent(abs(cet_anual_liquido) * 100)} a.a.", ln=True, align="L")
            pdf.cell(0, 7, f"Ganho Líquido (com ganho da aplicação) Mensal: {format_percent(abs(cet_mensal_liquido) * 100)} a.m.", ln=True, align="L")

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
    pdf.set_font("helvetica", "I", 10)
    # --- Seção 2: Tabela de Evolução com Quebra de Página ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Evolução Mensal da Operação", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho da tabela
    def draw_table_header():
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(220, 220, 220)
        # Largura das células ajustada
        pdf.cell(20, 10, "Mês", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Parcela Crédito (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Saldo Devedor (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Rendimento Aplic. (R$)", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Saldo Aplic. (R$)", 1, 1, 'C', 1)
    
    draw_table_header()
    
    pdf.set_font("helvetica", "", 8)
    for _, row in df_evolucao.iterrows():
        # Lógica de quebra de página: se não houver espaço suficiente para a próxima linha
        if pdf.get_y() > 250:
            pdf.add_page()
            draw_table_header()
            pdf.set_font("helvetica", "", 8)
        
        # Largura das células ajustada
        pdf.cell(20, 8, str(row['Mês']), 1, 0, 'C')
        pdf.cell(40, 8, format_brl(row['Parcela Mensal Credito']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Saldo Devedor Credito']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Rendimento Liquido Mensal da Aplicacao']), 1, 0, 'R')
        pdf.cell(40, 8, format_brl(row['Saldo Aplicacao Garantia']), 1, 1, 'R')
    
    return bytes(pdf.output(dest='S'))
    # --- FIM DO NOVO BLOCO ---
    
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
            "**Valor do Crédito (R$):**",
            min_value=1000.0,
            value=200000.0,
            step=1000.0,
            format="%.2f"
        )
    with col_prazo:
        prazo_credito_meses = st.slider(
            "**Prazo do Crédito (meses):**",
            min_value=1,
            max_value=60,
            value=60,
            step=1
        )

    col_taxa, col_tipo_taxa = st.columns(2)
    with col_taxa:
        taxa_juros_pactuada_input = st.number_input(
            "**Taxa de Juros Pactuada do Crédito (% ao mês):**",
            min_value=0.01,
            value=1.65,
            step=0.01,
            format="%.2f"
        )
        taxa_juros_pactuada_mensal = taxa_juros_pactuada_input / 100
    with col_tipo_taxa:
        st.write(" ") # Adiciona um espaço para alinhar os rádios
        tipo_taxa_credito = st.radio(
            "**Tipo de Taxa do Crédito:**",
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
# --- Opções de Carência (Novo Bloco) ---
st.markdown("---") # Linha divisória para separar visualmente
st.subheader("Opções de Carência")

usar_carencia = st.checkbox("Incluir período de carência na simulação?")

meses_carencia = 0 # Valor padrão para carência
if usar_carencia:
    meses_carencia = st.slider(
        "Selecione a quantidade de meses de carência:",
        min_value=6,
        max_value=12,
        value=6,
        step=1
    )
    st.info(f"Durante a carência de {meses_carencia} meses, o cliente pagará apenas os juros mensais. A amortização do saldo devedor começará após este período.")

# --- FIM DO NOVO BLOCO ---

# --- Expander para Custos Operacionais ---
with st.expander("**Custos Operacionais do Crédito (IOF e TAC)**"):
    col_iof, col_tac = st.columns(2)
    with col_iof:
        iof_percentual = st.number_input(
            "**IOF Total (% do valor do crédito):**",
            min_value=0.0,
            value=3.20,
            step=0.01,
            format="%.2f"
        )
    with col_tac:
        tac_percentual = st.number_input(
            "**TAC (% do valor do crédito):**",
            min_value=0.0,
            value=3.0,
            step=0.01,
            format="%.2f"
        )

# --- NOVO BLOCO: SEGURO PRESTAMISTA ---
# --- Container para Seguro Prestamista ---
st.header("Seguro Prestamista:")
with st.container(border=True):
    opcao_prestamista = st.radio(
        "**Incluir Seguro Prestamista?**",
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
            value=10.0,
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
# --- NOVO BLOCO: OPÇÃO DE CUSTOS FINANCIADOS OU DESCONTADOS ---
st.header("Forma de Pagamento dos Custos")
custos_financiados = st.radio(
    "**Os custos operacionais (IOF, TAC, etc.) serão:**",
    ("Financiados (somados ao saldo devedor)", "Descontados (abatidos do valor do crédito)"),
    index=0, # Padrão: financiados
    horizontal=False,
    help="Escolha se os custos iniciais da operação serão financiados no crédito ou descontados do valor total."
) == "Financiados (somados ao saldo devedor)"
# --- FIM DO NOVO BLOCO ---


# --- Container para Dados da Aplicação em Garantia ---
st.header("Detalhes da Aplicação (Garantia)")
# Checkbox para desabilitar a aplicação
simular_sem_aplicacao_financeira = st.checkbox("Simular sem aplicação financeira")

if not simular_sem_aplicacao_financeira:
    st.subheader("Entradas da Aplicação")
    valor_aplicacao = st.number_input(
        "Valor da Aplicação (R$)", min_value=0.0, value=200000.0, step=1000.0
    )
    taxa_rendimento_aplicacao_mensal = (
        st.number_input(
            "Taxa de Rendimento da Aplicação (% a.m.)",
            min_value=0.0,
            value=1.00,
            step=0.01,
            format="%.2f",
        )
        / 100
    )
    ir_aliquota = (
        st.number_input(
            "Alíquota de Imposto de Renda (% sobre o rendimento)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
        )
        / 100
    )
else:
    valor_aplicacao = 0.0
    taxa_rendimento_aplicacao_mensal = 0.0
    ir_aliquota = 0.0

st.divider() # Adiciona um divisor visual para separar as entradas do botão


# --- BOTÃO DE SIMULAÇÃO ---
if st.button("🚀 **Simular Operação**", key="btn_simular_nova_operacao", use_container_width=True):
    # Feedback visual durante o cálculo
    with st.spinner("Calculando a simulação..."):
        import time
        time.sleep(1)

    try:
        # --- INÍCIO: SEÇÃO DE CÁLCULOS DA OPERAÇÃO DE CRÉDITO E APLICAÇÃO ---

        # 1. CÁLCULOS INICIAIS
        iof_total = valor_credito * (iof_percentual / 100)
        tac_valor_calculado = valor_credito * (tac_percentual / 100)
        teto_tac = 10000.00
        tac_valor = min(tac_valor_calculado, teto_tac)
        custos_operacionais_totais = iof_total + tac_valor + valor_prestamista
        
        # Lógica condicional para definir o fluxo de caixa e saldos iniciais
        if custos_financiados:
            # Custos Financiados: Valor líquido recebido é o valor do crédito.
            # Saldo devedor inicial inclui os custos.
            valor_liquido_recebido = valor_credito
            saldo_devedor_inicial = valor_credito + custos_operacionais_totais
        else:
            # Custos Descontados: Valor líquido recebido é o valor do crédito menos os custos.
            # Saldo devedor inicial é o valor do crédito.
            valor_liquido_recebido = valor_credito - custos_operacionais_totais
            saldo_devedor_inicial = valor_credito

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
        
        df_evolucao.loc[0, "Saldo Devedor Credito"] = saldo_devedor_inicial
        df_evolucao.loc[0, "Saldo Aplicacao Garantia"] = valor_aplicacao
        
        saldo_devedor_atual = saldo_devedor_inicial

        # Se for taxa prefixada, a parcela é calculada uma única vez
        if tipo_taxa_credito == "Prefixada":
            parcela_fixa = npf.pmt(taxa_juros_pactuada_mensal, prazo_credito_meses, -saldo_devedor_inicial)
        else:
            parcela_fixa = 0.0

        for mes in range(1, prazo_credito_meses + 1):
            
            # ATUALIZAÇÃO DA TAXA DE JUROS SE FOR PÓS-FIXADA
            if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
                taxa_juros_mensal_efetiva = taxa_juros_pactuada_mensal + taxa_indexador_mensal
                juros_mensal_credito = saldo_devedor_atual * taxa_juros_mensal_efetiva
                saldo_devedor_corrigido = saldo_devedor_atual + juros_mensal_credito
                
                # Recalcula a parcela a cada mês com base no saldo devedor corrigido
                parcela_mensal_credito_real = npf.pmt(
                    taxa_juros_mensal_efetiva,
                    prazo_credito_meses - mes + 1,
                    -saldo_devedor_atual,
                )
                
                amortizacao_mensal = parcela_mensal_credito_real - juros_mensal_credito
                saldo_devedor_atual -= amortizacao_mensal

            else: # Prefixada
                juros_mensal_credito = saldo_devedor_atual * taxa_juros_pactuada_mensal
                parcela_mensal_credito_real = parcela_fixa
                amortizacao_mensal = parcela_mensal_credito_real - juros_mensal_credito
                saldo_devedor_atual -= amortizacao_mensal
            
            # Na carência, a parcela é apenas os juros do saldo devedor
            if usar_carencia and mes <= meses_carencia:
                juros_mensal_credito_carencia = df_evolucao.loc[mes - 1, "Saldo Devedor Credito"] * taxa_juros_pactuada_mensal
                parcela_mensal_credito_real = juros_mensal_credito_carencia
                amortizacao_mensal = 0.0
                
            # Now update the DataFrame with the calculated values
            df_evolucao.loc[mes, "Juros Mensal Credito"] = juros_mensal_credito
            df_evolucao.loc[mes, "Amortizacao Mensal"] = amortizacao_mensal
            df_evolucao.loc[mes, "Parcela Mensal Credito"] = parcela_mensal_credito_real
            df_evolucao.loc[mes, "Saldo Devedor Credito"] = saldo_devedor_atual
            
            # Calculation of the application remains the same
            saldo_aplicacao_garantia = df_evolucao.loc[mes - 1, "Saldo Aplicacao Garantia"]
            rendimento_bruto_mensal_aplicacao = saldo_aplicacao_garantia * taxa_rendimento_aplicacao_mensal
            ir_mensal_aplicacao = rendimento_bruto_mensal_aplicacao * ir_aliquota
            rendimento_liquido_mensal_aplicacao = rendimento_bruto_mensal_aplicacao - ir_mensal_aplicacao
            saldo_aplicacao_garantia += rendimento_liquido_mensal_aplicacao
            df_evolucao.loc[mes, "Saldo Aplicacao Garantia"] = saldo_aplicacao_garantia
            df_evolucao.loc[mes, "Rendimento Bruto Mensal da Aplicacao"] = rendimento_bruto_mensal_aplicacao
            df_evolucao.loc[mes, "IR Mensal da Aplicacao"] = ir_mensal_aplicacao
            df_evolucao.loc[mes, "Rendimento Liquido Mensal da Aplicacao"] = rendimento_liquido_mensal_aplicacao

        total_juros_pagos_credito = df_evolucao['Juros Mensal Credito'].sum()
        rendimento_liquido_total_aplicacao = df_evolucao['Rendimento Liquido Mensal da Aplicacao'].sum()
        ir_total_aplicacao = df_evolucao['IR Mensal da Aplicacao'].sum()
        capital_total_acumulado_aplicacao = df_evolucao.loc[prazo_credito_meses, "Saldo Aplicacao Garantia"]

        # 3. CÁLCULO DO GANHO LÍQUIDO E CET
        ganho_liquido_total_operacao = (capital_total_acumulado_aplicacao - valor_aplicacao) - (total_juros_pagos_credito + custos_operacionais_totais)
        
        # CÁLCULO DO CET BRUTO
        # O fluxo de caixa para o CET Bruto é o valor líquido recebido e as parcelas do crédito.
        cash_flows_bruto = [valor_liquido_recebido] + list(-df_evolucao['Parcela Mensal Credito'][1:])

        # Usar a função irr para encontrar a taxa efetiva do empréstimo
        try:
          cet_mensal_bruto = npf.irr(cash_flows_bruto)
          cet_anual_bruto = ((1 + cet_mensal_bruto) ** 12) - 1
        except:
          cet_mensal_bruto = 0.0
          cet_anual_bruto = 0.0
        
        # CÁLCULO DO CET LÍQUIDO (NOVA LÓGICA CORRIGIDA)
        # O fluxo de caixa para o CET Líquido é o valor do crédito (inflow)
        # e o fluxo líquido mensal (Parcela - Rendimento) (outflow).
        # A lógica é encontrar a taxa que iguala o valor recebido à soma dos
        # pagamentos líquidos futuros.
        cash_flows_liquido = [-valor_liquido_recebido]
        net_payments = df_evolucao['Parcela Mensal Credito'][1:] - df_evolucao['Rendimento Liquido Mensal da Aplicacao'][1:]
        cash_flows_liquido.extend(list(net_payments))

        try:
            cet_mensal_liquido = npf.irr(cash_flows_liquido)
            if isinstance(cet_mensal_liquido, (float, int)):
                cet_anual_liquido = ((1 + cet_mensal_liquido) ** 12) - 1
            else:
                cet_mensal_liquido = 0.0
                cet_anual_liquido = 0.0
        except Exception:
            cet_mensal_liquido = 0.0
            cet_anual_liquido = 0.0


        # --- FIM DOS CÁLCULOS ---
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
        # --- BOTÃO PARA GERAR O PDF ---
        with st.spinner("Gerando PDF..."):
            pdf_bytes = create_simulation_pdf(
                valor_credito, prazo_credito_meses, taxa_juros_pactuada_mensal,
                tipo_taxa_credito, taxa_indexador_mensal,
                valor_prestamista, iof_percentual, tac_percentual,
                valor_aplicacao, taxa_rendimento_aplicacao_mensal, ir_aliquota,
                df_evolucao, custos_operacionais_totais, rendimento_liquido_total_aplicacao,
                cet_anual_bruto, cet_mensal_bruto, cet_anual_liquido, cet_mensal_liquido,
                total_juros_pagos_credito, ir_total_aplicacao, capital_total_acumulado_aplicacao, ganho_liquido_total_operacao,
                usar_carencia, meses_carencia, valor_liquido_recebido, custos_financiados
            )
        
        st.download_button(
            label="Download PDF da Simulação",
            data=pdf_bytes,
            file_name="simulacao_completa.pdf",
            mime="application/pdf"
        )
            
    except Exception as e:
        st.error(f"Ocorreu um erro durante a simulação: {e}")
        st.warning("Por favor, verifique os dados inseridos e tente novamente.")