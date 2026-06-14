"""Clicksign integration for digital document signing.

Clicksign API docs: https://developers.clicksign.com/
Auth: API token passed as query parameter.

Flow:
1. Upload document (POST /documents)
2. Create signer (POST /signers)
3. Add signer to document (POST /lists)
4. Send notification (POST /notifications)
"""

import os
import base64
import logging
import httpx
from integrations.base import (
    SignatureProvider,
    SignatureRequest,
    SignatureResponse,
    SignerInfo,
)

logger = logging.getLogger(__name__)

class ClicksignProvider(SignatureProvider):
    """Clicksign digital signature integration."""

    def __init__(self):
        self.client = httpx.Client(timeout=30)

    @property
    def base_url(self) -> str:
        return os.getenv("CLICKSIGN_BASE_URL", "https://sandbox.clicksign.com/api/v1")

    @property
    def api_key(self) -> str:
        return os.getenv("CLICKSIGN_API_KEY", "")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}?access_token={self.api_key}"

    def upload_and_send(self, request: SignatureRequest) -> SignatureResponse:
        if not self.api_key:
            return SignatureResponse(
                success=False,
                provider="clicksign",
                error="CLICKSIGN_API_KEY not configured. Set it in .env to enable digital signing.",
            )

        try:
            # Step 1: Upload document
            doc_b64 = base64.standard_b64encode(request.document_pdf).decode()
            upload_resp = self.client.post(
                self._url("/documents"),
                json={
                    "document": {
                        "path": f"/contratos/{request.document_name}.pdf",
                        "content_base64": f"data:application/pdf;base64,{doc_b64}",
                    }
                },
            )
            upload_resp.raise_for_status()
            doc_data = upload_resp.json()["document"]
            doc_key = doc_data["key"]

            signer_keys = []
            for signer in request.signers:
                # Step 2: Create signer
                signer_resp = self.client.post(
                    self._url("/signers"),
                    json={
                        "signer": {
                            "email": signer.email,
                            "phone_number": signer.phone,
                            "auths": "email",
                            "name": signer.name,
                            "documentation": signer.document_cpf,
                        }
                    },
                )
                signer_resp.raise_for_status()
                signer_key = signer_resp.json()["signer"]["key"]
                signer_keys.append(signer_key)

                # Step 3: Add signer to document
                list_resp = self.client.post(
                    self._url("/lists"),
                    json={
                        "list": {
                            "document_key": doc_key,
                            "signer_key": signer_key,
                            "sign_as": "sign",
                        }
                    },
                )
                list_resp.raise_for_status()
                request_signature_key = list_resp.json()["list"]["request_signature_key"]

                # Step 4: Send notification
                self.client.post(
                    self._url("/notifications"),
                    json={
                        "request_signature_key": request_signature_key,
                        "message": request.message or f"Contrato de locação para assinatura — {request.document_name}",
                    },
                )

            return SignatureResponse(
                success=True,
                provider="clicksign",
                document_id=doc_key,
                signing_url=f"https://app.clicksign.com/sign/{doc_key}",
                status="sent",
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Clicksign API error: {e.response.text}")
            return SignatureResponse(
                success=False,
                provider="clicksign",
                error=f"Clicksign API error: {e.response.status_code} — {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Clicksign integration error: {e}")
            return SignatureResponse(
                success=False,
                provider="clicksign",
                error=str(e),
            )

    def check_status(self, document_id: str) -> SignatureResponse:
        if not self.api_key:
            return SignatureResponse(
                success=False,
                provider="clicksign",
                error="CLICKSIGN_API_KEY not configured",
            )

        try:
            resp = self.client.get(self._url(f"/documents/{document_id}"))
            resp.raise_for_status()
            doc = resp.json()["document"]
            return SignatureResponse(
                success=True,
                provider="clicksign",
                document_id=document_id,
                status=doc.get("status", "unknown"),
            )
        except Exception as e:
            return SignatureResponse(
                success=False,
                provider="clicksign",
                error=str(e),
            )


# Singleton
clicksign = ClicksignProvider()
