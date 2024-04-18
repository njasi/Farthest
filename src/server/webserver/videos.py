from aiohttp import web
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Video  # Assuming models.py contains the Video model definition

engine = create_engine("your_database_url")
Session = sessionmaker(bind=engine)

async def create_video(request):
    data = await request.json()

    try:
        async with Session() as session:
            video = Video.find_or_create(session=session, **data)
            return web.json_response({"message": "Video created successfully", "video_id": video.id})

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def get_video(request):
    video_id = request.match_info['video_id']

    try:
        async with Session() as session:
            video = Video.find_by_id(video_id, session=session)
            if video:
                return web.json_response({"video": video.__dict__})
            else:
                return web.json_response({"message": "Video not found"}, status=404)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_post('/videos', create_video)
app.router.add_get('/videos/{video_id}', get_video)

if __name__ == '__main__':
    web.run_app(app)
