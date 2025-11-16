# app/validators.py
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import date, time
from enum import Enum
from typing import Optional

# ------------------------------------------------------------------
# ENUMS – **must stay 1-to-1 with DB enums**
# ------------------------------------------------------------------
class EventModeEnum(str, Enum):
    online = "online"
    offline = "offline"

class EventVisibilityEnum(str, Enum):
    public = "public"
    private = "private"

class EventTagEnum(str, Enum):
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    MEETING = "Meeting"
    CONFERENCE = "Conference"
    PARTY = "Party"
    CELEBRATION = "Celebration"
    NETWORKING = "Networking"
    FUNDRAISER = "Fundraiser"
    COMPETITION = "Competition"
    PERFORMANCE = "Performance"
    FESTIVAL = "Festival"
    WEBINAR = "Webinar"
    TRAINING = "Training"
    SPORTS = "Sports"
    TRIP = "Trip"
    VOLUNTEERING = "Volunteering"
    HACKATHON = "Hackathon"
    LAUNCH = "Launch"
    CULTURAL = "Cultural"
    EDUCATIONAL = "Educational"
    ENTERTAINMENT = "Entertainment"
    SOCIAL = "Social"
    PROFESSIONAL = "Professional"
    TECH = "Tech"
    ART = "Art"
    MUSIC = "Music"
    FOOD = "Food"
    HEALTH = "Health"
    ENVIRONMENT = "Environment"


# ------------------------------------------------------------------
# USER CREATE
# ------------------------------------------------------------------
class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


# ------------------------------------------------------------------
# EVENT – CREATE / UPDATE
# ------------------------------------------------------------------
class EventCreateUpdateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    date: date
    starttime: Optional[time] = None
    endtime: Optional[time] = None
    mode: EventModeEnum = EventModeEnum.online
    venue: Optional[str] = Field(None, max_length=150)
    capacity: int = Field(..., ge=1, le=10_000)
    visibility: EventVisibilityEnum = EventVisibilityEnum.public
    tags: EventTagEnum = EventTagEnum.CELEBRATION

    @field_validator("date")
    @classmethod
    def date_not_past(cls, v: date) -> date:
        from datetime import date as date_cls
        if v < date_cls.today():
            raise ValueError("Event date cannot be in the past")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Event title cannot be empty")
        return v.strip()

    @model_validator(mode='after')
    def validate_end_after_start(self):
        if self.starttime and self.endtime and self.endtime <= self.starttime:
            raise ValueError("endtime must be after starttime")
        return self


# ------------------------------------------------------------------
# EVENT FILTER SCHEMA (for search/filter queries)
# ------------------------------------------------------------------
class EventFilterSchema(BaseModel):
    title: Optional[str] = None
    tag: Optional[str] = None
    organizer: Optional[str] = None
    date: Optional[date] = None
    visibility: Optional[EventVisibilityEnum] = None
    location: Optional[str] = None
    mode: Optional[EventModeEnum] = None


# ------------------------------------------------------------------
# ATTENDEE REGISTRATION
# ------------------------------------------------------------------
class AttendeeRegistrationSchema(BaseModel):
    event_id: int = Field(..., ge=1)

# ------------------------------------------------------------------
# QR CODE SCAN / MARK ATTENDANCE
# ------------------------------------------------------------------
class MarkAttendanceSchema(BaseModel):
    attendee_id: int = Field(..., ge=1)
    event_id: int = Field(..., ge=1)
    user_id: int = Field(..., ge=1)
    token: str = Field(..., min_length=1)