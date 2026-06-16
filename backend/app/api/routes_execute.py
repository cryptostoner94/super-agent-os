from fastapi import APIRouter
from backend.app.core.bounty_executor import execute_bounty_hunt

router = APIRouter(prefix="/execute/bounty", tags=["execute"])


@router.get("/dashboard")
async def bounty_dashboard():
    return await execute_bounty_hunt(action="dashboard")


@router.get("/programs")
async def bounty_programs(platform: str = "all"):
    return await execute_bounty_hunt(action="list_programs", platform=platform)


@router.get("/reports")
async def my_reports():
    return await execute_bounty_hunt(action="my_reports")


@router.get("/profile")
async def my_profile():
    return await execute_bounty_hunt(action="my_profile")


@router.post("/run")
async def run_bounty_action(payload: dict):
    action = payload.get("action", "dashboard")
    platform = payload.get("platform", "all")
    return await execute_bounty_hunt(action=action, platform=platform)
