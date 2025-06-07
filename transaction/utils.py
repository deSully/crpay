import os

import httpx


class ExternalTransactionDispatcher:
    BASE_URL = "https://apidist.gutouch.net/apidist/sec/touchpayapi"

    def __init__(self, transaction):
        self.transaction = transaction
        self.agency_code = os.environ["INTOUCH_AGENCY_CODE"]
        self.login_agent = os.environ["INTOUCH_LOGIN_AGENT"]
        self.password_agent = os.environ["INTOUCH_PASSWORD_AGENT"]
        self.callback_url = os.environ["INTOUCH_CALLBACK_URL"]

    async def dispatch(self):
        url = f"{self.BASE_URL}/{self.agency_code}/transaction"
        params = {
            "loginAgent": self.login_agent,
            "passwordAgent": self.password_agent,
        }

        details = self.transaction.details or {}

        payload = {
            "idFromClient": str(self.transaction.reference),
            "additionnalInfos": {
                "recipientEmail": details.get("recipientEmail", ""),
                "recipientFirstName": details.get("recipientFirstName", ""),
                "recipientLastName": details.get("recipientLastName", ""),
                "destinataire": details.get("destinataire", ""),
                "otp": details.get("otp", ""),
            },
            "amount": float(self.transaction.amount),
            "callback": self.callback_url,
            "recipientNumber": details.get("destinataire", ""),
            "serviceCode": "PAIEMENTMARCHANDOMPAYCIDIRECT",
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(url, params=params, json=payload)

        return response
