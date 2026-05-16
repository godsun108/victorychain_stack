from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import VoteCreate, VoteResponse
from ..services.donations import get_or_create_donor
from ..services.governance import cast_vote

router = APIRouter(prefix="/governance", tags=["governance"])


@router.post("/vote", response_model=VoteResponse)
def vote(payload: VoteCreate, db: Session = Depends(get_db)):
    donor = get_or_create_donor(db, email=payload.voter_email)
    try:
        vote_obj = cast_vote(db, donor, payload.category, payload.project_id, payload.signal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return VoteResponse(vote_id=vote_obj.id, token_weight=vote_obj.token_weight, advisory_only=vote_obj.advisory_only)
