"""
bKash Payment Gateway Service
Handles: Grant Token, Refresh Token, Create Payment, Execute Payment, Query Payment, Refund
Official docs: https://developer.bka.sh/docs/checkout-url-process-overview
"""

import requests
import logging
from django.conf import settings
from django.core.cache import cache



logger = logging.getLogger(__name__)

# Sandbox base URLs (use LIVE_BASE_URL in production) 
SANDBOX_BASE_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout"
LIVE_BASE_URL    = "https://tokenized.pay.bka.sh/v1.2.0-beta/tokenized/checkout"


class BkashService:
    """
    Stateless service call BkashService() anywhere.
    Tokens are cached in Django's cache backend (Redis recommended).
    """

    def __init__(self):
        self.app_key    = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username   = settings.BKASH_USERNAME
        self.password   = settings.BKASH_PASSWORD
        self.sandbox    = getattr(settings, "BKASH_SANDBOX", True)
        self.base_url   = SANDBOX_BASE_URL if self.sandbox else LIVE_BASE_URL
        self.timeout    = 30  # bKash requires 30-second API timeout

    # Headers

    def _base_headers(self):
        return {
            "Content-Type":  "application/json",
            "Accept":        "application/json",
            "username":      self.username,
            "password":      self.password,
            "X-APP-Key":     self.app_key,
        }

    def _auth_headers(self, token):
        return {
            "Content-Type":   "application/json",
            "Accept":         "application/json",
            "Authorization":  token,
            "X-APP-Key":      self.app_key,
        }

    # Token management 

    def _grant_token(self):
        """Call /token/grant and store both tokens in cache."""
        url = f"{self.base_url}/token/grant"
        payload = {
            "app_key":    self.app_key,
            "app_secret": self.app_secret,
        }
        resp = requests.post(url, json=payload,
                             headers=self._base_headers(),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if ("id_token" not in data or "refresh_token" not in data):
            raise Exception(
             data.get("statusMessage", "Token grant failed")
            )

        id_token      = data["id_token"]
        refresh_token = data["refresh_token"]

        # id_token valid 1 hour, refresh_token valid 28 days
        cache.set("bkash_id_token",      id_token,      timeout=3500)
        cache.set("bkash_refresh_token", refresh_token, timeout=28 * 24 * 3600)
        logger.info("bKash: new id_token granted.")
        return id_token

    def _refresh_token(self, refresh_token):
        """Call /token/refresh when id_token expires."""
        url = f"{self.base_url}/token/refresh"
        payload = {"app_key": self.app_key, "app_secret": self.app_secret,
                   "refresh_token": refresh_token}
        resp = requests.post(url, json=payload,
                             headers=self._base_headers(),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if "id_token" not in data:
            raise Exception(
             data.get("statusMessage", "Failed to refresh token")
             )

        id_token = data["id_token"]
        cache.set("bkash_id_token", id_token, timeout=3500)

        if "refresh_token" in data:
            cache.set(
            "bkash_refresh_token",
            data["refresh_token"],
            timeout=28 * 24 * 3600
                )
        logger.info("bKash: id_token refreshed.")
        return id_token

    def get_token(self):
        """
        Return a valid id_token.
        Priority: cached id_token → refresh → new grant.
        Per bKash docs: REUSE id_token for 1 hour across all requests.
        """
        id_token = cache.get("bkash_id_token")
        if id_token:
            return id_token

        refresh_token = cache.get("bkash_refresh_token")
        if refresh_token:
            try:
                return self._refresh_token(refresh_token)
            except Exception as e:
                logger.warning(f"bKash token refresh failed: {e}")

        return self._grant_token()

    #Create Payment

    def create_payment(self, amount, order_id, callback_url, currency="BDT",
                       intent="sale", merchant_invoice_number=None):
        """
        Step 1 Create a payment and get bKashURL to redirect the user to.

        Returns the full API response dict. Key fields:
          - bkashURL  → redirect user here
          - paymentID → store this; needed to execute
          - statusCode == "0000" means success
        """
        token = self.get_token()
        url   = f"{self.base_url}/create"
        payload = {
            "mode":                    "0011",  # Checkout URL mode
            "payerReference":          str(order_id),
            "callbackURL":             callback_url,
            "amount":                  str(amount),
            "currency":                currency,
            "intent":                  intent,
            "merchantInvoiceNumber":   merchant_invoice_number or str(order_id),
        }
        resp = requests.post(url, json=payload,
                             headers=self._auth_headers(token),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("statusCode") != "0000":
            raise Exception(
             data.get("statusMessage", "bKash API Error")
             )

        return data

    #Execute Payment 

    def execute_payment(self, payment_id):
        """
        Step 2  Execute after bKash redirects back with status=success.
        ONLY call this when callback status == 'success'.

        statusCode == "0000" is the ONLY success indicator.
        """
        token = self.get_token()
        url   = f"{self.base_url}/execute"
        payload = {"paymentID": payment_id}
        resp = requests.post(url, json=payload,
                             headers=self._auth_headers(token),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("statusCode") != "0000":
            raise Exception(
             data.get("statusMessage", "bKash API Error")
             )

        return data

    #Query Payment

    def query_payment(self, payment_id):
        """
        ONLY call this if execute_payment gets no response (network error).
        Do NOT use as a standard polling mechanism.
        """
        token = self.get_token()
        url   = f"{self.base_url}/payment/status"
        payload = {"paymentID": payment_id}
        resp = requests.post(url, json=payload,
                             headers=self._auth_headers(token),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("statusCode") != "0000":
            raise Exception(
             data.get("statusMessage", "bKash API Error")
             )

        return data

    #Refund

    def refund_transaction(self, payment_id, trx_id, amount, reason, sku=None):
        """
        Issue a full or partial refund for a completed transaction.
        Uses the same id_token as other calls.
        """
        token = self.get_token()
        url   = f"{self.base_url}/payment/refund"
        payload = {
            "paymentID":           payment_id,
            "trxID":               trx_id,
            "amount":              str(amount),
            "reason":              reason,
            "sku":                 sku or "refund",
        }
        resp = requests.post(url, json=payload,
                             headers=self._auth_headers(token),
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("statusCode") != "0000":
            raise Exception(
             data.get("statusMessage", "bKash API Error")
             )

        return data