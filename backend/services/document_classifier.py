from models import DocumentType


def classify_attachment(file_name: str) -> DocumentType | None:
    """Classify an attachment by its filename."""
    name = file_name.lower()

    if "cnh" in name or "rg" in name or "identidade" in name:
        return DocumentType.rg_cnh
    if "cpf" in name:
        return DocumentType.cpf
    if "holerite" in name or "renda" in name or "contracheque" in name:
        return DocumentType.comprovante_renda
    if "residencia" in name or "endereco" in name or "comprovante_end" in name:
        return DocumentType.comprovante_residencia
    if "casamento" in name or "civil" in name or "certidao" in name:
        return DocumentType.estado_civil
    if "caucao" in name or "pagamento" in name or "deposito" in name:
        return DocumentType.comprovante_caucao

    return None
