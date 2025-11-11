### **Project 04**  
**Project Title:** EventHive API – Event & RSVP Management System  

**Project Description:**  
Developed a scalable event management API that allows users to create events, manage capacity, and handle RSVPs through a stateless REST interface. The system enforces business logic (e.g., capacity limits, duplicate RSVP prevention) at the API layer and includes a CLI utility for sending automated reminders. The architecture emphasizes real-world constraint handling, data consistency, and modular expansion into notification or calendar systems.

**Objective:**  
- Build REST endpoints for event creation, Listing, and attendee management  
- Model `Event` and `Attendee` using a many-to-many relationship in SQLAlchemy  
- Prevent duplicate RSVPs and enforce event capacity limits at the business logic layer  
- Support querying upcoming events and attendee lists via clean, RESTful endpoints  
- Implement a CLI tool to simulate sending event reminders (example: 24 hours before start time)  
- Use appropriate HTTP status codes (`409 Conflict`, `400 Bad Request`, etc.)  
- Ensure data consistency via transaction-aware database operations  

**Tools Used:**  
- **Backend Framework:** Flask, Flask-SQLAlchemy, Flask-Migrate  
- **Database:** SQLite / PostgreSQL  
- **CLI:** Click (for reminder simulation and event listing)  
- **Validation:** Pydantic or Custom Validation  
- **Testing:** HTTPie / Curl / Optional Pytest  

**Timeline:** Week 1–4 (During Training)  
**Project Type:** Intermediate Backend Project based on API Design, Validation & Relational Modeling  
**Outcome:**  
Delivered a robust backend system capable of managing events, handling RSVP workflows efficiently, and enforcing key business rules. Ready for UI integration or notification system expansion.

---

## **Event Management System — Detailed Feature List**

### **1. Core System Architecture**
- **CLI Support**   
  Full system functionality is accessible through the command line.
  
- **Data Validation using Pydantic**   
  Ensures input correctness and enforces strict data integrity.

- **Tag-Based Classification**   
  Allows filtering and categorization of events using descriptive tags.

- **Advanced Search Functionality**   
  Users can search events by:
  - Event Name  
  - Location  
  - Date / Time Range  
  - Created By

- **QR Code Generation**  
  Generate QR codes for:
  - Event Check-In  
  - Access Verification  
  - Sharing Invitations

---

### **2. Event Creation & Configuration**

#### **Public vs Private Events**
- **Public Events:** Open to all users.
- **Private Events:** Require join request and approval.
  - Approval notifications are emailed to the event creator.

#### **Reminders**
- A checkbox enables reminder scheduling.
- Sends automated email reminders to all event participants.

#### **Event Duration & Scheduling** 
- Supports multi-day events with clear:
  - **Start Time**
  - **End Time**
  - **Duration Calculation**

#### **Location Mapping**
- Store and categorize events based on their physical and/or virtual location.

---

### **3. Event Lifecycle & Status Management**
- Automatically **mark events as completed** upon end time.
- **Archive completed events**:
  - Keep historical records.
  - Allow **duplicate/cloning** to quickly recreate similar future events.

---

