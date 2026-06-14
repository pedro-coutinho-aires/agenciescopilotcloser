from models import (
    Lead, Property, ChatMessage, Attachment, DealDocument,
    DocumentType, DocumentStatus,
)

mock_lead = Lead(
    id="lead_001",
    name="João Silva",
    phone="+55 11 99999-9999",
    email="joao@email.com",
    interest_type="locacao",
    income_range="R$ 8.000 - R$ 10.000",
    desired_move_in_date="2026-07-10",
    marital_status="Solteiro",
    occupation="Analista de Produto",
)

mock_property = Property(
    id="property_001",
    title="Apartamento 2 quartos na Vila Madalena",
    address="Rua Harmonia, 123",
    neighborhood="Vila Madalena",
    city="São Paulo",
    rent=2700,
    condo_fee=520,
    iptu=110,
    bedrooms=2,
    parking_spots=1,
    accepts_pet=True,
    status="available",
    owner_name="Maria Fernanda",
)

mock_messages: list[ChatMessage] = [
    ChatMessage(
        id="msg_001",
        sender="broker",
        text="Oi João! O que achou da visita?",
        created_at="2026-06-14T14:00:00Z",
    ),
    ChatMessage(
        id="msg_002",
        sender="lead",
        text="Adorei! Acredito que, após ela, eu vá fechar com vocês mesmo.",
        created_at="2026-06-14T14:01:00Z",
    ),
]

document_templates = {
    "locacao_pf_caucao": {
        "id": "locacao_pf_caucao",
        "name": "Locação PF com caução",
        "documents": [
            DealDocument(id="doc_rg_cnh", label="RG ou CNH", type=DocumentType.rg_cnh),
            DealDocument(id="doc_cpf", label="CPF", type=DocumentType.cpf),
            DealDocument(id="doc_income", label="Comprovante de renda", type=DocumentType.comprovante_renda),
            DealDocument(id="doc_address", label="Comprovante de residência", type=DocumentType.comprovante_residencia),
            DealDocument(id="doc_marital", label="Estado civil", type=DocumentType.estado_civil),
            DealDocument(id="doc_deposit", label="Comprovante de pagamento da caução", type=DocumentType.comprovante_caucao),
        ],
    },
    "locacao_pf_fiador": {
        "id": "locacao_pf_fiador",
        "name": "Locação PF com fiador",
        "documents": [
            DealDocument(id="doc_rg_cnh", label="RG ou CNH", type=DocumentType.rg_cnh),
            DealDocument(id="doc_cpf", label="CPF", type=DocumentType.cpf),
            DealDocument(id="doc_income", label="Comprovante de renda", type=DocumentType.comprovante_renda),
            DealDocument(id="doc_address", label="Comprovante de residência", type=DocumentType.comprovante_residencia),
            DealDocument(id="doc_marital", label="Estado civil", type=DocumentType.estado_civil),
        ],
    },
}
