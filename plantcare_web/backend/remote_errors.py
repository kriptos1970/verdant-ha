"""Safe actionable errors; dependency failures must survive HA Ingress proxies."""
import httpx


def describe(error):
    request=getattr(error,'request',None)
    host=request.url.host if request else ''
    service='Gemini' if host=='generativelanguage.googleapis.com' else 'OpenAI' if host=='api.openai.com' else 'Pl@ntNet' if host=='my-api.plantnet.org' else 'Perenual' if host in {'perenual.com','www.perenual.com'} else 'Open Plantbook' if host=='open.plantbook.io' else 'Il servizio esterno'
    if isinstance(error,httpx.TimeoutException):
        return 424,f'{service} non ha risposto in tempo. Riprova tra poco.'
    if not isinstance(error,httpx.HTTPStatusError):
        return 424,f'Impossibile raggiungere {service}. Controlla la connessione Internet e il DNS di Home Assistant.'
    code=error.response.status_code
    reasons=set();message=''
    try:
        data=error.response.json().get('error',{})
        if isinstance(data,dict):
            message=str(data.get('message','')).lower()
            for detail in data.get('details',[]) or []:
                if isinstance(detail,dict) and isinstance(detail.get('reason'),str):reasons.add(detail['reason'])
            if isinstance(data.get('code'),str):reasons.add(data['code'])
    except (ValueError,TypeError,AttributeError):pass
    # Never include arbitrary upstream text: providers may echo credentials.
    if reasons & {'API_KEY_INVALID','API_KEY_EXPIRED','invalid_api_key'} or 'api key not valid' in message:
        detail=f'La chiave {service} non è valida o è scaduta. Verifica la chiave nelle opzioni dell’add-on e riavvia Verdant.'
    elif reasons & {'API_KEY_HTTP_REFERRER_BLOCKED','API_KEY_IP_ADDRESS_BLOCKED','API_KEY_SERVICE_BLOCKED'}:
        detail=f'Le restrizioni della chiave impediscono l’accesso a {service} da Home Assistant. Verifica le autorizzazioni della chiave nel provider.'
    elif 'location is not supported' in message or 'not available in your country' in message:
        detail=f'{service} non è disponibile per la località della connessione Home Assistant.'
        if service=='Gemini':
            detail+=' Google classifica l’IP pubblico dell’istanza: se il problema compare solo da questa rete, prova a ottenere un nuovo IP dal router o segnalalo a Google.'
    elif code in (401,403):
        detail=f'{service} non autorizza questa chiave (HTTP {code}). Verifica chiave, progetto e autorizzazioni nel provider.'
    elif code==400:
        detail=f'{service} ha rifiutato la richiesta (HTTP 400). Verifica la chiave e il modello configurato.'
    elif code==404:
        detail=f'Il modello o servizio richiesto non è disponibile su {service} (HTTP 404). Carica il catalogo e scegli un modello disponibile.'
    elif code==429:
        detail=f'{service} ha raggiunto il limite di richieste o credito (HTTP 429). Controlla quota e fatturazione nel provider.'
    else:
        detail=f'{service} non è disponibile (HTTP {code}). Riprova tra poco.'
    return (422 if code in (400,401,403,404) else 424),detail
