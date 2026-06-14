import io
from fpdf import FPDF


def generate_pdf_from_html(html_content: str) -> bytes:
    """Generate PDF from HTML string using fpdf2's write_html()."""
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(html_content)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


class ProposalPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Proposta de Locacao", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Proposta gerada pelo Agencies Copilot Closer — sujeita a aprovacao", align="C")


class ContractPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "CONTRATO DE LOCACAO RESIDENCIAL", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, "Minuta Preliminar — Gerada automaticamente pelo Agencies Copilot Closer", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Minuta preliminar — requer revisao humana antes de assinatura", align="C")


def _section(pdf: FPDF, title: str):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def _field(pdf: FPDF, label: str, value: str):
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 6, label + ":")
    pdf.set_font("Helvetica", "", 10)
    if value and value != "[PENDENTE]":
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(192, 57, 43)
        pdf.cell(0, 6, "[PENDENTE]", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)


def _paragraph(pdf: FPDF, text: str):
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)


def generate_proposal_pdf(ctx: dict) -> bytes:
    pdf = ProposalPDF()
    pdf.add_page()

    _section(pdf, "Locatario")
    _field(pdf, "Nome", ctx.get("lead_name", ""))
    _field(pdf, "Telefone", ctx.get("lead_phone", ""))
    if ctx.get("lead_email"):
        _field(pdf, "E-mail", ctx["lead_email"])
    pdf.ln(3)

    _section(pdf, "Imovel")
    _field(pdf, "Imovel", ctx.get("property_title", ""))
    _field(pdf, "Endereco", f"{ctx.get('property_address', '')}, {ctx.get('property_neighborhood', '')}, {ctx.get('property_city', '')}")
    pdf.ln(3)

    _section(pdf, "Condicoes Comerciais")
    rent = ctx.get("rent", 0)
    condo = ctx.get("condo_fee", 0)
    iptu = ctx.get("iptu", 0)
    _field(pdf, "Aluguel", f"R$ {rent:,.2f}")
    _field(pdf, "Condominio", f"R$ {condo:,.2f}")
    _field(pdf, "IPTU", f"R$ {iptu:,.2f}")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 6, "Total mensal:")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f"R$ {rent + condo + iptu:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _field(pdf, "Garantia", ctx.get("guarantee_type_label", ""))
    if ctx.get("deposit_months"):
        _field(pdf, "Caucao", f"{ctx['deposit_months']} meses (R$ {rent * ctx['deposit_months']:,.2f})")
    _field(pdf, "Entrada prevista", ctx.get("move_in_date", "[PENDENTE]"))
    _field(pdf, "Prazo", f"{ctx.get('contract_duration_months', '')} meses")
    pdf.ln(3)

    if ctx.get("special_conditions"):
        _section(pdf, "Condicoes Especiais")
        _paragraph(pdf, ctx["special_conditions"])

    pending = ctx.get("pending_documents", [])
    if pending:
        _section(pdf, "Documentos Pendentes")
        for doc in pending:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"  - {doc}", new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def generate_contract_pdf(ctx: dict) -> bytes:
    pdf = ContractPDF()
    pdf.add_page()

    # Warning
    pdf.set_fill_color(255, 243, 205)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "  Este documento e uma minuta preliminar. Requer revisao humana.", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    _section(pdf, "1. Partes")
    _field(pdf, "LOCADOR(A)", ctx.get("owner_name", "[PENDENTE]"))
    _field(pdf, "LOCATARIO(A)", ctx.get("lead_name", ""))
    _field(pdf, "CPF", ctx.get("lead_cpf") or "[PENDENTE]")
    _field(pdf, "RG", ctx.get("lead_rg") or "[PENDENTE]")
    _field(pdf, "Estado Civil", ctx.get("lead_marital_status") or "[PENDENTE]")
    _field(pdf, "Profissao", ctx.get("lead_occupation") or "[PENDENTE]")
    _field(pdf, "Telefone", ctx.get("lead_phone", ""))
    pdf.ln(3)

    _section(pdf, "2. Imovel")
    _field(pdf, "Endereco", ctx.get("property_address", ""))
    _field(pdf, "Bairro", ctx.get("property_neighborhood", ""))
    _field(pdf, "Cidade", ctx.get("property_city", ""))
    pdf.ln(3)

    _section(pdf, "3. Valores")
    rent = ctx.get("rent", 0)
    condo = ctx.get("condo_fee", 0)
    iptu = ctx.get("iptu", 0)
    _field(pdf, "Aluguel mensal", f"R$ {rent:,.2f}")
    _field(pdf, "Condominio", f"R$ {condo:,.2f}")
    _field(pdf, "IPTU", f"R$ {iptu:,.2f}")
    _field(pdf, "Total mensal", f"R$ {rent + condo + iptu:,.2f}")
    pdf.ln(3)

    _section(pdf, "4. Prazo e Inicio")
    _paragraph(pdf, f"O prazo da locacao sera de {ctx.get('contract_duration_months', '')} meses, com inicio em {ctx.get('move_in_date', '[PENDENTE]')}.")

    _section(pdf, "5. Garantia")
    guarantee_text = f"A modalidade de garantia escolhida e {ctx.get('guarantee_type_label', '')}."
    if ctx.get("deposit_months"):
        guarantee_text += f" Valor da caucao: {ctx['deposit_months']} meses de aluguel (R$ {rent * ctx['deposit_months']:,.2f})."
    _paragraph(pdf, guarantee_text)

    _section(pdf, "6. Obrigacoes do Locatario")
    obligations = [
        "6.1. Pagar pontualmente o aluguel e encargos ate o dia 5 de cada mes.",
        "6.2. Manter o imovel em bom estado de conservacao.",
        "6.3. Nao sublocar ou ceder o imovel sem autorizacao previa do locador.",
        "6.4. Comunicar ao locador qualquer dano ou necessidade de reparo.",
        "6.5. Restituir o imovel ao final da locacao nas mesmas condicoes.",
    ]
    for ob in obligations:
        _paragraph(pdf, ob)

    _section(pdf, "7. Obrigacoes do Locador")
    for ob in [
        "7.1. Entregar o imovel em condicoes de uso.",
        "7.2. Garantir o uso pacifico do imovel.",
        "7.3. Realizar reparos estruturais necessarios.",
    ]:
        _paragraph(pdf, ob)

    _section(pdf, "8. Rescisao")
    _paragraph(pdf, "Em caso de rescisao antecipada pelo Locatario, sera devida multa proporcional ao periodo restante, conforme Lei 8.245/91.")

    _section(pdf, "9. Foro")
    _paragraph(pdf, f"Fica eleito o foro da comarca de {ctx.get('property_city', '')} para dirimir quaisquer duvidas.")

    missing = ctx.get("missing_fields", [])
    if missing:
        pdf.ln(3)
        _section(pdf, "Campos Pendentes")
        for f in missing:
            pdf.set_text_color(192, 57, 43)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"  - {f}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

    # Signature lines
    pdf.ln(20)
    pdf.line(20, pdf.get_y(), 90, pdf.get_y())
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, ctx.get("owner_name", "LOCADOR(A)"), align="C")
    pdf.cell(95, 5, ctx.get("lead_name", "LOCATARIO(A)"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(95, 5, "LOCADOR(A)", align="C")
    pdf.cell(95, 5, "LOCATARIO(A)", align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
