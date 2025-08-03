import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
import base64
from fpdf import FPDF # <-- NOVA IMPORTAÇÃO AQUI!
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

# --- SUAS FUNÇÕES EXISTENTES ---
def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(value):
    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

# --- NOVA FUNÇÃO PARA GERAR O PDF ---
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
    # --- NOVO TRECHO A SER ADICIONADO AQUI ---
    # Adicionar a fonte DejaVuSans
    # O argumento 'fname' deve ser o caminho para o seu arquivo .ttf
    # O argumento 'set_alias' é opcional, mas útil para usar um nome mais simples (ex: 'DejaVu')
    pdf.add_font('DejaVuSans', '', 'DejaVuSans.ttf', uni=True)
    # --- FIM DO NOVO TRECHO ---
    # --- INÍCIO DO BLOCO DO CABEÇALHO (insira aqui) ---
    # Salva a posição Y inicial do cabeçalho
    y_start_header = pdf.get_y()

    # Define a fonte para o cabeçalho
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(50, 50, 150) # Um azul escuro para o título do cabeçalho

    # Título do Simulador
    pdf.cell(0, 10, "Simulador Financeiro Empresarial", ln=True, align="C")

    # Seu Nome / Autoria (opcional)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100) # Cor cinza para o subtítulo/autoria
    pdf.cell(0, 7, "Desenvolvido por: José Costa Neto/IA Google Gemini", ln=True, align="C") # Substitua por seu nome

    # Linha divisória para o cabeçalho
    pdf.ln(5) # Pequeno espaço antes da linha
    pdf.set_draw_color(150, 150, 150) # Cor cinza para a linha
    pdf.set_line_width(0.4) # Espessura um pouco maior para a linha do cabeçalho
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10) # Espaço após a linha para o conteúdo principal começar

    # Voltar para as configurações de texto padrão
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0) # Preto
    # --- FIM DO BLOCO DO CABEÇALHO ---
    pdf.set_font("helvetica", "B", 16)
    
    # Título
    pdf.cell(0, 10, "Resumo da Simulação Financeira", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Data da Simulação: {pd.to_datetime('today').strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(10)

    # Seção Crédito
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detalhes do Crédito", ln=True)
    # Adiciona uma linha divisória
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2) # Pequeno espaço após a linha
    # --- INÍCIO DO NOVO BLOCO para o retângulo ---
    # Salva a posição Y antes de imprimir o conteúdo da seção
    y_start_credito = pdf.get_y()

    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"Valor do Crédito: {format_brl(valor_credito)}", ln=True)
    pdf.cell(0, 7, f"Prazo: {prazo_credito_meses} meses", ln=True)
    pdf.cell(0, 7, f"Taxa de Juros Pactuada: {format_percent(taxa_juros_pactuada_mensal * 100)} a.m.", ln=True)
    pdf.cell(0, 7, f"Tipo de Taxa: {tipo_taxa_credito}", ln=True)
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
        pdf.cell(0, 7, f"Taxa do Indexador Mensal: {format_percent(taxa_indexador_mensal * 100)} a.m.", ln=True)

    # --- NOVO TRECHO COM LÓGICA CONDICIONAL PARA O VALOR LÍQUIDO RECEBIDO ---
    valor_liquido_recebido_final = valor_credito # Valor padrão, para Prefixada

    # Se a taxa for pós-fixada, os custos são descontados do valor do crédito para o valor líquido recebido
    # Caso contrário (Prefixada), os custos são financiados e o valor líquido recebido é o próprio valor do crédito
    if tipo_taxa_credito == "Pós-fixada (TR + Taxa)": # Ajuste a string conforme o nome exato no seu código
        valor_liquido_recebido_final = valor_credito - custos_operacionais_totais

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, f"Valor Líquido Recebido pelo Cliente: {format_brl(valor_liquido_recebido_final)}", ln=True, align="L")
    pdf.set_font("helvetica", "", 12)
    # --- FIM DO NOVO TRECHO ---

    
    # Salva a posição Y após imprimir todo o conteúdo da seção
    y_end_credito = pdf.get_y()

    # Desenha o retângulo ao redor da seção "Detalhes do Crédito"
    pdf.set_draw_color(200, 200, 200) # Cor cinza claro para a borda (RGB)
    pdf.set_line_width(0.2) # Espessura da linha (em mm)
    # pdf.rect(x, y, w, h)
    # x: Posição horizontal de início (margem esquerda)
    # y: Posição vertical de início (y_start_credito - um pequeno padding)
    # w: Largura do retângulo (largura da área de conteúdo)
    # h: Altura do retângulo (y_end_credito - y_start_credito + um pequeno padding)
    pdf.rect(pdf.l_margin, y_start_credito - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_credito - y_start_credito + 4)
    pdf.ln(5) # Espaço no final da seção
    # --- FIM DO NOVO BLOCO para o retângulo ---
    
    # Seção Custos Operacionais
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Custos Iniciais da Operação", ln=True)
    # Adiciona uma linha divisória
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2) # Pequeno espaço após a linha
    # --- INÍCIO DO NOVO BLOCO para o retângulo ---
    y_start_custos = pdf.get_y() # Salva a posição Y antes de imprimir o conteúdo da seção

    pdf.set_font("helvetica", "", 12)
    if iof_percentual > 0:
        pdf.cell(0, 7, f"IOF: {format_percent(iof_percentual)} ({format_brl(iof_total)})", ln=True, align="L")
    if tac_percentual > 0:
        pdf.cell(0, 7, f"TAC: {format_percent(tac_percentual)} ({format_brl(tac_valor)})", ln=True, align="L")
    if valor_prestamista > 0:
        pdf.cell(0, 7, f"Seguro Prestamista: {format_brl(valor_prestamista)}", ln=True)

    pdf.cell(0, 7, f"Total de Custos Iniciais: {format_brl(custos_operacionais_totais)}", ln=True)

    y_end_custos = pdf.get_y() # Salva a posição Y após imprimir todo o conteúdo da seção

    pdf.set_draw_color(200, 200, 200) # Cor cinza claro para a borda
    pdf.set_line_width(0.2) # Espessura da linha
    pdf.rect(pdf.l_margin, y_start_custos - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_custos - y_start_custos + 4)
    pdf.ln(5) # Espaço no final da seção
    # --- FIM DO NOVO BLOCO para o retângulo ---
    
    # Seção Aplicação
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detalhes da Aplicação", ln=True)
    # Adiciona uma linha divisória
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2) # Pequeno espaço após a linha
    # --- INÍCIO DO NOVO BLOCO para o retângulo ---
    y_start_aplicacao = pdf.get_y() # Salva a posição Y antes de imprimir o conteúdo da seção

    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"Valor da Aplicação: {format_brl(valor_aplicacao)}", ln=True)
    pdf.cell(0, 7, f"Taxa de Rendimento: {format_percent(taxa_rendimento_aplicacao_mensal * 100)} a.m.", ln=True)
    pdf.cell(0, 7, f"Alíquota de Imposto de Renda: {format_percent(ir_aliquota * 100)}", ln=True)
    pdf.cell(0, 7, f"Rendimento Líquido Total da Aplicação: {format_brl(rendimento_liquido_total_aplicacao)}", ln=True)

    y_end_aplicacao = pdf.get_y() # Salva a posição Y após imprimir todo o conteúdo da seção

    pdf.set_draw_color(200, 200, 200) # Cor cinza claro para a borda
    pdf.set_line_width(0.2) # Espessura da linha
    pdf.rect(pdf.l_margin, y_start_aplicacao - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_aplicacao - y_start_aplicacao + 4)
    pdf.ln(5) # Espaço no final da seção
    # --- FIM DO NOVO BLOCO para o retângulo ---

       
    # Seção Resumo Financeiro
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Resumo Financeiro Detalhado", ln=True)
    # Adiciona uma linha divisória
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2) # Pequeno espaço após a linha
    # --- INÍCIO DO NOVO BLOCO para o retângulo ---
    y_start_resumo = pdf.get_y() # Salva a posição Y antes de imprimir o conteúdo da seção

    pdf.set_font("helvetica", "", 12)
    # Adicionando as informações da parcela
    parcela_mensal_credito_media = df_evolucao['Parcela Mensal Credito'].mean()
    parcela_mensal_liquida_media = (df_evolucao['Parcela Mensal Credito'] - df_evolucao['Rendimento Liquido Mensal da Aplicacao']).mean()

    pdf.cell(0, 7, f"Parcela Mensal do Crédito: {format_brl(parcela_mensal_credito_media)}", ln=True)
    pdf.cell(0, 7, f"Parcela Mensal do Crédito (com desconto da Aplicação): {format_brl(parcela_mensal_liquida_media)}", ln=True)

    pdf.cell(0, 7, f"Juros Totais Pagos no Crédito: {format_brl(total_juros_pagos_credito)}", ln=True)
    pdf.cell(0, 7, f"Imposto de Renda Retido na Aplicação: {format_brl(ir_total_aplicacao)}", ln=True)

    # Destaque para Capital Total Acumulado
    pdf.set_font("helvetica", "B", 12) # Negrito
    pdf.cell(0, 7, f"Capital Total Acumulado ao Final do Contrato: {format_brl(capital_total_acumulado_aplicacao)}", ln=True)
    pdf.set_font("helvetica", "", 12) # Voltar para a fonte normal

    # Destaque para Ganho Líquido Total da Operação
    pdf.set_font("helvetica", "B", 12) # Negrito
    if ganho_liquido_total_operacao >= 0:
        pdf.set_text_color(0, 0, 200) # Azul (pode ser 0, 0, 255 para um azul mais vivo, ou 0, 0, 150 para mais escuro)
        pdf.cell(0, 7, f"Ganho Líquido Total da Operação: {format_brl(ganho_liquido_total_operacao)}", ln=True)
    else:
        pdf.set_text_color(200, 0, 0) # Vermelho
        pdf.cell(0, 7, f"Custo Líquido Total da Operação: {format_brl(abs(ganho_liquido_total_operacao))}", ln=True) # Mostrar como custo, com valor absoluto
    pdf.set_text_color(0, 0, 0) # Voltar para preto após o destaque
    pdf.set_font("helvetica", "", 12) # Voltar para a fonte normal

    y_end_resumo = pdf.get_y() # Salva a posição Y após imprimir todo o conteúdo da seção

    pdf.set_draw_color(200, 200, 200) # Cor cinza claro para a borda
    pdf.set_line_width(0.2) # Espessura da linha
    pdf.rect(pdf.l_margin, y_start_resumo - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_resumo - y_start_resumo + 4)
    pdf.ln(5) # Espaço no final da seção
    # --- FIM DO NOVO BLOCO para o retângulo ---
    
    # Seção Custo Efetivo Total (CET)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Custo Efetivo Total (CET)", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)

    # --- INÍCIO DO BLOCO para o retângulo ---
    y_start_cet = pdf.get_y() # Salva a posição Y antes de imprimir o conteúdo da seção

    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 7, f"CET Bruto Anual: {format_percent(cet_anual_bruto * 100)} a.a.", ln=True, align="L")
    pdf.cell(0, 7, f"CET Bruto Mensal: {format_percent(cet_mensal_bruto * 100)} a.m.", ln=True, align="L")

    # Destaque para CET Líquido
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

    pdf.ln(3) # Pequeno espaço antes do breakdown

    # --- NOVO LOCAL PARA O TRECHO: BREAKDOWN DO CET (AGORA DENTRO DO RETÂNGULO) ---
    pdf.set_font("helvetica", "B", 10) # Negrito e fonte menor para o título da explicação
    # Usar multi_cell com x e w definidos para alinhar ao conteúdo
    current_x = pdf.l_margin + 5 # Ajuste o 5mm para o padding desejado
    cell_width = pdf.w - pdf.l_margin - pdf.r_margin - 10 # Largura total - margens - 2x padding

    pdf.set_x(current_x)
    pdf.cell(cell_width, 7, "O CET inclui:", ln=True, align="L")

    pdf.set_font("DejaVuSans", "", 10) # Manter DejaVuSans para os bullets
    pdf.set_x(current_x) # Define X novamente para a lista
    pdf.multi_cell(cell_width, 6, "• Juros (taxa de juros do crédito) \n• Tarifas (como a TAC - Tarifa de Abertura de Crédito) \n• Impostos (como o IOF - Imposto sobre Operações Financeiras) \n• Seguros (como o Seguro Prestamista, se aplicável) \n• Outras despesas cobradas na operação", align="L")

    # --- FIM DO NOVO TRECHO ---

    y_end_cet = pdf.get_y() # Salva a posição Y APÓS IMPRIMIR TUDO, incluindo o breakdown

    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    # O retângulo agora engloba tudo, do y_start_cet até o novo y_end_cet
    pdf.rect(pdf.l_margin, y_start_cet - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_cet - y_start_cet + 4)
    pdf.ln(10) # Espaço no final da seção CET
    # --- FIM DO BLOCO para o retângulo ---
    
    # --- INÍCIO DA NOVA SEÇÃO: Observações Importantes ---
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Observações Importantes", ln=True)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.w - pdf.r_margin - pdf.l_margin, pdf.get_y())
    pdf.ln(2)

    # Início do bloco para o retângulo desta seção
    y_start_observacoes = pdf.get_y()

    pdf.set_font("helvetica", "", 10) # Fonte um pouco menor para notas, se desejar
    pdf.multi_cell(0, 6, "1. A simulação de crédito utiliza o sistema de amortização Tabela Price.  \n2. Os cálculos de juros e rendimentos são baseados no regime de juros compostos.  \n3. O Imposto de Renda (IR) incide apenas sobre o rendimento bruto da aplicação, conforme alíquota informada.  \n4. Para taxas pós-fixadas, a Taxa Referencial (TR) ou outro indexador pode influenciar os valores das parcelas e rendimentos da aplicação.  \n5. Os valores apresentados são estimativas e podem variar conforme as condições de mercado e políticas da instituição financeira. ", align="L")

    y_end_observacoes = pdf.get_y()

    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.rect(pdf.l_margin, y_start_observacoes - 2, pdf.w - pdf.l_margin - pdf.r_margin, y_end_observacoes - y_start_observacoes + 4)
    pdf.ln(5)
    # --- FIM DA NOVA SEÇÃO ---
    
    pdf.set_font("helvetica", "I", 10)
    #pdf.cell(0, 5, "Simulador financeiro desenvolvido com Streamlit e Python", ln=True, align="R")

    return bytes(pdf.output(dest='S')) # Converte o bytearray/bytes para bytes

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
            value=100000.0,
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
            value=0.8,
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

# ... o restante do seu código para IOF e TAC segue aqui ...

# --- Expander para Custos Operacionais ---
with st.expander("**Custos Operacionais do Crédito (IOF e TAC)**"):
    col_iof, col_tac = st.columns(2)
    with col_iof:
        iof_percentual = st.number_input(
            "**IOF Total (% do valor do crédito):**",
            min_value=0.0,
            value=0.38,
            step=0.01,
            format="%.2f"
        )
    with col_tac:
        tac_percentual = st.number_input(
            "**TAC (% do valor do crédito):**",
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
            "**Valor da Aplicação em Garantia (R$):**",
            min_value=1000.0,
            value=50000.0,
            step=1000.0,
            format="%.2f"
        )
    with col_aplicacao_taxa:
        taxa_rendimento_aplicacao_input = st.number_input(
            "**Taxa de Rendimento da Aplicação (% ao mês):**",
            min_value=0.01,
            max_value=2.0,
            value=0.8,
            step=0.01,
            format="%.2f"
        )
        taxa_rendimento_aplicacao_mensal = taxa_rendimento_aplicacao_input / 100

    ir_aliquota = st.slider(
        "**Alíquota de Imposto de Renda sobre Rendimento da Aplicação (%):**",
        min_value=0.0,
        max_value=22.5,
        value=15.0,
        step=0.5,
        format="%.1f",
        help="**Alíquota de IR para o cálculo do rendimento líquido da aplicação.**"
    ) / 100

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

        # 2. LÓGICA DO SEGURO PRESTAMISTA E OUTROS CUSTOS (IOF, TAC, Prestamista)
        valor_total_para_parcela_calculo = valor_credito
        valor_liquido_recebido = valor_credito
        custos_operacionais_totais = iof_total + tac_valor + valor_prestamista

        if tipo_taxa_credito == "Prefixada":
            valor_total_para_parcela_calculo += custos_operacionais_totais
        else:
            valor_liquido_recebido -= custos_operacionais_totais

        # 3. CÁLCULO DA TAXA DE JUROS EFETIVA DO CRÉDITO
        if tipo_taxa_credito == "Pós-fixada (TR + Taxa)":
            taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal + taxa_indexador_mensal
        else:
            taxa_juros_credito_efetiva_mensal = taxa_juros_pactuada_mensal

        # 4. CÁLCULO DA PARCELA MENSAL E JUROS TOTAIS (BASE TABLE PRICE)
        parcela_mensal_credito = 0.0
        total_juros_pagos_credito = 0.0
        juros_pagos_na_carencia = 0.0

        if prazo_credito_meses > 0:
            if usar_carencia and meses_carencia > 0:
                # Lógica para Simulação com Carência (Juros Pagos)
                juros_pagos_na_carencia = valor_total_para_parcela_calculo * taxa_juros_credito_efetiva_mensal * meses_carencia
                prazo_amortizacao = prazo_credito_meses - meses_carencia
                
                if prazo_amortizacao > 0:
                    parcela_mensal_credito = npf.pmt(
                        taxa_juros_credito_efetiva_mensal,
                        prazo_amortizacao,
                        -valor_total_para_parcela_calculo
                    )
                    juros_fase_amortizacao = (parcela_mensal_credito * prazo_amortizacao) - valor_total_para_parcela_calculo
                    total_juros_pagos_credito = juros_pagos_na_carencia + juros_fase_amortizacao
                else:
                    parcela_mensal_credito = juros_pagos_na_carencia / meses_carencia
                    total_juros_pagos_credito = juros_pagos_na_carencia
            else:
                # Lógica de cálculo da Tabela Price sem carência (SEU CÓDIGO ORIGINAL)
                parcela_mensal_credito = npf.pmt(
                    taxa_juros_credito_efetiva_mensal,
                    prazo_credito_meses,
                    -valor_total_para_parcela_calculo
                )
                total_juros_pagos_credito = (parcela_mensal_credito * prazo_credito_meses) - valor_total_para_parcela_calculo

        # 5. CÁLCULOS DA APLICAÇÃO (sempre fora do if da carência)
        rendimento_bruto_total_aplicacao = valor_aplicacao * ((1 + taxa_rendimento_aplicacao_mensal)**prazo_credito_meses - 1)
        ir_total_aplicacao = rendimento_bruto_total_aplicacao * ir_aliquota
        rendimento_liquido_total_aplicacao = rendimento_bruto_total_aplicacao - ir_total_aplicacao
        capital_total_acumulado_aplicacao = valor_aplicacao + rendimento_liquido_total_aplicacao

        # 6. CÁLCULO DO GANHO LÍQUIDO TOTAL
        ganho_liquido_total_operacao = rendimento_liquido_total_aplicacao - total_juros_pagos_credito

        # 7. GERAÇÃO DOS DADOS MENSAIS PARA OS GRÁFICOS
        historico = []
        saldo_atual_credito = valor_total_para_parcela_calculo
        saldo_atual_aplicacao = valor_aplicacao

        for mes_idx in range(1, prazo_credito_meses + 1):
            # Lógica para carência
            if usar_carencia and mes_idx <= meses_carencia:
                juros_mes_credito = saldo_atual_credito * taxa_juros_credito_efetiva_mensal
                amortizacao_mes = 0 # Sem amortização na carência
                parcela_mensal_credito_real = juros_mes_credito # A parcela é só o juros
            else:
                juros_mes_credito = saldo_atual_credito * taxa_juros_credito_efetiva_mensal
                amortizacao_mes = parcela_mensal_credito - juros_mes_credito
                parcela_mensal_credito_real = parcela_mensal_credito # A parcela é a fixa
            
            saldo_atual_credito = max(0, saldo_atual_credito - amortizacao_mes)

            # Aplicação
            rendimento_mes_bruto = saldo_atual_aplicacao * taxa_rendimento_aplicacao_mensal
            rendimento_liquido_mensal_aplicacao = rendimento_mes_bruto * (1 - ir_aliquota)
            saldo_atual_aplicacao += rendimento_mes_bruto

            historico.append({
                'Mês': mes_idx,
                'Saldo Devedor Credito': saldo_atual_credito,
                'Parcela Mensal Credito': parcela_mensal_credito_real, # Use a parcela real do mês
                'Rendimento Liquido Mensal da Aplicacao': rendimento_liquido_mensal_aplicacao,
                'Saldo Aplicacao Garantia': saldo_atual_aplicacao
            })

        df_evolucao = pd.DataFrame(historico)
        df_fluxo_mensal = df_evolucao.copy()

        # 8. CÁLCULO DO CET (Custo Efetivo Total)
        # Fluxo de Caixa para CET Bruto
        fluxo_bruto = [valor_credito - custos_operacionais_totais]
        fluxo_bruto.extend([-p for p in df_evolucao["Parcela Mensal Credito"].tolist()])
        try:
            cet_mensal_bruto = npf.irr(fluxo_bruto)
            if isinstance(cet_mensal_bruto, (int, float)) and cet_mensal_bruto > -1:
                cet_anual_bruto = (1 + cet_mensal_bruto)**12 - 1
            else:
                cet_mensal_bruto, cet_anual_bruto = 0.0, 0.0
        except ValueError:
            cet_mensal_bruto, cet_anual_bruto = 0.0, 0.0

        # Fluxo de Caixa para CET Líquido
        fluxo_liquido = [valor_credito - custos_operacionais_totais]
        for i in range(prazo_credito_meses):
            fluxo_liquido.append(-(df_evolucao.loc[i, "Parcela Mensal Credito"] - df_evolucao.loc[i, "Rendimento Liquido Mensal da Aplicacao"]))
        try:
            cet_mensal_liquido = npf.irr(fluxo_liquido)
            if isinstance(cet_mensal_liquido, (int, float)) and cet_mensal_liquido > -1:
                cet_anual_liquido = (1 + cet_mensal_liquido)**12 - 1
            else:
                cet_mensal_liquido, cet_anual_liquido = 0.0, 0.0
        except ValueError:
            cet_mensal_liquido, cet_anual_liquido = 0.0, 0.0

        # --- FIM: SEÇÃO DE CÁLCULOS ---

        # --- INÍCIO: SEÇÃO DE EXIBIÇÃO DOS RESULTADOS ---
        st.header("Resultados da Simulação:")
        
        st.subheader("Resumo Financeiro da Operação:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Valor Líquido Recebido", format_brl(valor_liquido_recebido))
            st.metric("Parcela Mensal do Crédito", format_brl(df_evolucao['Parcela Mensal Credito'].mean()))
            st.metric("Total de Juros Pagos no Crédito", format_brl(total_juros_pagos_credito))
        with col2:
            st.metric("Rendimento Bruto Total da Aplicação", format_brl(rendimento_bruto_total_aplicacao))
            st.metric("Imposto de Renda Retido", format_brl(ir_total_aplicacao))
            st.metric("Rendimento Líquido Total", format_brl(rendimento_liquido_total_aplicacao))
        with col3:
            st.metric("Ganho Líquido Total da Operação", format_brl(ganho_liquido_total_operacao))
        
        st.subheader("Detalhes da Operação:")
        st.write(f"- **Valor do Crédito Liberado:** {format_brl(valor_credito)}")
        if iof_total > 0:
            st.write(f"- **Imposto sobre Operações Financeiras (IOF):** {format_brl(iof_total)}")
        if tac_valor > 0:
            st.write(f"- **Tarifa de Abertura de Crédito (TAC):** {format_brl(tac_valor)}")
        if valor_prestamista > 0:
            st.write(f"- **Seguro Prestamista:** {format_brl(valor_prestamista)}")

        st.write(f"- **Parcela Mensal do Crédito (média):** {format_brl(df_evolucao['Parcela Mensal Credito'].mean())}")
        st.write(f"- **Parcela Mensal do Crédito (com desconto da Aplicação):** **{format_brl((df_evolucao['Parcela Mensal Credito'] - df_evolucao['Rendimento Liquido Mensal da Aplicacao']).mean())}**")
        st.write(f"- **Juros Totais Pagos no Crédito:** {format_brl(total_juros_pagos_credito)}")
        st.write(f"- **Rendimento Bruto Total da Aplicação:** {format_brl(rendimento_bruto_total_aplicacao)}")
        st.write(f"- **Imposto de Renda Retido na Aplicação:** {format_brl(ir_total_aplicacao)}")
        st.write(f"- **Rendimento Líquido Total da Aplicação:** {format_brl(rendimento_liquido_total_aplicacao)}")
        st.write(f"- **Capital Total Acumulado ao Final do Contrato:** **{format_brl(capital_total_acumulado_aplicacao)}**")
        st.write(f"- **Ganho Líquido Total da Operação (Rendimento Líquido - Juros Pagos):** **{format_brl(ganho_liquido_total_operacao)}**")

        st.markdown("---")
        st.subheader("Custo Efetivo Total (CET):")
        if cet_anual_bruto != 0.0:
            st.write(f"**Custo Efetivo Total (CET) Bruto Anual:** {format_percent(cet_anual_bruto * 100)} a.a.")
            st.write(f"**Custo Efetivo Total (CET) Bruto Mensal:** {format_percent(cet_mensal_bruto * 100)} a.m.")
        else:
            st.warning("Não foi possível calcular o CET Bruto. Verifique os valores de entrada ou o fluxo de caixa.")
        if cet_anual_liquido != 0.0:
            st.write(f"**Custo Efetivo Total (CET) Líquido (com ganho da aplicação) Anual:** {format_percent(cet_anual_liquido * 100)} a.a.")
            st.write(f"**Custo Efetivo Total (CET) Líquido (com ganho da aplicação) Mensal:** {format_percent(cet_mensal_liquido * 100)} a.m.")
        else:
            st.warning("Não foi possível calcular o CET Líquido. Verifique os valores de entrada ou o fluxo de caixa.")
        st.markdown("---")

        if ganho_liquido_total_operacao >= 0:
            st.success("🎉 Esta operação de crédito, considerando o rendimento da sua aplicação, resulta em um **ganho líquido total** para você!")
            st.info(f"""
                💡 Você não apenas cobriu os juros e custos do crédito com sua aplicação, como também obteve um **ganho de {format_brl(ganho_liquido_total_operacao)}**!
                Isso demonstra a **vantagem de usar sua aplicação como garantia** para otimizar seus custos de crédito ao máximo.
                """)
        else:
            st.warning("⚠️ Esta operação de crédito, mesmo com o rendimento da sua aplicação, resulta em um **custo líquido total**.")
            st.info("O rendimento gerado pela sua aplicação foi crucial! Ele cobriu parte dos juros do seu crédito, resultando em uma redução significativa no valor final que você pagou.")

        st.subheader("📊 Evolução Financeira ao Longo do Contrato")
        if not df_evolucao.empty:
            fig_saldo = px.line(df_evolucao, x="Mês", y=["Saldo Devedor Credito", "Saldo Aplicacao Garantia"],
                                title='Evolução do Saldo Devedor do Crédito vs. Saldo da Aplicação em Garantia',
                                labels={"value": "Valor (R$)", "variable": "Ativo"},
                                line_shape="spline",
                                height=400)
            fig_saldo.update_layout(hovermode="x unified", legend_title_text='Tipo')
            fig_saldo.update_xaxes(showgrid=True, zeroline=True)
            fig_saldo.update_yaxes(showgrid=True, zeroline=True)
            st.plotly_chart(fig_saldo, use_container_width=True)

            fig_fluxo = px.bar(df_fluxo_mensal, x='Mês', y=['Parcela Mensal Credito', 'Rendimento Liquido Mensal da Aplicacao'],
                                title='Parcela Mensal do Crédito vs. Rendimento Líquido Mensal da Aplicação',
                                labels={"value": "Valor (R$)", "variable": "Tipo de Fluxo"},
                                barmode='group',
                                height=400,
                                color_discrete_map={'Parcela Mensal Credito': 'red', 'Rendimento Liquido Mensal da Aplicacao': 'green'}
                            )
            fig_fluxo.update_layout(hovermode="x unified", legend_title_text='Fluxo')
            fig_fluxo.update_xaxes(showgrid=True, zeroline=True)
            fig_fluxo.update_yaxes(showgrid=True, zeroline=True)
            st.plotly_chart(fig_fluxo, use_container_width=True)

            st.markdown("---")
            st.subheader("Opções de Exportação:")
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
                label="⬇️ Baixar Resumo em PDF",
                data=pdf_bytes,
                file_name="resumo_simulacao_credito.pdf",
                mime="application/pdf",
                help="Clique para baixar um resumo completo da simulação em formato PDF."
            )

    except Exception as e:
        # CORREÇÃO AQUI: as linhas abaixo DEVEM ser indentadas
        st.error(f"Ocorreu um erro durante a simulação: {e}")
        st.warning("Por favor, verifique os dados inseridos e tente novamente.")

# --- FIM DO BOTÃO ---
        # ... (Seu código existente de exibição de resultados, gráficos, etc.) ...

                
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
            