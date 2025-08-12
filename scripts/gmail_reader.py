#pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import os
import base64
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def read_emails():
    creds = None
    token_path = 'google_api/token.json'
    creds_path = 'google_api/credentials.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
    messages = results.get('messages', [])

    emails = []
    if not messages:
        return ["No tienes correos nuevos."]
    
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Remitente desconocido')
        emails.append(f"De: {sender} | Asunto: {subject}")
    
    return emails

def search_emails(query_filter: str):
    """
    Realiza una búsqueda avanzada en los correos de Gmail.
    query_filter: cadena con sintaxis de Gmail como:
        - 'from:amazon'
        - 'subject:pedido'
        - 'after:2024/07/01'
        - 'from:google subject:factura after:2024/06/01'
    """
    creds = None
    token_path = 'google_api/token.json'
    creds_path = 'google_api/credentials.json'
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', q=query_filter, maxResults=5).execute()
    messages = results.get('messages', [])
    output = []

    if not messages:
        return [f"No se encontraron correos para: {query_filter}"]

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Remitente desconocido')
        output.append(f"De: {sender} | Asunto: {subject}")
    
    return output
