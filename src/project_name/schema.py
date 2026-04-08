from typing import List

from pydantic import BaseModel, Field


class MicrocategoryDictEntry(BaseModel):
    mcId: int
    mcTitle: str = Field(min_length=1)
    keyPhrases: List[str] = Field(default_factory=list)


class ItemInput(BaseModel):
    itemId: int
    mcId: int
    mcTitle: str = Field(min_length=1)
    description: str = Field(min_length=1)


class Draft(BaseModel):
    mcId: int
    mcTitle: str = Field(min_length=1)
    text: str = ""


class SplitResult(BaseModel):
    detectedMcIds: List[int] = Field(default_factory=list)
    shouldSplit: bool
    drafts: List[Draft] = Field(default_factory=list)
