from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Column,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Junction table: chat_message <-> attachment
# ---------------------------------------------------------------------------

chat_message_attachment = Table(
    "chat_message_attachment",
    Base.metadata,
    Column(
        "chat_message_id",
        UUID(as_uuid=False),
        ForeignKey("chat_message.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "attachment_id",
        UUID(as_uuid=False),
        ForeignKey("attachment.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ---------------------------------------------------------------------------
# AgencyORM
# ---------------------------------------------------------------------------

class AgencyORM(TimestampMixin, Base):
    __tablename__ = "agency"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    leads: Mapped[list[LeadORM]] = relationship("LeadORM", back_populates="agency")
    properties: Mapped[list[PropertyORM]] = relationship(
        "PropertyORM", back_populates="agency"
    )
    document_templates: Mapped[list[DocumentTemplateORM]] = relationship(
        "DocumentTemplateORM", back_populates="agency"
    )
    deals: Mapped[list[DealORM]] = relationship("DealORM", back_populates="agency")


# ---------------------------------------------------------------------------
# LeadORM
# ---------------------------------------------------------------------------

class LeadORM(TimestampMixin, Base):
    __tablename__ = "lead"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agency.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interest_type: Mapped[str] = mapped_column(
        String, nullable=False, default="locacao"
    )
    income_range: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    desired_move_in_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rg: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address_extracted: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    income_extracted: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    agency: Mapped[AgencyORM] = relationship("AgencyORM", back_populates="leads")
    deals: Mapped[list[DealORM]] = relationship("DealORM", back_populates="lead")
    chat_messages: Mapped[list[ChatMessageORM]] = relationship(
        "ChatMessageORM", back_populates="lead"
    )


# ---------------------------------------------------------------------------
# PropertyORM
# ---------------------------------------------------------------------------

class PropertyORM(TimestampMixin, Base):
    __tablename__ = "property"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agency.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    neighborhood: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    condo_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iptu: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    parking_spots: Mapped[int] = mapped_column(Integer, nullable=False)
    accepts_pet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="available")
    owner_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    agency: Mapped[AgencyORM] = relationship("AgencyORM", back_populates="properties")
    deals: Mapped[list[DealORM]] = relationship("DealORM", back_populates="property")


# ---------------------------------------------------------------------------
# DocumentTemplateORM
# ---------------------------------------------------------------------------

class DocumentTemplateORM(TimestampMixin, Base):
    __tablename__ = "document_template"
    __table_args__ = (
        UniqueConstraint("agency_id", "slug", name="uq_document_template_agency_slug"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    agency_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agency.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    documents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    html_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    agency: Mapped[Optional[AgencyORM]] = relationship(
        "AgencyORM", back_populates="document_templates"
    )
    deals: Mapped[list[DealORM]] = relationship(
        "DealORM", back_populates="document_template"
    )


# ---------------------------------------------------------------------------
# DealORM
# ---------------------------------------------------------------------------

class DealORM(TimestampMixin, Base):
    __tablename__ = "deal"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agency.id"), nullable=False
    )
    lead_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("lead.id"), nullable=False
    )
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("property.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False, default="locacao")
    stage: Mapped[str] = mapped_column(String, nullable=False, default="negotiation")
    document_template_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("document_template.id"), nullable=True
    )
    pending_actions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    agency: Mapped[AgencyORM] = relationship("AgencyORM", back_populates="deals")
    lead: Mapped[LeadORM] = relationship("LeadORM", back_populates="deals")
    property: Mapped[PropertyORM] = relationship("PropertyORM", back_populates="deals")
    document_template: Mapped[Optional[DocumentTemplateORM]] = relationship(
        "DocumentTemplateORM", back_populates="deals"
    )
    documents: Mapped[list[DealDocumentORM]] = relationship(
        "DealDocumentORM", back_populates="deal", cascade="all, delete-orphan"
    )
    proposals: Mapped[list[ProposalORM]] = relationship(
        "ProposalORM", back_populates="deal", cascade="all, delete-orphan"
    )
    contract_drafts: Mapped[list[ContractDraftORM]] = relationship(
        "ContractDraftORM", back_populates="deal", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list[ChatMessageORM]] = relationship(
        "ChatMessageORM", back_populates="deal"
    )


# ---------------------------------------------------------------------------
# DealDocumentORM
# ---------------------------------------------------------------------------

class DealDocumentORM(Base):
    __tablename__ = "deal_document"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deal.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    attachment_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("attachment.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    deal: Mapped[DealORM] = relationship("DealORM", back_populates="documents")
    attachment: Mapped[Optional[AttachmentORM]] = relationship("AttachmentORM")


# ---------------------------------------------------------------------------
# AttachmentORM
# ---------------------------------------------------------------------------

class AttachmentORM(Base):
    __tablename__ = "attachment"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    document_type_classification: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# ProposalORM
# ---------------------------------------------------------------------------

class ProposalORM(Base):
    __tablename__ = "proposal"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deal.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    condo_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iptu: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    guarantee_type: Mapped[str] = mapped_column(String, nullable=False)
    deposit_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    move_in_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contract_duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    special_conditions: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    generated_text: Mapped[str] = mapped_column(String, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    deal: Mapped[DealORM] = relationship("DealORM", back_populates="proposals")


# ---------------------------------------------------------------------------
# ContractDraftORM
# ---------------------------------------------------------------------------

class ContractDraftORM(Base):
    __tablename__ = "contract_draft"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deal.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    template_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    generated_text: Mapped[str] = mapped_column(String, nullable=False, default="")
    missing_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    deal: Mapped[DealORM] = relationship("DealORM", back_populates="contract_drafts")


# ---------------------------------------------------------------------------
# ChatMessageORM
# ---------------------------------------------------------------------------

class ChatMessageORM(Base):
    __tablename__ = "chat_message"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    deal_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deal.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("lead.id"), nullable=True
    )
    sender: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    deal: Mapped[Optional[DealORM]] = relationship(
        "DealORM", back_populates="chat_messages"
    )
    lead: Mapped[Optional[LeadORM]] = relationship(
        "LeadORM", back_populates="chat_messages"
    )
    attachments: Mapped[list[AttachmentORM]] = relationship(
        "AttachmentORM",
        secondary=chat_message_attachment,
    )


# ---------------------------------------------------------------------------
# DocumentAnalysisORM
# ---------------------------------------------------------------------------

class GuidelineORM(TimestampMixin, Base):
    __tablename__ = "guideline"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agency.id"), nullable=False
    )
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    agency: Mapped[AgencyORM] = relationship("AgencyORM")


# ---------------------------------------------------------------------------
# DocumentAnalysisORM
# ---------------------------------------------------------------------------

class DocumentAnalysisORM(TimestampMixin, Base):
    __tablename__ = "document_analysis"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    attachment_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("attachment.id"), nullable=True
    )
    deal_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deal.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("lead.id"), nullable=True
    )
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_resume: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    attachment: Mapped[Optional[AttachmentORM]] = relationship("AttachmentORM")
    deal: Mapped[Optional[DealORM]] = relationship("DealORM")
    lead: Mapped[Optional[LeadORM]] = relationship("LeadORM")
