"""HTTP client for CoW Protocol Orderbook API.

This module provides an async client for interacting with the CoW Protocol
orderbook API, supporting order submission, status queries, and appData uploads.
"""

import json
from typing import Any

import aiohttp


class OrderbookClient:
    """Async client for CoW Protocol Orderbook API.

    Provides methods for submitting orders, querying order status, and uploading
    appData documents to the orderbook service.
    """

    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3):
        """Initialize the orderbook client.

        Args:
            base_url: Base URL of the orderbook API (e.g., http://localhost:8080)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries

    async def submit_order(self, signed_order: dict[str, Any]) -> dict[str, Any]:
        """Submit a signed order to the orderbook.

        Args:
            signed_order: Complete signed order with all required fields

        Returns:
            Response from the orderbook containing order UID and status

        Raises:
            aiohttp.ClientError: If the request fails
            aiohttp.ClientResponseError: If the server returns an error status
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.base_url}/api/v1/orders",
                json=signed_order,
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Order submission failed: {error_text}",
                        headers=response.headers,
                    )
                result: dict[str, Any] = await response.json()
                return result

    async def get_order(self, order_uid: str) -> dict[str, Any]:
        """Get order details by UID.

        Args:
            order_uid: The unique order identifier

        Returns:
            Order details including status, amounts, and metadata

        Raises:
            aiohttp.ClientError: If the request fails
            aiohttp.ClientResponseError: If the order is not found or server error
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/api/v1/orders/{order_uid}",
            ) as response:
                response.raise_for_status()
                result: dict[str, Any] = await response.json()
                return result

    async def get_trades(self, order_uid: str) -> list[dict[str, Any]]:
        """Get trades for an order.

        Args:
            order_uid: The unique order identifier

        Returns:
            List of trades associated with the order. Empty list if no trades found.

        Raises:
            aiohttp.ClientError: If the request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/api/v1/orders/{order_uid}/trades",
            ) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                result: list[dict[str, Any]] = await response.json()
                return result

    async def upload_app_data(
        self, app_data_hash: str, app_data_doc: str | dict[str, Any]
    ) -> dict[str, Any]:
        """Upload appData document to the orderbook.

        This is required before submitting orders with custom appData (e.g., hooks).

        Args:
            app_data_hash: 32-byte hash of the appData document (with 0x prefix)
            app_data_doc: Full appData JSON document (as string or dict)

        Returns:
            Response from the orderbook (typically empty on success)

        Raises:
            aiohttp.ClientError: If the request fails
            aiohttp.ClientResponseError: If the server returns an error status
        """
        # Parse app_data_doc to dict if it's a string
        if isinstance(app_data_doc, str):
            app_data_doc = json.loads(app_data_doc)

        # Strip 0x prefix for the URL path
        hash_without_prefix = app_data_hash[2:] if app_data_hash.startswith("0x") else app_data_hash

        # The API expects the appData wrapped in a "fullAppData" field
        request_body = {"fullAppData": json.dumps(app_data_doc)}

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.put(
                f"{self.base_url}/api/v1/app_data/{hash_without_prefix}",
                json=request_body,
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"AppData upload failed: {error_text}",
                        headers=response.headers,
                    )
                # API may return empty response on success
                text = await response.text()
                if text:
                    result: dict[str, Any] = await response.json()
                    return result
                return {}

    async def get_version(self) -> dict[str, Any]:
        """Get the API version information.

        Useful for health checks and API compatibility verification.

        Returns:
            Version information from the orderbook API

        Raises:
            aiohttp.ClientError: If the request fails
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/api/v1/version",
            ) as response:
                response.raise_for_status()
                result: dict[str, Any] = await response.json()
                return result

    async def check_health(self) -> bool:
        """Check if the orderbook API is healthy and responding.

        Returns:
            True if the API is healthy, False otherwise
        """
        try:
            await self.get_version()
            return True
        except Exception:
            return False
