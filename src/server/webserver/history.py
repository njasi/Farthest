from aiohttp import web
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import History  # Assuming models.py contains the History model definition

engine = create_engine("your_database_url")
Session = sessionmaker(bind=engine)

async def create_history(request):
    data = await request.json()

    try:
        async with Session() as session:
            history = History.create(session=session, **data)
            return web.json_response({"message": "History created successfully", "history_id": history.id})

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def update_history(request):
    data = await request.json()
    history_id = data.get('id')
    if not history_id:
        return web.json_response({"error": "History ID is required"}, status=400)

    try:
        async with Session() as session:
            History.update(history_id, **data, session=session)
            return web.json_response({"message": "History updated successfully"})

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_post('/history', create_history)
app.router.add_put('/history', update_history)

if __name__ == '__main__':
    web.run_app(app)
