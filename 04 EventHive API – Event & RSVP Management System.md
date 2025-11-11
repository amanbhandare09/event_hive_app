### **Project 04**  
**Project Title**: EventHive API – Event & RSVP Management System  
**Project Description**:  
Developed a scalable event management API that allows users to create events, manage capacity, and handle RSVPs through a stateless REST interface. The system enforces business logic (e.g., capacity limits, duplicate prevention) at the API layer and includes a CLI utility for sending automated reminders, showcasing real-world constraint handling in web APIs.

**Objective**:  
- Build REST endpoints for event creation, listing, and attendee management  
- Model `Event` and `Attendee` with a many-to-many relationship in SQLAlchemy  
- Prevent duplicate RSVPs and enforce event capacity limits in business logic  
- Support querying upcoming events and attendee lists via clean endpoints  
- Implement a CLI tool to simulate sending reminders (e.g., 24 hours before event)  
- Use proper HTTP status codes (409 for conflicts, 400 for invalid requests)  
- Ensure data consistency with transaction-aware database operations  

**Tools Used**:  
- **Backend Framework**: Flask, Flask-SQLAlchemy, Flask-Migrate  
- **Database**: SQLite or PostgreSQL  
- **CLI**: Click for reminder simulation and event listing  
- **Validation**: Custom validation logic or Pydantic  
- **Testing**: Manual testing with curl/HTTPie; optional pytest coverage  

**Weeks (during training)**: 1–4 (both inclusive)  
**Project Type**: Intermediate API project emphasizing business logic enforcement, relational modeling, and state management  
**Outcome**:  
Delivered a robust event and RSVP API that handles real-world constraints like capacity and duplication. The system is ready for integration with notification services or frontend calendars and demonstrates strong backend engineering discipline using Flask and SQL.
