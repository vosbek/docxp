"""
Repository management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
from pathlib import Path
import git

from app.core.database import get_session, Repository
from app.models.schemas import RepositoryInfo

router = APIRouter()

@router.get("/", response_model=List[RepositoryInfo])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    """List all repositories"""
    query = await db.execute(
        select(Repository)
        .offset(skip)
        .limit(limit)
    )
    repos = query.scalars().all()
    
    return [
        RepositoryInfo(
            path=repo.path,
            name=repo.name,
            total_files=repo.total_files,
            total_lines=repo.total_lines,
            languages=repo.languages or {},
            is_git=bool(repo.git_remote),
            last_commit=repo.last_commit,
            size_mb=0  # Calculate if needed
        )
        for repo in repos
    ]

@router.post("/validate", response_model=RepositoryInfo)
async def validate_repository(
    repo_path: str,
    db: AsyncSession = Depends(get_session)
):
    """Validate and analyze a repository"""
    
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail="Repository path not found")
    
    # Analyze repository
    info = await _analyze_repository(repo_path)
    
    # Check if it's a git repository
    is_git = False
    last_commit = None
    git_remote = None
    
    try:
        repo = git.Repo(repo_path)
        is_git = True
        if repo.head.commit:
            last_commit = str(repo.head.commit)
        if repo.remotes:
            git_remote = repo.remotes[0].url
    except:
        pass
    
    # Save to database
    db_repo = Repository(
        path=repo_path,
        name=Path(repo_path).name,
        total_files=info['total_files'],
        total_lines=info['total_lines'],
        languages=info['languages'],
        git_remote=git_remote,
        last_commit=last_commit
    )
    
    # Check if already exists
    existing = await db.execute(
        select(Repository).where(Repository.path == repo_path)
    )
    if not existing.scalar_one_or_none():
        db.add(db_repo)
        await db.commit()
    
    return RepositoryInfo(
        path=repo_path,
        name=Path(repo_path).name,
        total_files=info['total_files'],
        total_lines=info['total_lines'],
        languages=info['languages'],
        is_git=is_git,
        last_commit=last_commit,
        size_mb=info['size_mb']
    )

async def _analyze_repository(repo_path: str) -> dict:
    """Analyze repository structure"""
    info = {
        'total_files': 0,
        'total_lines': 0,
        'languages': {},
        'size_mb': 0
    }
    
    total_size = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        
        for file in files:
            file_path = Path(root) / file
            info['total_files'] += 1
            
            # Count by extension
            ext = file_path.suffix
            if ext:
                info['languages'][ext] = info['languages'].get(ext, 0) + 1
            
            # Get file size
            total_size += file_path.stat().st_size
            
            # Count lines for text files
            if ext in ['.py', '.java', '.js', '.ts', '.pl', '.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        info['total_lines'] += sum(1 for _ in f)
                except:
                    pass
    
    info['size_mb'] = round(total_size / (1024 * 1024), 2)
    
    return info
