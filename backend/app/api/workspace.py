from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.auth import WorkspaceCreate, WorkspaceResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ws = Workspace(name=payload.name, slug=payload.slug, owner_id=current_user.id)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)

    member = WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="OWNER")
    db.add(member)
    await db.commit()

    return WorkspaceResponse(id=ws.id, name=ws.name, slug=ws.slug, owner_id=ws.owner_id)

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(Workspace.owner_id == current_user.id)
    res = await db.execute(stmt)
    workspaces = res.scalars().all()
    if not workspaces:
        # Auto-create default workspace for dev
        default_ws = Workspace(name="Default Workspace", slug="default-workspace", owner_id=current_user.id)
        db.add(default_ws)
        await db.commit()
        await db.refresh(default_ws)
        workspaces = [default_ws]

    return [WorkspaceResponse(id=w.id, name=w.name, slug=w.slug, owner_id=w.owner_id) for w in workspaces]
