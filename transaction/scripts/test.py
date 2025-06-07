import random
import time

import requests

# Étape 1 : Connexion
login_url = "http://127.0.0.1:8000/api/v0/entities/login/"
login_payload = {"code": "CRPAY", "entity_id": "0aef8351-d226-4310-9e9f-c4c432a028de"}
headers = {"Content-Type": "application/json"}
login_response = requests.post(login_url, json=login_payload, headers=headers)
print("Login status code:", login_response.status_code)
print("Login response:", login_response.json())

if login_response.status_code == 200:
    token = login_response.json().get("access")
    transaction_url = "http://127.0.0.1:8000/api/v0/transactions/create"
    transaction_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    for i in range(1000):
        amount = random.randint(200, 3500)
        purpose = random.choice(["Refund", "Payment"])
        first_name = random.choice(
            ["Aliou", "Fatou", "Ibrahima", "Mariam", "Seydou", "Aissatou"]
        )
        last_name = random.choice(["Barry", "Diallo", "Bah", "Camara", "Sow", "Sylla"])
        transaction_payload = {
            "amount": amount,
            "invoice_type": "Payment",
            "purpose": purpose,
            "details": {
                "recipientFirstName": first_name,
                "recipientLastName": last_name,
            },
        }
        response = requests.post(
            transaction_url, json=transaction_payload, headers=transaction_headers
        )
        print(
            f"[{i + 1}/1000] Status: {response.status_code} - {response.json() if response.status_code != 500 else 'Erreur serveur'}"
        )
        time.sleep(
            0.05
        )  # Petite pause pour éviter de saturer le serveur (peut ajuster selon besoin

else:
    print("Échec de l'authentification.")
