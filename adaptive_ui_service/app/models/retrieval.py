from pydantic import BaseModel

from adaptive_ui_service.app.models.capability import Capability


class ScoredCapability(BaseModel):
    capability: Capability
    score: float
