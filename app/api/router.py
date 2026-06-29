from fastapi import APIRouter

from app.api.v1 import auth, package, member, subscription, checkin
from app.api.v1.admin import users as admin_users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(package.router)
api_router.include_router(member.router)
api_router.include_router(subscription.router)
api_router.include_router(checkin.router)
api_router.include_router(admin_users.router)
