import asyncio

import httpx

from app.config import get_settings


async def main() -> None:
    s = get_settings()
    base = s.gemini_base_url.rstrip("/")
    key_prefix = (s.gemini_api_key or "")[:12]
    print("configured_model", s.chat_model, "key_prefix", key_prefix)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Say hi in one word."}]}],
        "generationConfig": {"temperature": 0.2},
    }
    models = [
        s.chat_model if s.chat_model.startswith("models/") else f"models/{s.chat_model}",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-lite",
        "models/gemini-2.5-flash-lite",
    ]
    seen: set[str] = set()
    async with httpx.AsyncClient(timeout=30) as client:
        for m in models:
            if m in seen:
                continue
            seen.add(m)
            r = await client.post(
                f"{base}/{m}:generateContent",
                params={"key": s.gemini_api_key},
                json=payload,
            )
            body = r.text.replace("\n", " ")[:400]
            print(m, r.status_code, body)


if __name__ == "__main__":
    asyncio.run(main())
