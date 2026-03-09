import asyncio
from google.adk.sessions import InMemorySessionService

async def main():
    service = InMemorySessionService()
    await service.create_session(app_name="app", user_id="user", session_id="123")
    session = await service.get_session(app_name="app", user_id="user", session_id="123")
    print("AGENT STATE DIR:")
    print(dir(session.agent_state))
    print("AGENT STATE DICT:")
    print(session.agent_state.__dict__)

if __name__ == "__main__":
    asyncio.run(main())
