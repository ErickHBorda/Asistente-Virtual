import re
import datetime

months = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

def interpret_gmail_query(text: str) -> str:
    text = text.lower()
    query_parts = []
    today = datetime.date.today()

    # Frases relativas de tiempo
    if "ayer" in text:
        date = today - datetime.timedelta(days=1)
        query_parts.append(f"after:{date.strftime('%Y/%m/%d')}")
    elif "hoy" in text:
        query_parts.append(f"after:{today.strftime('%Y/%m/%d')}")
    elif "últimos 7 días" in text or "última semana" in text:
        date = today - datetime.timedelta(days=7)
        query_parts.append(f"after:{date.strftime('%Y/%m/%d')}")

    # Buscar remitente
    match_sender = re.search(r"correos de (\w+)", text)
    if match_sender:
        posible_remitente = match_sender.group(1)
        if posible_remitente not in months:
            query_parts.append(f"from:{posible_remitente}")

    # Buscar asunto
    match_subject = re.search(r"sobre (\w+)", text)
    if match_subject:
        query_parts.append(f"subject:{match_subject.group(1)}")

    # Buscar fecha exacta tipo "del 15 de julio"
    match_date = re.search(r"del (\d{1,2}) de (\w+)", text)
    if match_date:
        day = match_date.group(1).zfill(2)
        mes = match_date.group(2)
        if mes in months:
            year = today.year
            query_parts.append(f"after:{year}/{months[mes]}/{day}")

    # Buscar "entre mes1 y mes2"
    match_between = re.search(r"entre (\w+) y (\w+)", text)
    if match_between:
        mes1, mes2 = match_between.groups()
        if mes1 in months and mes2 in months:
            year = today.year
            query_parts.append(f"after:{year}/{months[mes1]}/01")
            query_parts.append(f"before:{year}/{months[mes2]}/01")

    # Buscar solo el mes (ej: julio)
    for mes in months:
        if f"de {mes}" in text or mes in text:
            year = today.year
            query_parts.append(f"after:{year}/{months[mes]}/01")
            next_month = int(months[mes]) + 1
            if next_month <= 12:
                query_parts.append(f"before:{year}/{str(next_month).zfill(2)}/01")
            break

    return " ".join(query_parts)