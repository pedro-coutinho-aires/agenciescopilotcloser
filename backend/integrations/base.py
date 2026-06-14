"""Base interface for digital signature integrations."""

from abc import ABC, abstractmethod
from pydantic import BaseModel


class SignerInfo(BaseModel):
    name: str
    email: str
    phone: str = ""
    document_cpf: str = ""


class SignatureRequest(BaseModel):
    document_name: str
    document_pdf: bytes  # PDF content
    signers: list[SignerInfo]
    message: str = ""


class SignatureResponse(BaseModel):
    success: bool
    provider: str
    document_id: str = ""
    signing_url: str = ""
    status: str = ""
    error: str = ""


class SignatureProvider(ABC):
    """Abstract base for signature providers."""

    @abstractmethod
    def upload_and_send(self, request: SignatureRequest) -> SignatureResponse:
        """Upload document and send for signature."""
        ...

    @abstractmethod
    def check_status(self, document_id: str) -> SignatureResponse:
        """Check signing status."""
        ...
