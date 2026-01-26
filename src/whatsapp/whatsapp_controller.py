from fastapi import APIRouter, Request

router = APIRouter(prefix="/whatsapp", tags=["Whatsapp"])

@router.post("/messages-upsert")
async def read_messages(request: Request):
    """Endpoint para recibir y procesar mensajes de WhatsApp"""
    headers = dict(request.headers)
    body = await request.body()
    json_body = await request.json() if body else None
    query_params = dict(request.query_params)
    
    print("=== HEADERS ===")
    print(headers)
    print("=== BODY (raw) ===")
    print(body)
    print("=== BODY (json) ===")
    print(json_body)
    print("=== QUERY PARAMS ===")
    print(query_params)
    print("=== METHOD ===")
    print(request.method)
    print("=== URL ===")
    print(request.url)