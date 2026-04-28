import asyncio
from llm_provider import OpenRouterProvider

async def main():
    try:
        # Use a dummy key to trigger an auth error. We want to see if the error is 401 Unauth or something else like validation error.
        provider = OpenRouterProvider(api_key="sk-or-v1-dummy")
        response = await provider.generate_content(
            model='gemini-2.5-flash',
            system_instruction='test',
            messages=[{'role':'user', 'content':'test'}]
        )
        print(response)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
