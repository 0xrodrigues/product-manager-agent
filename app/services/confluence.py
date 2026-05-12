import logging
from base64 import b64encode

import httpx

from app.config import settings
from app.models.story import ConfluencePage, ConfluencePageResponse, ConfluenceSearchResult

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """HTTP client para a API REST v1 do Confluence."""

    def __init__(self) -> None:
        token = b64encode(
            f"{settings.atlassian_user_email}:{settings.atlassian_api_token}".encode()
        ).decode()
        self._base_url = settings.atlassian_base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._ssl_verify = settings.atlassian_ssl_verify

    def search_pages(self, cql: str, limit: int = 10) -> list[ConfluenceSearchResult]:
        """Busca páginas usando CQL (Confluence Query Language).

        Raises:
            httpx.HTTPStatusError: em respostas 4xx/5xx.
        """
        logger.info("Buscando páginas no Confluence com CQL: %s", cql)
        with httpx.Client(headers=self._headers, verify=self._ssl_verify) as client:
            response = client.get(
                f"{self._base_url}/wiki/rest/api/content/search",
                params={"cql": cql, "limit": limit, "expand": "space,version"},
            )
            response.raise_for_status()

        results = response.json().get("results", [])
        return [
            ConfluenceSearchResult(
                page_id=item["id"],
                title=item["title"],
                space_key=item["space"]["key"],
                url=f"{self._base_url}/wiki{item['_links']['webui']}",
            )
            for item in results
        ]

    def get_page_by_id(self, page_id: str) -> dict:
        """Retorna uma página pelo ID com conteúdo em formato storage.

        Raises:
            httpx.HTTPStatusError: em respostas 4xx/5xx.
        """
        logger.info("Buscando página do Confluence com ID: %s", page_id)
        with httpx.Client(headers=self._headers, verify=self._ssl_verify) as client:
            response = client.get(
                f"{self._base_url}/wiki/rest/api/content/{page_id}",
                params={"expand": "body.storage,version,space,ancestors"},
            )
            response.raise_for_status()

        return response.json()

    def get_pages_by_space(self, space_key: str, limit: int = 25) -> list[ConfluenceSearchResult]:
        """Lista páginas de um espaço Confluence.

        Raises:
            httpx.HTTPStatusError: em respostas 4xx/5xx.
        """
        logger.info("Listando páginas do espaço Confluence: %s", space_key)
        with httpx.Client(headers=self._headers, verify=self._ssl_verify) as client:
            response = client.get(
                f"{self._base_url}/wiki/rest/api/content",
                params={
                    "spaceKey": space_key,
                    "type": "page",
                    "limit": limit,
                    "expand": "version,space",
                    "status": "current",
                },
            )
            response.raise_for_status()

        results = response.json().get("results", [])
        return [
            ConfluenceSearchResult(
                page_id=item["id"],
                title=item["title"],
                space_key=item["space"]["key"],
                url=f"{self._base_url}/wiki{item['_links']['webui']}",
            )
            for item in results
        ]

    def create_page(self, page: ConfluencePage) -> ConfluencePageResponse:
        """Cria uma nova página no Confluence.

        Raises:
            httpx.HTTPStatusError: em respostas 4xx/5xx.
        """
        payload = self._build_create_payload(page)
        logger.info("Criando página no Confluence no espaço %s: %s", page.space_key, page.title)

        with httpx.Client(headers=self._headers, verify=self._ssl_verify) as client:
            response = client.post(
                f"{self._base_url}/wiki/rest/api/content",
                json=payload,
            )
            response.raise_for_status()

        return self._parse_page_response(response.json())

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version_number: int,
    ) -> ConfluencePageResponse:
        """Atualiza o conteúdo de uma página existente.

        Raises:
            httpx.HTTPStatusError: em respostas 4xx/5xx.
        """
        payload = {
            "type": "page",
            "title": title,
            "version": {"number": version_number},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            },
        }
        logger.info("Atualizando página do Confluence ID %s para versão %d", page_id, version_number)

        with httpx.Client(headers=self._headers, verify=self._ssl_verify) as client:
            response = client.put(
                f"{self._base_url}/wiki/rest/api/content/{page_id}",
                json=payload,
            )
            response.raise_for_status()

        return self._parse_page_response(response.json())

    def _build_create_payload(self, page: ConfluencePage) -> dict:
        """Converte um ConfluencePage em payload para a API REST do Confluence."""
        payload: dict = {
            "type": "page",
            "title": page.title,
            "space": {"key": page.space_key},
            "body": {
                "storage": {
                    "value": page.body,
                    "representation": "storage",
                }
            },
        }
        if page.parent_id:
            payload["ancestors"] = [{"id": page.parent_id}]
        return payload

    def _parse_page_response(self, data: dict) -> ConfluencePageResponse:
        """Extrai campos relevantes da resposta da API do Confluence."""
        return ConfluencePageResponse(
            page_id=data["id"],
            title=data["title"],
            url=f"{self._base_url}/wiki{data['_links']['webui']}",
            version=data["version"]["number"],
        )
