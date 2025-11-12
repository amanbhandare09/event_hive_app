from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, time, datetime
from enum import Enum
from typing import Optional


# ---------------- ENUMS ---------------- #

class EventModeEnum(str, Enum):
    online = "online"
    offline = "offline"


class EventVisibilityEnum(str, Enum):
    public = "public"
    private = "private"


# ---------------- USER VALIDATION ---------------- #

class UserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=200)

    @validator("password")
    def validate_password_strength(cls, v):
        """
        Enforces minimum complexity:
        - At least 8 characters
        - At least one digit
        - At least one letter
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        return v

    class Config:
        orm_mode = True


# ---------------- EVENT VALIDATION ---------------- #

class EventCreateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    date: date
    time: Optional[time]
    mode: EventModeEnum = EventModeEnum.online
    venue: Optional[str] = Field(None, max_length=150)
    capacity: int = Field(..., ge=1)
    visibility: EventVisibilityEnum = EventVisibilityEnum.public
    organizer_id: int = Field(..., gt=0, description="ID of the event organizer (User ID)")

    @validator("date")
    def validate_event_date(cls, v):
        """Ensure event date is today or in the future."""
        if v < date.today():
            raise ValueError("Event date cannot be in the past.")
        return v

    @validator("title")
    def validate_title(cls, v):
        """Prevent titles that are just spaces."""
        if not v.strip():
            raise ValueError("Event title cannot be empty or blank.")
        return v

    class Config:
        orm_mode = True


# ---------------- EVENT RESPONSE SCHEMA ---------------- #

class EventResponseSchema(BaseModel):
    id: int
    title: str
    description: Optional[str]
    date: date
    time: Optional[time]
    mode: EventModeEnum
    venue: Optional[str]
    capacity: int
    visibility: EventVisibilityEnum
    organizer_id: int

    class Config:
        orm_mode = True
