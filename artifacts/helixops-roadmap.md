# HelixOps — Product Development Roadmap

**Philosophy:** Build the SaaS foundation first. Infrastructure before intelligence. Workflows before automation. Automation before agents. Agents before orchestration.

---

## Table of Contents

1. [Phase 0 — Project Foundation & Architecture](#phase-0)
2. [Phase 1 — Authentication & Authorization](#phase-1)
3. [Phase 2 — Clinic Management](#phase-2)
4. [Phase 3 — Patient Management](#phase-3)
5. [Phase 4 — Appointment Management](#phase-4)
6. [Phase 5 — Document Management](#phase-5)
7. [Phase 6 — Notifications & Communication Infrastructure](#phase-6)
8. [Phase 7 — Dashboard & Operational Analytics](#phase-7)
9. [Phase 8 — Event-Driven Architecture](#phase-8)
10. [Phase 9 — AI Infrastructure Layer](#phase-9)
11. [Phase 10 — Document Intelligence Agent](#phase-10)
12. [Phase 11 — Appointment Scheduling Agent](#phase-11)
13. [Phase 12 — Medical Knowledge RAG Agent](#phase-12)
14. [Phase 13 — Follow-Up & Reminder Agent](#phase-13)
15. [Phase 14 — Risk Escalation Agent](#phase-14)
16. [Phase 15 — LangGraph Orchestration Layer](#phase-15)
17. [Phase 16 — Multi-Agent Workflow Automation](#phase-16)
18. [Phase 17 — Advanced Analytics & Insights](#phase-17)
19. [Cross-Cutting Concerns](#cross-cutting)
20. [Full Tech Stack Summary](#tech-stack)
21. [Project Timeline Estimate](#timeline)

---

## Phase 0 — Project Foundation & Architecture {#phase-0}

### Goal
Establish the monorepo structure, tooling, CI/CD pipeline, environment configuration, and coding conventions that every subsequent phase depends on.

### Why This Phase Exists
No feature can be built reliably without a shared foundation. A misconfigured environment, missing linting rules, or absent CI/CD pipeline creates compounding technical debt from day one. This phase costs one week and saves ten.

### Features
- Monorepo scaffold (Next.js frontend + FastAPI backend in one repo)
- ESLint, Prettier, Black, Ruff configured
- Pre-commit hooks (Husky + lint-staged)
- GitHub Actions CI pipeline (lint → test → build)
- Docker Compose for local development (app + postgres + redis)
- Environment variable schema with validation (Zod on frontend, Pydantic Settings on backend)
- Shared TypeScript types package
- README, contribution guide, ADR (Architecture Decision Record) template

### Backend Scope
- FastAPI project scaffold with `app/`, `routers/`, `models/`, `schemas/`, `services/`, `core/` folders
- Pydantic Settings for typed environment config (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, etc.)
- Alembic for database migrations, baseline migration
- Health check endpoint `GET /health`
- Structured JSON logging via `structlog`
- Global exception handler returning RFC 7807 problem+json responses
- CORS middleware configured for local dev

### Frontend Scope
- Next.js 16 App Router scaffold with `app/`, `components/`, `lib/`, `hooks/`, `types/` folders
- Tailwind CSS + shadcn/ui initialized
- Absolute imports configured (`@/`)
- Environment variable validation with Zod
- Base layout shell (header, sidebar placeholder, main content area)
- Dark/light mode toggle via `next-themes`

### Database Changes
- PostgreSQL database created (`helixops_db`)
- Alembic migration history table initialized
- No domain tables yet — schema only

### API Surface
- `GET /health` — liveness check returning `{ status: "ok", version, timestamp }`
- `GET /api/v1/` — API root returning available route groups

### Architecture Additions
```
helixops/
├── apps/
│   ├── web/          ← Next.js frontend
│   └── api/          ← FastAPI backend
├── packages/
│   └── types/        ← Shared TypeScript types
├── infra/
│   └── docker-compose.yml
├── .github/
│   └── workflows/ci.yml
└── docs/
    └── adr/          ← Architecture decision records
```

### Event Flow
None. No events are produced or consumed in this phase.

### Dependencies
- None. This is the root dependency for everything else.

### Definition of Done
- `docker compose up` starts all services without error
- `GET /health` returns 200
- CI pipeline passes on a clean branch
- Linting and formatting pass on all files
- At least one passing test exists (health check smoke test)
- README explains local setup in under 10 steps

### Risks & Considerations
- Monorepo tooling (Turborepo vs Nx) decision should be made now, not later — changing it mid-project is painful
- Alembic migration naming conventions must be agreed on before Phase 1 adds tables
- Docker Compose postgres volume should be named explicitly to prevent accidental data loss on `compose down -v`

### Future AI Impact
The structured logging set up here will be essential for tracing agent decision chains. The ADR folder will hold agent design decisions. The folder structure accommodates a future `apps/agent/` service without restructuring.

---

## Phase 1 — Authentication & Authorization {#phase-1}

### Goal
Implement a complete, role-based authentication system for three user types: Patient, Doctor, and Admin — with secure session management, JWT issuance, and route protection.

### Why This Phase Exists
Every subsequent phase requires knowing *who* is making a request and *what they are allowed to do*. Without auth, you cannot build multi-tenant clinic isolation, patient-scoped data access, or doctor-specific dashboards. Auth must exist before any domain data model.

### Features
- Registration and login for all three roles
- Email verification flow
- Password reset via email token
- JWT access tokens (short-lived, 15 min) + refresh tokens (long-lived, 7 days, stored in httpOnly cookie)
- Role-based access control (RBAC): `patient`, `doctor`, `admin`
- Permission guards on all API routes
- Session invalidation (logout, token revocation via Redis blocklist)
- Rate limiting on auth endpoints (login, register, reset)
- Optional: Clerk integration as external auth provider (recommended for production)

### Backend Scope
- `POST /auth/register` — creates user with hashed password (bcrypt), sends verification email
- `POST /auth/login` — validates credentials, issues JWT pair
- `POST /auth/refresh` — rotates access token using refresh token cookie
- `POST /auth/logout` — revokes refresh token, adds to Redis blocklist
- `POST /auth/forgot-password` — generates reset token, sends email
- `POST /auth/reset-password` — validates reset token, updates password
- `GET /auth/verify-email` — confirms email with token
- `get_current_user` dependency injectable into any FastAPI route
- `require_role(roles: list[str])` dependency for RBAC enforcement
- Refresh token rotation: each use issues a new token, old one is revoked

### Frontend Scope
- `/login`, `/register`, `/forgot-password`, `/reset-password` pages
- Auth context with `useAuth()` hook (current user, role, loading state)
- Axios/fetch interceptor: auto-attaches Authorization header, auto-refreshes token on 401
- Route guards: `<ProtectedRoute role="doctor" />` wrapper component
- Redirect logic: unauthenticated users → `/login`, authenticated → role-specific dashboard
- Persistent auth state via secure cookie (no localStorage for tokens)

### Database Changes

**Table: `users`**
```
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
password_hash VARCHAR(255)
role          ENUM('patient','doctor','admin','super_admin') NOT NULL
is_verified   BOOLEAN DEFAULT FALSE
is_active     BOOLEAN DEFAULT TRUE
created_at    TIMESTAMPTZ DEFAULT NOW()
updated_at    TIMESTAMPTZ DEFAULT NOW()
```

**Table: `refresh_tokens`**
```
id          UUID PRIMARY KEY
user_id     UUID REFERENCES users(id) ON DELETE CASCADE
token_hash  VARCHAR(255) UNIQUE NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
revoked_at  TIMESTAMPTZ
created_at  TIMESTAMPTZ DEFAULT NOW()
```

**Table: `email_verifications`**
```
id         UUID PRIMARY KEY
user_id    UUID REFERENCES users(id) ON DELETE CASCADE
token      VARCHAR(255) UNIQUE NOT NULL
expires_at TIMESTAMPTZ NOT NULL
used_at    TIMESTAMPTZ
```

**Indexes:**
- `users(email)` — unique, used on every login
- `refresh_tokens(token_hash)` — used on every token refresh
- `refresh_tokens(user_id)` — used for session listing and bulk revocation

### API Surface
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `GET  /api/v1/auth/verify-email?token=`
- `GET  /api/v1/auth/me` — returns current user profile

### Architecture Additions
- `app/core/security.py` — JWT signing, verification, bcrypt hashing
- `app/core/dependencies.py` — `get_current_user`, `require_role` FastAPI dependencies
- `app/services/auth_service.py` — registration, login, token lifecycle
- `app/services/email_service.py` — templated email sending (Sendgrid or SMTP)
- Redis client module for token blocklist operations
- Frontend: `lib/auth.ts`, `hooks/useAuth.tsx`, `components/ProtectedRoute.tsx`

### Event Flow
- `user.registered` → triggers verification email dispatch
- `user.verified` → unlocks full account access
- `user.password_reset` → triggers confirmation email

### Dependencies
- Phase 0 (project scaffold, database connection, logging)

### Definition of Done
- All three roles can register, verify email, and log in
- Protected routes return 401 for unauthenticated requests and 403 for wrong-role requests
- Refresh token rotation works correctly
- Rate limiting blocks >10 failed login attempts per minute per IP
- All auth endpoints have integration tests

### Risks & Considerations
- JWT secret must be rotated without invalidating all sessions — plan for key versioning
- Refresh token in httpOnly cookie requires same-site and secure flags in production; local dev needs explicit CORS credentials configuration
- If using Clerk, replace the custom JWT layer but keep the `users` table synchronized via Clerk webhooks — the rest of the system depends on `user_id`

### Future AI Impact
Every agent action will be attributed to a `user_id`. The `require_role` dependency will gate which agents are accessible to patients vs doctors. The `users` table becomes the identity anchor for all AI-generated records (summaries, escalations, reminders).

---

## Phase 2 — Clinic Management {#phase-2}

### Goal
Allow platform admins to onboard clinics, configure their settings, manage their staff roster, and establish the multi-tenant boundary that isolates one clinic's data from another.

### Why This Phase Exists
Helixops is a multi-tenant SaaS platform. Every piece of domain data — patients, appointments, documents — belongs to a specific clinic. Without clinic isolation established now, retrofitting it later means migrating every existing table. Clinic context must be the second thing built, right after identity.

### Features
- Clinic registration and onboarding flow (for super admins)
- Clinic profile: name, address, logo, contact details, specialty type
- Clinic settings: working hours, appointment duration defaults, timezone
- Staff management: invite doctors and admin staff by email, assign roles
- Doctor profiles: specialty, qualifications, availability template, bio
- Clinic subscription/plan status (Free / Pro / Enterprise) — placeholder for billing
- Soft-delete for clinics (deactivation, not hard deletion)
- Clinic slug for vanity URLs (`/clinic/apollo-delhi`)

### Backend Scope
- Full CRUD for `clinics` resource
- Clinic onboarding wizard endpoint (multi-step: basic info → hours → first admin)
- Staff invitation system: generates time-limited invite token, sends email, links accepted user to clinic
- `clinic_id` injected as a dependency on all domain routes — every query is scoped to it
- Doctor availability template CRUD (weekly schedule patterns)
- Clinic settings CRUD
- File upload for clinic logo (S3/R2 pre-signed URL flow)

### Frontend Scope
- Super admin panel: clinic list, create clinic, view clinic details
- Clinic admin dashboard shell (scoped nav, clinic branding in header)
- Clinic settings page: general, working hours, appearance
- Staff management page: invite by email, view roster, deactivate staff
- Doctor profile page: edit bio, qualifications, availability template
- Invite acceptance flow: `/invite/accept?token=` page

### Database Changes

**Table: `clinics`**
```
id           UUID PRIMARY KEY
name         VARCHAR(255) NOT NULL
slug         VARCHAR(100) UNIQUE NOT NULL
address      TEXT
city         VARCHAR(100)
state        VARCHAR(100)
country      VARCHAR(100) DEFAULT 'IN'
phone        VARCHAR(20)
email        VARCHAR(255)
logo_url     TEXT
timezone     VARCHAR(50) DEFAULT 'Asia/Kolkata'
plan         ENUM('free','pro','enterprise') DEFAULT 'free'
is_active    BOOLEAN DEFAULT TRUE
created_at   TIMESTAMPTZ DEFAULT NOW()
updated_at   TIMESTAMPTZ DEFAULT NOW()
```

**Table: `clinic_staff`** (join table between users and clinics)
```
id         UUID PRIMARY KEY
clinic_id  UUID REFERENCES clinics(id) ON DELETE CASCADE
user_id    UUID REFERENCES users(id) ON DELETE CASCADE
role       ENUM('admin','doctor','receptionist') NOT NULL
is_active  BOOLEAN DEFAULT TRUE
joined_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE(clinic_id, user_id)
```

**Table: `doctor_profiles`**
```
id               UUID PRIMARY KEY
user_id          UUID REFERENCES users(id) UNIQUE
clinic_id        UUID REFERENCES clinics(id)
specialty        VARCHAR(100)
qualifications   TEXT[]
bio              TEXT
consultation_fee NUMERIC(10,2)
created_at       TIMESTAMPTZ DEFAULT NOW()
```

**Table: `clinic_settings`**
```
id                         UUID PRIMARY KEY
clinic_id                  UUID REFERENCES clinics(id) UNIQUE
default_slot_duration_mins INTEGER DEFAULT 20
working_hours              JSONB  -- { mon: {open:"09:00", close:"17:00"}, ... }
appointment_types          JSONB  -- ["in-person","teleconsult"]
updated_at                 TIMESTAMPTZ DEFAULT NOW()
```

**Table: `staff_invitations`**
```
id         UUID PRIMARY KEY
clinic_id  UUID REFERENCES clinics(id)
email      VARCHAR(255) NOT NULL
role       ENUM('admin','doctor','receptionist')
token      VARCHAR(255) UNIQUE NOT NULL
expires_at TIMESTAMPTZ NOT NULL
accepted_at TIMESTAMPTZ
```

**Indexes:**
- `clinic_staff(clinic_id, user_id)` — unique constraint + lookup
- `clinic_staff(user_id)` — find all clinics for a user
- `clinics(slug)` — URL routing

### API Surface
- `POST   /api/v1/clinics` — create clinic (super_admin only)
- `GET    /api/v1/clinics/:id` — get clinic details
- `PATCH  /api/v1/clinics/:id` — update clinic profile
- `GET    /api/v1/clinics/:id/staff` — list staff
- `POST   /api/v1/clinics/:id/staff/invite` — send invitation
- `POST   /api/v1/invitations/accept` — accept staff invite
- `GET    /api/v1/clinics/:id/settings` — get settings
- `PATCH  /api/v1/clinics/:id/settings` — update settings
- `GET    /api/v1/doctors/:id/profile` — get doctor profile
- `PATCH  /api/v1/doctors/:id/profile` — update doctor profile

### Architecture Additions
- `app/core/clinic_context.py` — FastAPI dependency that extracts and validates `clinic_id` from JWT claims or path param; injects into all domain routes
- `app/services/clinic_service.py`
- `app/services/invitation_service.py`
- `app/storage/s3_client.py` — pre-signed URL generation for logo uploads
- Row-Level Security (RLS) consideration: all domain tables will have `clinic_id` FK, queries always filtered by it

### Event Flow
- `clinic.created` → sends welcome email to clinic admin
- `staff.invited` → sends invitation email with accept link
- `staff.joined` → notifies clinic admin of new staff member

### Dependencies
- Phase 0 (foundation), Phase 1 (users table, auth system)

### Definition of Done
- A clinic can be created and has settings, staff, and doctor profiles
- All domain routes correctly scope data to the requesting user's clinic
- Staff invitation flow works end-to-end (invite → email → accept → login)
- Attempting to access another clinic's resources returns 403

### Risks & Considerations
- The `clinic_id` scoping dependency must be applied consistently — missing it on one route is a data leak. Consider a base router class that enforces it
- Timezone handling: store all datetimes in UTC, convert to clinic timezone only at display layer. Establish this convention now; it affects every appointment and reminder later
- Soft-delete on clinics must cascade to deactivation of all associated staff accounts without hard-deleting patient records

### Future AI Impact
The `clinic_id` scoping established here ensures each clinic gets its own isolated RAG knowledge base partition, its own agent workflow configurations, and its own analytics dashboards. Clinic settings (working hours, appointment types) become direct inputs to the Scheduling Agent's slot-fetching logic.

---

## Phase 3 — Patient Management {#phase-3}

### Goal
Build the complete patient lifecycle: registration, profile management, medical history, allergies, current medications, and emergency contacts — giving doctors and staff a complete view of who a patient is before any appointment or document is created.

### Why This Phase Exists
Patients are the central entity in the entire system. Appointments are booked for patients. Documents belong to patients. Reminders are sent to patients. Risk flags are attached to patients. Building the patient record correctly now — with all its relationships — prevents painful schema changes later when AI agents need structured patient context to reason over.

### Features
- Patient self-registration via portal
- Admin/receptionist-assisted patient registration
- Patient profile: demographics, contact info, emergency contact
- Medical history: chronic conditions, past surgeries, family history
- Current medications list (name, dose, frequency, prescribing doctor)
- Allergy registry (allergen, reaction type, severity)
- Patient search (by name, phone, date of birth, patient ID)
- Patient ID generation (formatted: `MED-YYYY-XXXXX`)
- Patient deactivation (soft delete)
- GDPR/data privacy: patient data export and deletion request workflow

### Backend Scope
- Patient registration with duplicate detection (same phone + DOB)
- Patient search with full-text search on name + fuzzy match on phone
- Medical history CRUD (versioned — never overwrite, append new entries)
- Medications CRUD with active/discontinued status
- Allergies CRUD
- Patient summary endpoint (aggregates profile + active meds + allergies + last visit)
- Pagination on patient list endpoints

### Frontend Scope
- Patient portal: self-registration, profile view and edit
- Doctor/staff views: patient list with search, patient detail page
- Patient detail page tabs: Overview, Medical History, Medications, Allergies, Appointments (placeholder), Documents (placeholder)
- Medication entry form: drug name (autocomplete from a local drug list), dose, frequency, start date
- Allergy entry form: allergen, reaction, severity badge
- Patient search bar: debounced, returns name + DOB + patient ID

### Database Changes

**Table: `patients`**
```
id                UUID PRIMARY KEY
clinic_id         UUID REFERENCES clinics(id)
user_id           UUID REFERENCES users(id) UNIQUE  -- if patient has portal access
patient_number    VARCHAR(20) UNIQUE NOT NULL        -- MED-2025-00001
first_name        VARCHAR(100) NOT NULL
last_name         VARCHAR(100) NOT NULL
date_of_birth     DATE NOT NULL
gender            ENUM('male','female','other','prefer_not_to_say')
phone             VARCHAR(20) NOT NULL
email             VARCHAR(255)
address           TEXT
blood_group       VARCHAR(5)
emergency_contact JSONB  -- { name, phone, relationship }
is_active         BOOLEAN DEFAULT TRUE
created_at        TIMESTAMPTZ DEFAULT NOW()
updated_at        TIMESTAMPTZ DEFAULT NOW()
```

**Table: `medical_history`**
```
id            UUID PRIMARY KEY
patient_id    UUID REFERENCES patients(id)
condition     VARCHAR(255) NOT NULL
diagnosed_at  DATE
notes         TEXT
recorded_by   UUID REFERENCES users(id)
created_at    TIMESTAMPTZ DEFAULT NOW()
```

**Table: `medications`**
```
id               UUID PRIMARY KEY
patient_id       UUID REFERENCES patients(id)
drug_name        VARCHAR(255) NOT NULL
dosage           VARCHAR(100)
frequency        VARCHAR(100)
route            VARCHAR(50)   -- oral, IV, topical
prescribed_by    UUID REFERENCES users(id)
start_date       DATE
end_date         DATE
is_active        BOOLEAN DEFAULT TRUE
created_at       TIMESTAMPTZ DEFAULT NOW()
```

**Table: `allergies`**
```
id           UUID PRIMARY KEY
patient_id   UUID REFERENCES patients(id)
allergen     VARCHAR(255) NOT NULL
reaction     VARCHAR(255)
severity     ENUM('mild','moderate','severe','life_threatening')
notes        TEXT
created_at   TIMESTAMPTZ DEFAULT NOW()
```

**Indexes:**
- `patients(clinic_id)` — all patients of a clinic
- `patients(clinic_id, phone)` — duplicate detection
- `patients(patient_number)` — unique patient lookup
- Full-text index on `patients(first_name, last_name)` using `tsvector`
- `medications(patient_id, is_active)` — active meds query
- `allergies(patient_id)` — patient allergy lookup

### API Surface
- `POST   /api/v1/patients` — register patient
- `GET    /api/v1/patients` — list patients (paginated, searchable)
- `GET    /api/v1/patients/:id` — patient detail
- `PATCH  /api/v1/patients/:id` — update profile
- `GET    /api/v1/patients/:id/summary` — full clinical summary
- `POST   /api/v1/patients/:id/medical-history` — add history entry
- `GET    /api/v1/patients/:id/medical-history` — list history
- `POST   /api/v1/patients/:id/medications` — add medication
- `PATCH  /api/v1/patients/:id/medications/:med_id` — update/discontinue
- `GET    /api/v1/patients/:id/medications` — list medications
- `POST   /api/v1/patients/:id/allergies` — add allergy
- `GET    /api/v1/patients/:id/allergies` — list allergies
- `DELETE /api/v1/patients/:id/allergies/:allergy_id` — remove allergy

### Architecture Additions
- `app/services/patient_service.py` with search, summary aggregation
- `app/utils/patient_number.py` — sequential ID generator with prefix
- PostgreSQL full-text search (`to_tsvector`, `to_tsquery`) on patient names
- Frontend: patient search component with debounce, patient summary card

### Event Flow
- `patient.registered` → welcome SMS/email (consumed by Phase 6 notification service)
- `patient.profile_updated` → audit log entry

### Dependencies
- Phase 1 (auth — to link patient portal user), Phase 2 (clinic scoping)

### Definition of Done
- A doctor can search, view, and update any patient in their clinic
- A patient can view and edit their own profile via the portal
- Medical history, medications, and allergies are all CRUD-complete
- Patient summary endpoint aggregates all clinical context in one call
- Full-text search returns correct results for partial name matches

### Risks & Considerations
- Duplicate patient detection must be surfaced as a warning, not a hard block — same person may have two records from different registration channels
- Medical history must be append-only at the service level; updates should create new version entries to preserve audit trail
- Phone number normalization (E.164 format) must be enforced on input — `+91XXXXXXXXXX` — or search will silently fail

### Future AI Impact
The `GET /patients/:id/summary` endpoint becomes the primary context payload passed to every AI agent that needs to reason about a patient. The structured medications and allergies tables enable the Risk Escalation Agent to check for drug interactions and allergy conflicts. The medical history entries are the ground truth that the RAG Agent's answers must be consistent with.

---

## Phase 4 — Appointment Management {#phase-4}

### Goal
Build a complete appointment lifecycle system: slot availability, booking, confirmation, rescheduling, cancellation, and visit records — without any AI involvement.

### Why This Phase Exists
Appointment management is the core transactional workflow of any clinic. It must work reliably as a pure CRUD + calendar system before any agent touches it. The Scheduling Agent in a later phase is only as good as the underlying slot engine it sits on top of. Building this now also generates real appointment data that analytics (Phase 7) and event-driven workflows (Phase 8) will depend on.

### Features
- Doctor availability templates (weekly recurring schedule)
- Slot generation from availability templates
- Real-time slot availability queries
- Appointment booking (in-person / teleconsult)
- Appointment confirmation, rescheduling, cancellation
- Cancellation reasons and policies (e.g., free before 24h, fee after)
- Waitlist for fully-booked slots
- Appointment status workflow: `scheduled → confirmed → checked_in → completed → cancelled`
- Visit notes (doctor adds post-visit notes after appointment)
- Optimistic slot locking to prevent double-booking
- Calendar view on doctor dashboard

### Backend Scope
- Slot generation algorithm: reads availability template + exceptions, produces available windows
- Conflict detection: queries existing confirmed appointments before booking
- Optimistic lock: Redis TTL-based slot hold (5 minutes) when slot is surfaced to a patient
- Appointment state machine enforced at the service layer (invalid transitions rejected)
- Visit notes endpoint: doctor submits SOAP-formatted or free-text notes after appointment
- Appointment history: full audit trail of status changes with timestamps and actor

### Frontend Scope
- Doctor availability template editor: weekly grid (Mon–Sun, time blocks)
- Patient-facing booking flow: choose specialty → choose doctor → pick date → pick slot → confirm
- Doctor dashboard: calendar view (weekly/daily) with appointment cards
- Appointment detail modal: patient info, visit type, notes, status controls
- Admin view: all appointments across all doctors, filter by date/doctor/status
- Cancellation flow with reason selection
- Waitlist join UI

### Database Changes

**Table: `availability_templates`**
```
id             UUID PRIMARY KEY
doctor_id      UUID REFERENCES doctor_profiles(id)
clinic_id      UUID REFERENCES clinics(id)
day_of_week    SMALLINT NOT NULL  -- 0=Mon, 6=Sun
start_time     TIME NOT NULL
end_time       TIME NOT NULL
slot_duration  INTEGER NOT NULL   -- minutes
visit_types    TEXT[]             -- ['in-person','teleconsult']
is_active      BOOLEAN DEFAULT TRUE
```

**Table: `availability_exceptions`**
```
id          UUID PRIMARY KEY
doctor_id   UUID REFERENCES doctor_profiles(id)
date        DATE NOT NULL
reason      VARCHAR(255)    -- "Annual leave", "Conference"
is_blocked  BOOLEAN DEFAULT TRUE
```

**Table: `appointments`**
```
id              UUID PRIMARY KEY
clinic_id       UUID REFERENCES clinics(id)
patient_id      UUID REFERENCES patients(id)
doctor_id       UUID REFERENCES doctor_profiles(id)
scheduled_at    TIMESTAMPTZ NOT NULL
duration_mins   INTEGER NOT NULL DEFAULT 20
visit_type      ENUM('in_person','teleconsult') NOT NULL
status          ENUM('scheduled','confirmed','checked_in','completed','cancelled','no_show') DEFAULT 'scheduled'
room            VARCHAR(50)
cancellation_reason TEXT
booked_by       UUID REFERENCES users(id)
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

**Table: `appointment_status_log`**
```
id             UUID PRIMARY KEY
appointment_id UUID REFERENCES appointments(id)
from_status    VARCHAR(50)
to_status      VARCHAR(50) NOT NULL
changed_by     UUID REFERENCES users(id)
reason         TEXT
changed_at     TIMESTAMPTZ DEFAULT NOW()
```

**Table: `visit_notes`**
```
id             UUID PRIMARY KEY
appointment_id UUID REFERENCES appointments(id) UNIQUE
doctor_id      UUID REFERENCES doctor_profiles(id)
subjective     TEXT   -- patient's complaints
objective      TEXT   -- examination findings
assessment     TEXT   -- diagnosis
plan           TEXT   -- treatment plan
follow_up_in   INTEGER  -- days until follow-up
created_at     TIMESTAMPTZ DEFAULT NOW()
updated_at     TIMESTAMPTZ DEFAULT NOW()
```

**Table: `waitlist`**
```
id          UUID PRIMARY KEY
clinic_id   UUID REFERENCES clinics(id)
patient_id  UUID REFERENCES patients(id)
doctor_id   UUID REFERENCES doctor_profiles(id)
preferred_from DATE
preferred_to   DATE
visit_type  ENUM('in_person','teleconsult')
notified_at TIMESTAMPTZ
created_at  TIMESTAMPTZ DEFAULT NOW()
```

**Table: `slot_holds`** (Redis-backed, but schema here for reference)
```
key:   slot_hold:{doctor_id}:{date}:{time}
value: { patient_id, held_at }
ttl:   300 seconds
```

**Indexes:**
- `appointments(clinic_id, scheduled_at)` — calendar queries
- `appointments(doctor_id, scheduled_at, status)` — doctor's schedule
- `appointments(patient_id)` — patient's appointment history
- `appointments(status, scheduled_at)` — daily ops queries
- `availability_templates(doctor_id, day_of_week)` — slot generation

### API Surface
- `GET    /api/v1/doctors/:id/slots` — available slots for a date range
- `POST   /api/v1/appointments` — book appointment
- `GET    /api/v1/appointments` — list (doctor or patient scoped)
- `GET    /api/v1/appointments/:id` — detail
- `PATCH  /api/v1/appointments/:id/status` — advance status
- `POST   /api/v1/appointments/:id/reschedule` — reschedule to new slot
- `POST   /api/v1/appointments/:id/cancel` — cancel with reason
- `POST   /api/v1/appointments/:id/visit-notes` — submit visit notes
- `GET    /api/v1/appointments/:id/visit-notes` — retrieve visit notes
- `POST   /api/v1/waitlist` — join waitlist
- `DELETE /api/v1/waitlist/:id` — leave waitlist
- `GET    /api/v1/availability-templates/:doctor_id` — get template
- `PUT    /api/v1/availability-templates/:doctor_id` — set template

### Architecture Additions
- `app/services/slot_engine.py` — core slot generation and conflict detection logic
- `app/services/appointment_service.py` — booking, state machine transitions
- `app/core/redis.py` — Redis client, slot hold TTL operations
- `app/utils/calendar.py` — date/time utilities respecting clinic timezone
- Frontend: `components/calendar/WeekView.tsx`, `components/booking/SlotPicker.tsx`

### Event Flow
- `appointment.booked` → triggers confirmation notification (Phase 6)
- `appointment.cancelled` → triggers cancellation notification; checks waitlist
- `appointment.completed` → triggers post-visit follow-up (Phase 6 placeholder)
- `appointment.status_changed` → writes to `appointment_status_log`

### Dependencies
- Phase 2 (clinic, doctor profiles, settings), Phase 3 (patients)

### Definition of Done
- A patient can book an available slot and see it confirmed
- A doctor can view their daily schedule on a calendar
- Double-booking is prevented under concurrent requests (tested with load test)
- All appointment status transitions work and are logged
- Visit notes can be submitted and retrieved
- Waitlist entry is created when no slots are available

### Risks & Considerations
- Slot generation for a 3-month window can produce thousands of records — generate on-demand, not upfront; cache generated slots in Redis with short TTL
- Timezone bugs are the most common silent failure in scheduling systems — all datetimes stored as UTC, all user-facing times converted using clinic timezone in the API response layer
- The slot hold (Redis TTL lock) must be released explicitly on booking failure, not just on expiry — otherwise slots stay locked for 5 minutes after errors

### Future AI Impact
The `slot_engine.py` service becomes the tool the Scheduling Agent calls. Visit notes become the source material the Document Intelligence Agent summarizes and the RAG Agent indexes. The `appointment.completed` event triggers the Follow-up Agent chain. The `waitlist` table enables the Scheduling Agent to auto-notify patients when a slot opens.

---

## Phase 5 — Document Management {#phase-5}

### Goal
Build a structured document storage and retrieval system for lab reports, prescriptions, discharge summaries, imaging reports, and consent forms — with versioning, access control, and patient-doctor sharing.

### Why This Phase Exists
Documents are the other half of the clinical record alongside appointments. Before an AI agent can extract data from a lab report, the report must be stored, versioned, and retrievable in a structured way. The document pipeline built here is the infrastructure the Document Intelligence Agent sits on top of. Building it now as a pure file management system, without any AI, means the AI layer is additive, not foundational.

### Features
- Multi-type document upload: lab reports, prescriptions, imaging, discharge summaries, consent forms
- Upload via clinic staff or patient self-upload
- File storage on S3/Cloudflare R2 with pre-signed URL pattern
- Document versioning (upload a newer version of the same report)
- Document metadata: type, uploaded by, date, tags, associated appointment
- Document access control: patient-owned, doctor-viewable, clinic-admin-viewable
- Document sharing: generate time-limited shareable link
- Document status: `uploaded → processing → reviewed → archived`
- Audit log: who viewed or downloaded each document
- Bulk upload support

### Backend Scope
- Pre-signed upload URL generation (direct browser → S3 upload, no server proxying)
- Post-upload webhook/callback to register document in DB after S3 upload completes
- Document metadata CRUD
- Version management: new upload creates a new version, previous version archived
- Access control enforcement: patient can only see their own documents; doctor can see documents of patients they have appointments with; admin sees all clinic documents
- Signed download URL generation (time-limited, 15 minutes)
- Document audit trail

### Frontend Scope
- Patient portal: upload lab report, view all my documents, download/share
- Doctor view: patient documents tab, preview in-browser (PDF viewer), mark as reviewed
- Staff upload UI: bulk upload for reception, associate with patient and appointment
- Document list: filterable by type, date, status, associated doctor
- Version history drawer: see all versions of a document
- Share link modal: generate link, set expiry, copy to clipboard

### Database Changes

**Table: `documents`**
```
id              UUID PRIMARY KEY
clinic_id       UUID REFERENCES clinics(id)
patient_id      UUID REFERENCES patients(id)
appointment_id  UUID REFERENCES appointments(id)  -- optional
uploaded_by     UUID REFERENCES users(id)
document_type   ENUM('lab_report','prescription','imaging','discharge_summary','consent_form','other')
title           VARCHAR(255) NOT NULL
description     TEXT
storage_key     TEXT NOT NULL    -- S3 object key
file_size_bytes INTEGER
mime_type       VARCHAR(100)
status          ENUM('uploaded','processing','reviewed','archived') DEFAULT 'uploaded'
version         INTEGER DEFAULT 1
parent_doc_id   UUID REFERENCES documents(id)  -- for versioning
tags            TEXT[]
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

**Table: `document_access_log`**
```
id          UUID PRIMARY KEY
document_id UUID REFERENCES documents(id)
accessed_by UUID REFERENCES users(id)
action      ENUM('view','download','share')
ip_address  VARCHAR(45)
accessed_at TIMESTAMPTZ DEFAULT NOW()
```

**Table: `document_share_links`**
```
id          UUID PRIMARY KEY
document_id UUID REFERENCES documents(id)
created_by  UUID REFERENCES users(id)
token       VARCHAR(255) UNIQUE NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
accessed_at TIMESTAMPTZ   -- null until first access
```

**Indexes:**
- `documents(patient_id, document_type)` — patient document list
- `documents(clinic_id, status)` — clinic document queue
- `documents(appointment_id)` — documents for a visit
- `documents(parent_doc_id)` — version chain lookup

### API Surface
- `POST   /api/v1/documents/upload-url` — request pre-signed S3 upload URL
- `POST   /api/v1/documents` — register document after upload completes
- `GET    /api/v1/documents` — list (patient-scoped or clinic-scoped)
- `GET    /api/v1/documents/:id` — document metadata
- `GET    /api/v1/documents/:id/download-url` — generate signed download URL
- `PATCH  /api/v1/documents/:id` — update metadata/status
- `POST   /api/v1/documents/:id/share` — create share link
- `GET    /api/v1/documents/:id/versions` — version history
- `GET    /api/v1/documents/share/:token` — resolve share link (public)

### Architecture Additions
- `app/storage/s3_client.py` — pre-signed URL generation for upload and download
- `app/services/document_service.py` — registration, versioning, access control
- `app/services/share_service.py` — share link lifecycle
- Frontend: PDF in-browser viewer component (react-pdf), document upload dropzone

### Event Flow
- `document.uploaded` → status set to `processing`; triggers Document Intelligence Agent pipeline in Phase 10
- `document.reviewed` → notifies patient that their report has been reviewed
- `document.shared` → audit log entry

### Dependencies
- Phase 1 (auth, access control), Phase 2 (clinics), Phase 3 (patients), Phase 4 (appointments — for associating docs with visits)

### Definition of Done
- Files upload directly to S3 via pre-signed URL without passing through the server
- Documents are listed, versioned, and downloadable
- Access control prevents patients seeing other patients' documents
- Share links expire correctly and log access
- Audit log captures every view and download action

### Risks & Considerations
- Pre-signed URL expiry (15 min for upload) must be communicated to the frontend — if the user takes too long to pick a file, the upload will fail silently
- File type validation must happen both client-side and server-side (validate MIME type after upload, not just file extension)
- Large files (imaging, CT scans) may be 100MB+ — enforce a file size limit per plan tier; implement multipart upload for files > 10MB

### Future AI Impact
The `documents` table with `status = 'uploaded'` is the trigger queue for the Document Intelligence Agent. The `storage_key` is the S3 key the agent downloads for processing. The structured metadata (document type, patient ID, appointment ID) gives the agent context before it even reads the file. Extraction results from the agent are written back as structured fields on this record.

---

## Phase 6 — Notifications & Communication Infrastructure {#phase-6}

### Goal
Build the complete outbound communication infrastructure: email, SMS, and WhatsApp — with template management, delivery tracking, retry logic, and a channel preference system.

### Why This Phase Exists
Every other phase has already emitted events — patient registered, appointment booked, document uploaded — but nothing has consumed them yet. Before building agents that send messages, the messaging infrastructure itself must be reliable, retryable, observable, and template-driven. Agents should not own message delivery; they should invoke a notification service that does.

### Features
- Notification service abstraction: one interface, multiple channels (Email via Sendgrid, SMS via Twilio, WhatsApp via Twilio Business API)
- Patient communication preferences: preferred channel, language, do-not-disturb hours
- Notification templates: parameterized templates per event type and channel
- Template versioning: update a template without breaking in-flight sends
- Delivery tracking: sent, delivered, failed, opened (for email)
- Retry logic: exponential backoff for failed deliveries (3 retries)
- Notification inbox: in-app notification centre for patients and staff
- Opt-out management: patients can unsubscribe from non-critical notifications
- Notification history per patient

### Backend Scope
- `NotificationService` with `send(patient_id, event_type, context)` interface
- Channel router: selects channel based on patient preference and message criticality
- Template engine: Jinja2 templates with variable interpolation per event type and language
- Delivery status webhook handlers (Sendgrid events, Twilio status callbacks)
- Retry queue: failed notifications re-queued with exponential backoff via Redis
- `POST /api/v1/notifications/send` — internal endpoint for other services
- In-app notification storage and mark-as-read

### Frontend Scope
- Patient notification preferences page: channel (SMS/email/WhatsApp), language, DND hours
- Notification inbox (bell icon in nav): unread count badge, list of recent notifications, mark-all-read
- Admin notification dashboard: view delivery status, re-trigger failed sends
- Template management (super admin): view and edit notification templates

### Database Changes

**Table: `notification_preferences`**
```
id                  UUID PRIMARY KEY
patient_id          UUID REFERENCES patients(id) UNIQUE
preferred_channel   ENUM('sms','email','whatsapp') DEFAULT 'sms'
preferred_language  VARCHAR(10) DEFAULT 'en'
dnd_start_time      TIME DEFAULT '22:00'
dnd_end_time        TIME DEFAULT '07:00'
opt_out_marketing   BOOLEAN DEFAULT FALSE
updated_at          TIMESTAMPTZ DEFAULT NOW()
```

**Table: `notification_templates`**
```
id           UUID PRIMARY KEY
event_type   VARCHAR(100) NOT NULL   -- e.g. 'appointment.booked'
channel      ENUM('sms','email','whatsapp')
language     VARCHAR(10) DEFAULT 'en'
subject      TEXT                    -- email only
body         TEXT NOT NULL           -- Jinja2 template
version      INTEGER DEFAULT 1
is_active    BOOLEAN DEFAULT TRUE
created_at   TIMESTAMPTZ DEFAULT NOW()
UNIQUE(event_type, channel, language, version)
```

**Table: `notification_logs`**
```
id              UUID PRIMARY KEY
clinic_id       UUID REFERENCES clinics(id)
patient_id      UUID REFERENCES patients(id)
event_type      VARCHAR(100)
channel         ENUM('sms','email','whatsapp','in_app')
recipient       VARCHAR(255)   -- phone or email
template_id     UUID REFERENCES notification_templates(id)
context         JSONB          -- template variables used
status          ENUM('queued','sent','delivered','failed','opened') DEFAULT 'queued'
provider_msg_id VARCHAR(255)   -- Twilio SID or Sendgrid message ID
error_message   TEXT
attempt_count   INTEGER DEFAULT 0
sent_at         TIMESTAMPTZ
delivered_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT NOW()
```

**Table: `in_app_notifications`**
```
id         UUID PRIMARY KEY
user_id    UUID REFERENCES users(id)
title      VARCHAR(255)
body       TEXT
action_url TEXT
is_read    BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ DEFAULT NOW()
```

**Indexes:**
- `notification_logs(patient_id, created_at DESC)` — patient notification history
- `notification_logs(status, created_at)` — retry queue queries
- `in_app_notifications(user_id, is_read)` — unread count

### API Surface
- `POST   /api/v1/notifications/send` — trigger notification (internal, service-to-service)
- `GET    /api/v1/notifications` — notification history (patient-scoped)
- `GET    /api/v1/notifications/in-app` — in-app inbox
- `PATCH  /api/v1/notifications/in-app/:id/read` — mark as read
- `GET    /api/v1/notifications/preferences` — get patient preferences
- `PATCH  /api/v1/notifications/preferences` — update preferences
- `POST   /api/v1/webhooks/sendgrid` — delivery status callback
- `POST   /api/v1/webhooks/twilio` — SMS/WhatsApp status callback

### Architecture Additions
- `app/services/notification_service.py` — channel abstraction, template rendering, dispatch
- `app/workers/retry_worker.py` — polls Redis retry queue, re-attempts failed sends
- `app/integrations/sendgrid.py` — Sendgrid API wrapper
- `app/integrations/twilio.py` — Twilio SMS + WhatsApp API wrapper
- Webhook signature verification middleware (Twilio + Sendgrid)

### Event Flow
Consumes events produced by all prior phases:
- `patient.registered` → welcome notification
- `appointment.booked` → confirmation notification
- `appointment.cancelled` → cancellation notification
- `appointment.status_changed` (→ `checked_in`) → doctor alert
- `document.reviewed` → patient notification

### Dependencies
- Phase 3 (patients — for preferences), Phase 4 (appointments — for confirmation events), Phase 5 (documents — for review events)

### Definition of Done
- Appointment confirmation SMS and email are sent successfully within 30 seconds of booking
- Failed deliveries retry up to 3 times with backoff
- Delivery status is tracked and visible in the admin dashboard
- DND hours are respected (messages queued, not sent)
- Opt-out is honoured for non-critical messages
- Patient can change their preferred channel and language

### Risks & Considerations
- WhatsApp Business API requires pre-approved message templates — submit templates for approval before building the follow-up agent; approval takes 24–72 hours
- Twilio and Sendgrid have rate limits; implement a send-rate governor for bulk reminder dispatches
- DND window handling must account for clinic timezone, not server timezone

### Future AI Impact
The notification service is the dispatch layer every AI agent uses to communicate with patients. The Follow-up Agent does not send messages directly — it calls `NotificationService.send(patient_id, event_type, context)`. The Response Writer Agent generates the message *content*, but this service handles *delivery*. The delivery logs provide the feedback signal for analytics: did patients who received reminders show up at higher rates?

---

## Phase 7 — Dashboard & Operational Analytics {#phase-7}

### Goal
Build a real-time operational dashboard for clinic admins and doctors showing appointment volume, no-show rates, patient flow, document throughput, and notification delivery metrics — using only data already in the database.

### Why This Phase Exists
Before adding AI-generated insights, there must be human-readable dashboards that surface the raw operational data. This phase proves the data model is correct and complete (if you can't query it for a dashboard, an agent can't reason over it either). It also delivers immediate value to clinic admins without requiring any AI infrastructure.

### Features
- Admin dashboard: total appointments by day/week/month, no-show rate, cancellation rate, new patient registrations, revenue placeholder
- Doctor dashboard: my schedule today, upcoming appointments, pending visit notes, patient load
- Patient dashboard: upcoming appointments, recent documents, active medications reminder
- Date-range filtering on all metrics
- CSV export for appointment and patient reports
- Real-time updates via polling (WebSocket upgrade in Phase 8)

### Backend Scope
- Analytics query layer: pre-built SQL aggregations for each metric
- Materialized views for heavy aggregate queries (refresh every 15 minutes)
- `GET /api/v1/analytics/overview` — clinic-level KPIs
- `GET /api/v1/analytics/appointments` — appointment trends
- `GET /api/v1/analytics/patients` — patient growth and activity
- `GET /api/v1/analytics/staff` — per-doctor metrics
- CSV export endpoint (streams large datasets)

### Frontend Scope
- Admin overview page: stat cards (total patients, appointments today, no-show %, revenue placeholder), line chart (appointments over time), bar chart (appointments by doctor), table (recent cancellations)
- Doctor home page: today's schedule list, completion progress bar, unfinished notes alert
- Patient home page: next appointment card, last visit summary, active medications banner
- Date range picker component
- Export button on all tables

### Database Changes

**Materialized view: `mv_daily_appointment_stats`**
```sql
CREATE MATERIALIZED VIEW mv_daily_appointment_stats AS
SELECT
  clinic_id,
  DATE(scheduled_at AT TIME ZONE 'UTC') AS date,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE status = 'completed') AS completed,
  COUNT(*) FILTER (WHERE status = 'no_show') AS no_shows,
  COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled
FROM appointments
GROUP BY clinic_id, DATE(scheduled_at AT TIME ZONE 'UTC');
```

No new tables in this phase — only views and indexes on existing tables.

**Additional indexes added:**
- `appointments(clinic_id, status, scheduled_at)` — analytics query optimization
- `patients(clinic_id, created_at)` — patient growth queries

### API Surface
- `GET /api/v1/analytics/overview?from=&to=`
- `GET /api/v1/analytics/appointments?from=&to=&doctor_id=`
- `GET /api/v1/analytics/patients?from=&to=`
- `GET /api/v1/analytics/no-show-rate?from=&to=`
- `GET /api/v1/reports/appointments.csv?from=&to=` — CSV export
- `GET /api/v1/reports/patients.csv` — CSV export

### Architecture Additions
- `app/services/analytics_service.py` — query aggregations, date range handling
- Materialized view refresh scheduled every 15 minutes via APScheduler
- Frontend: Recharts components (LineChart, BarChart, StatCard), date range picker
- CSV streaming using FastAPI's `StreamingResponse`

### Event Flow
No new events produced. This phase only reads from existing tables.

### Dependencies
- Phase 2–6 (all domain data must exist to be meaningful to display)

### Definition of Done
- Admin dashboard loads in < 2 seconds for a clinic with 1000+ appointments
- No-show rate and cancellation rate are calculated correctly (verified against raw data)
- Doctor dashboard shows correct today's schedule
- CSV exports download correctly for date ranges up to 1 year
- Materialized views refresh without locking the database

### Risks & Considerations
- Materialized view refresh should be `CONCURRENTLY` to avoid read locks on the analytics tables
- CSV export for large date ranges (1+ years) must stream, not buffer, to avoid memory issues
- All metrics must be clinic-scoped — a query without `WHERE clinic_id = ?` is a data leak

### Future AI Impact
The analytics data established here is what the Analytics Agent in Phase 17 will interpret, narrate, and compare against benchmarks. The `mv_daily_appointment_stats` view becomes the primary input for anomaly detection ("this week's no-show rate is 40% higher than your 3-month average"). The per-doctor metrics enable the system to identify scheduling inefficiencies and suggest optimizations.

---

## Phase 8 — Event-Driven Architecture {#phase-8}

### Goal
Replace the implicit event coupling (direct service calls) with a formal event bus, enabling asynchronous processing, reliable event delivery, and the decoupled architecture that AI agents require to trigger on domain events without being tightly coupled to the web request lifecycle.

### Why This Phase Exists
AI agents cannot run synchronously in a web request. When a document is uploaded, the Document Intelligence Agent may take 30 seconds to process it — that cannot block the HTTP response. When an appointment is booked, the Follow-up Agent needs to schedule reminders minutes later — not as part of the booking API call. An event bus is the prerequisite for all agentic behavior. Building it now, as a SaaS infrastructure concern before agents exist, means agents are consumers of a reliable system, not bolted-on hacks.

### Features
- Message queue infrastructure (Redis Streams or RabbitMQ)
- Event schema registry: typed event definitions for all domain events
- Event producers: domain services emit events to the bus after every state change
- Event consumers: background workers subscribe to event types
- Dead letter queue (DLQ): failed events land here for inspection and replay
- Event replay capability: replay events from a specific timestamp for debugging
- Idempotency keys on all event handlers
- Monitoring: queue depth, consumer lag, DLQ size visible in admin panel

### Backend Scope
- Event bus abstraction: `EventBus.publish(event_type, payload)` used by all services
- Worker process: separate from the API server; runs event consumers in background
- Existing notification triggers (from Phases 4–6) migrated to publish events rather than calling notification service directly
- Idempotency enforcement: each event has a `event_id` (UUID); consumers check if already processed before executing
- DLQ consumer: admin can view, retry, or discard dead-letter events

### Frontend Scope
- Admin panel: Event bus monitoring page — queue depth, recent events, DLQ entries
- Real-time appointment status updates via WebSocket (WebSocket server added here, consuming from event bus)
- Live notification delivery status updates in the admin notification dashboard

### Database Changes

**Table: `event_log`** (audit trail, not the queue itself)
```
id           UUID PRIMARY KEY
event_id     UUID UNIQUE NOT NULL    -- idempotency key
event_type   VARCHAR(100) NOT NULL
payload      JSONB NOT NULL
source       VARCHAR(100)            -- which service produced it
processed_at TIMESTAMPTZ
status       ENUM('published','processed','failed','dead_lettered')
created_at   TIMESTAMPTZ DEFAULT NOW()
```

No new domain tables. This phase is infrastructure-only.

### API Surface
- `GET  /api/v1/admin/events` — recent event log
- `GET  /api/v1/admin/events/dlq` — dead letter queue
- `POST /api/v1/admin/events/dlq/:id/retry` — retry dead-lettered event
- WebSocket: `ws://host/ws/clinic/:clinic_id` — real-time events for the clinic dashboard

### Architecture Additions
```
apps/
└── api/
    ├── app/
    │   ├── events/
    │   │   ├── bus.py           ← EventBus abstraction
    │   │   ├── schemas.py       ← Typed event Pydantic models
    │   │   └── handlers/        ← One file per event type
    │   └── workers/
    │       └── event_worker.py  ← Consumer process entry point
```
- Redis Streams as the queue backend (or RabbitMQ for higher throughput needs)
- `event_worker.py` runs as a separate Docker container/process
- WebSocket manager: `app/core/websocket.py`

### Event Flow (full registry at this point)

All events are now formal typed schemas:

| Event | Producer | Consumers |
|---|---|---|
| `patient.registered` | PatientService | NotificationWorker |
| `appointment.booked` | AppointmentService | NotificationWorker, CalendarWorker |
| `appointment.cancelled` | AppointmentService | NotificationWorker, WaitlistWorker |
| `appointment.completed` | AppointmentService | FollowUpWorker (Phase 13) |
| `document.uploaded` | DocumentService | DocumentIntelligenceWorker (Phase 10) |
| `document.reviewed` | DocumentService | NotificationWorker |
| `visit_notes.created` | AppointmentService | RAGIndexWorker (Phase 12) |

### Dependencies
- All prior phases (Phase 0–7 must be complete — events are retrofitted onto existing services)

### Definition of Done
- All existing service-to-service notification calls migrated to event bus
- Queue depth monitoring is visible in the admin panel
- A dead-lettered event can be retried from the admin UI
- WebSocket delivers real-time appointment status updates to the doctor dashboard
- Event consumer handles duplicate delivery correctly (idempotency confirmed by test)

### Risks & Considerations
- Redis Streams vs RabbitMQ: Redis is simpler and already in the stack; RabbitMQ is more robust for high throughput. Choose Redis for MVP, plan migration path to RabbitMQ if queue depth regularly exceeds 10k messages
- Consumer group semantics must be set correctly in Redis Streams — a message consumed by one worker in a group should not be re-delivered to others
- The event log table will grow large quickly — partition by month and add a retention policy (90 days)

### Future AI Impact
This is the single most important infrastructure phase for AI. Every agent in Phases 10–16 is an event consumer. The Document Intelligence Agent wakes up because `document.uploaded` lands on the bus. The Follow-up Agent schedules reminders because `appointment.completed` fires. The Risk Escalation Agent monitors `document.processed` events for abnormal values. Without this phase, agents would require polling or synchronous invocation — both are architecturally inferior.

---

# AI Phases

> The SaaS platform is now complete. Every agent phase below builds *on top of* a functioning product — it adds intelligence to existing workflows, not infrastructure.

---

## Phase 9 — AI Infrastructure Layer {#phase-9}

### Goal
Set up the shared AI infrastructure: LLM client abstraction, prompt management, token usage tracking, vector database, embedding pipeline, and the agent base class that all subsequent agents inherit from.

### Why This Phase Exists
Individual agents cannot be built reliably without shared infrastructure. Prompt versioning, cost tracking, retry logic for LLM timeouts, and vector store connectivity are cross-cutting concerns. Building them once here prevents five teams solving the same problem five different ways.

### Features
- LLM client abstraction: `LLMClient.complete(prompt, model, config)` with GPT-4o and Claude Sonnet backends, switchable per use case
- Prompt registry: versioned prompts stored in DB or files, not hardcoded in agent code
- Token usage tracking: every LLM call logged with input tokens, output tokens, model, cost estimate
- Pinecone vector store client: namespace-per-clinic design
- Embedding pipeline: text → embedding via OpenAI `text-embedding-3-small`, stored in Pinecone
- Agent base class: `BaseAgent` with `run(context) -> AgentResult`, retry logic, structured output parsing, timeout handling
- AI feature flags: per-clinic toggle to enable/disable agents
- LangGraph setup: graph builder utilities, node templates

### Backend Scope
- `app/ai/llm_client.py` — OpenAI + Anthropic wrapper with retry, timeout, fallback
- `app/ai/prompts/` — prompt files with version tags, loaded at startup
- `app/ai/vector_store.py` — Pinecone client, upsert, query, namespace management
- `app/ai/embeddings.py` — text chunking, embedding generation, batch upsert
- `app/ai/base_agent.py` — abstract base class for all agents
- `app/ai/token_tracker.py` — middleware that logs every LLM call
- `app/ai/tools/` — reusable LangChain tool definitions (shared across agents)

### Database Changes

**Table: `ai_usage_logs`**
```
id            UUID PRIMARY KEY
clinic_id     UUID REFERENCES clinics(id)
agent_name    VARCHAR(100)
model         VARCHAR(100)
input_tokens  INTEGER
output_tokens INTEGER
cost_usd      NUMERIC(10,6)
latency_ms    INTEGER
created_at    TIMESTAMPTZ DEFAULT NOW()
```

**Table: `prompt_registry`**
```
id          UUID PRIMARY KEY
name        VARCHAR(100) NOT NULL
version     INTEGER NOT NULL
content     TEXT NOT NULL
description TEXT
is_active   BOOLEAN DEFAULT TRUE
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE(name, version)
```

**Table: `ai_feature_flags`**
```
clinic_id   UUID REFERENCES clinics(id)
feature     VARCHAR(100)
enabled     BOOLEAN DEFAULT FALSE
config      JSONB
PRIMARY KEY (clinic_id, feature)
```

### Architecture Additions
```
apps/api/app/
└── ai/
    ├── llm_client.py
    ├── base_agent.py
    ├── vector_store.py
    ├── embeddings.py
    ├── token_tracker.py
    ├── prompts/
    │   ├── triage.v1.txt
    │   ├── document_extract.v1.txt
    │   └── rag_answer.v1.txt
    └── tools/
        ├── patient_context.py
        └── slot_lookup.py
```

### Dependencies
- Phase 8 (event bus — agents will be event consumers), all Phase 0–8 complete

### Definition of Done
- `BaseAgent.run()` executes a test prompt, logs token usage, and returns a structured result
- Pinecone namespace for a test clinic is created and a test embedding is queryable
- Token usage is visible per-clinic in the admin panel
- AI feature flags can be toggled per clinic without redeployment
- LangGraph graph builder creates a minimal 2-node graph successfully

---

## Phase 10 — Document Intelligence Agent {#phase-10}

### Goal
Automatically process uploaded lab reports and clinical documents: extract structured data, flag abnormal values, compare with previous reports, and make results queryable and summarized.

### Why This Phase Exists
Document processing is the highest-ROI AI feature because it replaces a purely manual task (doctor reading and interpreting a PDF) with structured, queryable data. It also produces the first concrete AI output the clinic can see and trust — making it the ideal first agent.

### Features
- Triggered by `document.uploaded` event
- PDF text extraction and OCR for scanned documents
- Lab report parsing: extract test name, value, unit, reference range, abnormal flag
- Structured extraction stored in DB (not just a summary)
- Comparison with prior reports: "Your HbA1c was 7.2 in March, now 6.8 — improving"
- Patient-facing summary: plain-language explanation of results
- Doctor-facing summary: clinical highlights and out-of-range flags
- Abnormal value detection: any value outside reference range flagged as alert
- Emits `document.processed` event with structured results

### Backend Scope
- `DocumentIntelligenceAgent(BaseAgent)` consuming `document.uploaded` events
- S3 download → PDF text extraction (pdfplumber) → OCR fallback (Tesseract) if scan
- LLM extraction prompt: structured JSON output of lab values
- Comparison query: fetch previous documents of same type for patient, compute delta
- Structured extraction stored in `document_extractions` table
- Abnormal values written to `lab_alerts` table
- `document.processed` event published with extraction summary

### Frontend Scope
- Document detail page: "AI Extracted Data" tab showing structured lab values table
- Abnormal values highlighted in red with reference ranges shown
- Patient-facing summary in plain language (translated if needed)
- Doctor-facing panel: compare current vs previous results side-by-side
- Processing status indicator: spinner while agent runs

### Database Changes

**Table: `document_extractions`**
```
id            UUID PRIMARY KEY
document_id   UUID REFERENCES documents(id)
agent_version VARCHAR(50)
extraction    JSONB   -- { tests: [{ name, value, unit, ref_range, is_abnormal }] }
summary_patient TEXT
summary_doctor  TEXT
processed_at  TIMESTAMPTZ DEFAULT NOW()
```

**Table: `lab_alerts`**
```
id           UUID PRIMARY KEY
document_id  UUID REFERENCES documents(id)
patient_id   UUID REFERENCES patients(id)
test_name    VARCHAR(255)
value        VARCHAR(100)
unit         VARCHAR(50)
ref_range    VARCHAR(100)
severity     ENUM('mild','moderate','critical')
acknowledged BOOLEAN DEFAULT FALSE
created_at   TIMESTAMPTZ DEFAULT NOW()
```

### Event Flow
- Consumes: `document.uploaded`
- Produces: `document.processed` (with extraction payload), `lab_alert.created` (if abnormal values found)

### Dependencies
- Phase 5 (documents), Phase 9 (AI infrastructure), Phase 8 (event bus)

### Definition of Done
- A lab report PDF uploaded by a patient is processed within 60 seconds
- Structured test values are correctly extracted for 3 test document types
- Abnormal values are flagged with correct severity
- Patient and doctor summaries are generated in plain language
- `lab_alert.created` event fires for critical values (consumed by Risk Escalation Agent in Phase 14)

---

## Phase 11 — Appointment Scheduling Agent {#phase-11}

### Goal
Enable patients to book, reschedule, and check appointment availability through a conversational interface, with the agent handling entity extraction, slot negotiation, and calendar writes via tool calls.

### Features
- Conversational booking: "I need to see a cardiologist next Tuesday afternoon"
- Entity extraction: doctor, specialty, date/time preference, visit type
- Slot querying via tool call to `slot_engine.py`
- Slot negotiation when preferred time is unavailable
- Calendar write via tool call to `appointment_service.py`
- Confirmation generation passed to notification service
- Handles rescheduling and cancellation via natural language
- Waitlist join via conversation

### Event Flow
- Consumes: patient message with booking intent (routed by Triage Agent in Phase 16)
- Produces: `appointment.booked`, `appointment.rescheduled`, `appointment.cancelled`

### Dependencies
- Phase 4 (appointment system), Phase 9 (AI infrastructure)

---

## Phase 12 — Medical Knowledge RAG Agent {#phase-12}

### Goal
Answer patient and doctor questions about clinic policies, treatment protocols, medication instructions, and general medical FAQs using retrieval-augmented generation over an indexed knowledge base.

### Features
- Knowledge base ingestion: clinic uploads PDF protocols, FAQ documents, consent form templates → chunked, embedded, stored in Pinecone under clinic's namespace
- Patient-facing: "How do I prepare for my colonoscopy?", "What should I avoid after my procedure?"
- Doctor-facing: "What is our clinic's protocol for anticoagulation management?"
- Answers cite the source document and page
- Confidence scoring: low-confidence answers escalate to a human
- Knowledge base management UI: upload, view, delete documents from the index

### Event Flow
- Consumes: patient/doctor query with RAG intent (routed by Triage Agent)
- Consumes: `visit_notes.created` → indexes new notes into vector store
- Produces: `rag.answered` with source citations

### Dependencies
- Phase 9 (vector store, embedding pipeline), Phase 5 (document management for ingestion)

---

## Phase 13 — Follow-Up & Reminder Agent {#phase-13}

### Goal
Proactively send personalized reminders and follow-up communications to patients: pre-appointment prep, post-visit care plan summaries, medication reminders, and chronic care check-ins.

### Features
- Pre-appointment reminder (24h before): preparation instructions from visit notes + appointment type
- Post-visit follow-up (2h after): care plan summary from visit notes, next steps
- Medication reminders: generated from active medications list
- Chronic care check-ins: scheduled based on doctor's follow-up instruction in visit notes
- Personalised message generation: patient's name, specific test/medication, not generic
- Multi-language support: detects patient's preferred language from profile
- DND-aware: respects notification preferences from Phase 6
- Snooze capability: patient can delay a reminder via reply

### Event Flow
- Consumes: `appointment.booked` → schedules pre-appointment reminder task
- Consumes: `appointment.completed` → schedules post-visit follow-up task
- Consumes: `visit_notes.created` → parses follow-up instruction, schedules chronic care reminder
- Produces: notification events consumed by Phase 6 notification service

### Dependencies
- Phase 6 (notification service), Phase 9 (AI infrastructure), Phase 8 (event bus)

---

## Phase 14 — Risk Escalation Agent {#phase-14}

### Goal
Monitor patient data streams — lab results, medication changes, missed follow-ups — and automatically escalate to the responsible doctor when risk thresholds are crossed.

### Features
- Critical lab value detection: consumes `lab_alert.created` events from Document Intelligence Agent
- Drug interaction checking: when new medication is added, checks against current med list
- Missed follow-up detection: patient had a "follow up in 2 weeks" note, no appointment booked after 18 days → escalate
- Allergy-prescription conflict: new prescription conflicts with known allergy → immediate alert
- Escalation routing: finds responsible doctor (last visit doctor), sends structured alert
- Escalation acknowledgement: doctor marks alert as reviewed in dashboard
- Severity tiers: advisory → urgent → critical (different notification channels per tier)

### Event Flow
- Consumes: `lab_alert.created`, `medication.added`, `appointment.missed_followup`
- Produces: `escalation.created`, `escalation.acknowledged`

### Dependencies
- Phase 10 (document intelligence — produces lab alerts), Phase 3 (medications, allergies), Phase 9 (AI infrastructure)

---

## Phase 15 — LangGraph Orchestration Layer {#phase-15}

### Goal
Replace the ad-hoc agent invocations with a formal LangGraph-based orchestration layer: stateful multi-step agent graphs, conditional routing, human-in-the-loop pause points, and agent result persistence.

### Features
- LangGraph state graph for each agent workflow
- Triage node: entry point for all patient messages, classifies intent, routes to correct agent subgraph
- Parallel execution: RAG Agent and Scheduling Agent can run concurrently when intent is compound
- Human-in-the-loop: escalations pause the graph and wait for doctor acknowledgement before proceeding
- Agent memory: per-session conversation state persisted in Redis
- Graph execution tracing: every node transition logged with inputs/outputs
- Retry on node failure: LangGraph retry policy per node type

### Architecture Additions
```
apps/api/app/ai/
└── graphs/
    ├── triage_graph.py
    ├── scheduling_graph.py
    ├── document_graph.py
    ├── rag_graph.py
    ├── followup_graph.py
    └── escalation_graph.py
```

### Dependencies
- Phase 10–14 (all agents must exist before orchestrating them)

---

## Phase 16 — Multi-Agent Workflow Automation {#phase-16}

### Goal
Chain agents together into end-to-end automated workflows that span multiple agents, triggered by a single event, with no human intervention required for routine cases.

### Features
- Workflow: Patient uploads lab report → Document Intelligence Agent extracts → Risk Agent checks → if normal: Follow-up Agent schedules routine check-in → Response Writer drafts patient summary; if abnormal: Risk Agent escalates to doctor
- Workflow: Post-visit → Visit notes created → RAG Agent indexes notes → Follow-up Agent generates personalised care plan message → Notification Service delivers
- Workflow: Appointment no-show → event fires → Follow-up Agent sends re-booking prompt → Scheduling Agent offers next 3 slots → patient replies → booking confirmed
- Admin workflow editor: visual representation of active workflow chains (read-only for V1)

### Dependencies
- Phase 15 (LangGraph orchestration), all agent phases (Phase 10–14)

---

## Phase 17 — Advanced Analytics & Insights {#phase-17}

### Goal
Layer AI-generated narrative insights on top of the operational analytics from Phase 7: anomaly detection, trend interpretation, benchmark comparisons, and weekly clinic health reports.

### Features
- Weekly clinic health report: auto-generated PDF summarizing the week's operational metrics with AI narrative ("No-show rate spiked 35% on Wednesdays — consider SMS reminders 2h before appointment")
- Anomaly detection: flags when a metric deviates significantly from the rolling 4-week average
- Per-doctor performance insights: completion rate, average visit duration, follow-up compliance
- Patient cohort analysis: chronic condition patients with missed check-ins, at-risk segments
- Predictive no-show score: per appointment, based on historical patient behaviour
- Natural language query interface: clinic admin types "show me no-show rate for Dr. Mehta last month" → SQL generated and executed

### Dependencies
- Phase 7 (analytics foundation), Phase 9 (AI infrastructure), all prior phases for rich data

---

## Cross-Cutting Concerns {#cross-cutting}

These are not phases but must be addressed throughout the build:

**Security:** All API routes are authenticated. All data is clinic-scoped. PII is encrypted at rest (AES-256 on S3, TDE on PostgreSQL). TLS everywhere. HIPAA/DPDPA compliance checklist reviewed at Phase 5 completion.

**Audit Trail:** Every create/update/delete on patient records, documents, and appointments writes an audit log entry with `user_id`, `action`, `timestamp`, `diff`.

**Rate Limiting:** Auth endpoints (Phase 1), notification sends (Phase 6), LLM calls (Phase 9) all have per-IP and per-user rate limits.

**Testing Strategy:** Unit tests for services and utilities; integration tests for API endpoints; E2E tests for critical user journeys (booking, document upload, auth flow). Target 70%+ coverage before any AI phase begins.

**Observability:** Structured JSON logs from day 1 (Phase 0). APM with Sentry (error tracking). Uptime monitoring. AI phases add LLM latency tracking and agent success rate dashboards.

---

## Full Tech Stack Summary {#tech-stack}

| Layer | Technology |
|---|---|
| Frontend framework | Next.js 14 (App Router) |
| UI components | Tailwind CSS + shadcn/ui |
| Backend framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 (Supabase or self-hosted) |
| Cache / Queue | Redis 7 (Redis Streams for events) |
| File storage | AWS S3 / Cloudflare R2 |
| Authentication | Clerk or custom JWT (Phase 1) |
| Email | Sendgrid |
| SMS / WhatsApp | Twilio |
| Calendar | Google Calendar API |
| LLM — reasoning | OpenAI GPT-4o |
| LLM — documents | Anthropic Claude Sonnet |
| Embeddings | OpenAI text-embedding-3-small |
| Vector database | Pinecone |
| Agent orchestration | LangGraph |
| Agent framework | LangChain |
| PDF processing | pdfplumber + Tesseract (OCR) |
| Background workers | APScheduler + Redis Streams |
| Deployment — frontend | Vercel |
| Deployment — backend | Railway / AWS ECS |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Monitoring | Sentry + Structlog |
| Payments (future) | Stripe |

---

## Project Timeline Estimate {#timeline}

| Phase | Estimated Duration |
|---|---|
| Phase 0 — Foundation | 3–4 days |
| Phase 1 — Auth | 5–7 days |
| Phase 2 — Clinic Management | 5–7 days |
| Phase 3 — Patient Management | 7–10 days |
| Phase 4 — Appointment Management | 10–14 days |
| Phase 5 — Document Management | 5–7 days |
| Phase 6 — Notifications | 5–7 days |
| Phase 7 — Analytics Dashboard | 4–5 days |
| Phase 8 — Event-Driven Architecture | 5–7 days |
| **SaaS Foundation Total** | **~7–9 weeks** |
| Phase 9 — AI Infrastructure | 4–5 days |
| Phase 10 — Document Intelligence | 7–10 days |
| Phase 11 — Scheduling Agent | 5–7 days |
| Phase 12 — RAG Agent | 7–10 days |
| Phase 13 — Follow-Up Agent | 5–7 days |
| Phase 14 — Risk Escalation | 5–7 days |
| Phase 15 — LangGraph Orchestration | 7–10 days |
| Phase 16 — Workflow Automation | 5–7 days |
| Phase 17 — Advanced Analytics | 5–7 days |
| **AI Layer Total** | **~7–9 weeks** |
| **Total Project Estimate** | **~14–18 weeks** |

*Estimates assume a solo developer or 2-person team. Parallel frontend/backend work can compress the SaaS phases by 20–30%.*

---

*Helixops AI — Product Roadmap v1.0*
*Architecture: SaaS-first, AI-augmented*
