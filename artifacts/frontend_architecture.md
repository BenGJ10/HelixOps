# HelixOps Frontend Design System & Architecture Specification

Before generating any frontend code, read all documents inside the `artifacts/` directory and understand:

* Product Vision
* Role Flows
* User Workflows
* SaaS Foundation Roadmap
* System Architecture
* Database Design
* Future AI Vision

The frontend must be designed to support both the current SaaS platform and future AI-powered workflows.

Do NOT generate generic admin dashboards.

Do NOT generate template-looking healthcare portals.

Do NOT use default shadcn examples without customization.

The goal is to create a premium SaaS experience that feels closer to:

* Silna Health
* Stripe
* Linear
* Vercel

than traditional hospital management software.

---

# Design Philosophy

HelixOps should feel:

* Professional
* Modern
* Trustworthy
* Healthcare-focused
* Operationally efficient
* Executive-grade

Avoid:

* Bootstrap-style dashboards
* Heavy borders everywhere
* Overcrowded screens
* Excessive colors
* Legacy EMR aesthetics
* Generic SaaS templates

The interface should emphasize:

* Clarity
* Whitespace
* Typography
* Information hierarchy
* Fast navigation

---

# Design System

## Brand Personality

HelixOps is:

* Premium Healthcare SaaS
* AI-native Operations Platform
* Modern Clinic Infrastructure

The visual language should communicate:

Trust + Intelligence + Efficiency

---

## Color System

Primary

```css
#2E103D
```

Deep Plum

---

Secondary

```css
#6D28D9
```

Royal Violet

---

Accent

```css
#D8B4FE
```

Soft Lavender

---

Background

```css
#FAFAFC
```

---

Card

```css
#FFFFFF
```

---

Border

```css
#EAEAF0
```

---

Success

```css
#10B981
```

---

Warning

```css
#F59E0B
```

---

Danger

```css
#EF4444
```

---

## Typography

Marketing Pages

Use:

* DM Serif Display

For:

* Hero Headlines
* Landing Page Sections
* Marketing Copy

Example:

"Operational Intelligence for Modern Clinics"

---

Application UI

Use:

* Geist

For:

* Navigation
* Tables
* Forms
* Dashboards
* Settings

---

## Spacing System

Use an 8px spacing grid.

Examples:

8px
16px
24px
32px
48px
64px

Avoid random spacing values.

---

## Border Radius

Use:

```css
16px
```

as the primary radius.

Cards should feel modern and soft.

---

## Shadows

Very subtle.

Avoid heavy dashboard shadows.

Prefer:

* Low blur
* Low opacity
* Layered depth

---

# Frontend Architecture

Use Next.js App Router.

Structure:

```text
src/
├── app/
├── components/
│   ├── layout/
│   ├── dashboard/
│   ├── forms/
│   ├── tables/
│   ├── charts/
│   ├── patients/
│   ├── appointments/
│   ├── documents/
│   └── ui/
├── features/
│   ├── auth/
│   ├── clinics/
│   ├── patients/
│   ├── appointments/
│   ├── documents/
│   ├── notifications/
│   └── analytics/
├── hooks/
├── services/
├── stores/
├── lib/
├── types/
└── providers/
```

Organize by feature/domain.

Avoid dumping everything into components/.

---

# Layout Architecture

## Public Marketing Site

Routes:

```text
/
 /features
 /pricing
 /about
```

Characteristics:

* Large typography
* Generous whitespace
* Premium visuals
* Soft gradients
* Healthcare-focused messaging

---

## Auth Layout

Routes:

```text
/login
/register
/forgot-password
```

Characteristics:

* Centered forms
* Clean branding
* Minimal distractions

---

## Application Layout

Routes:

```text
/dashboard
/patients
/appointments
/documents
/notifications
/settings
```

Characteristics:

* Persistent sidebar
* Top navigation
* Breadcrumbs
* Global search
* Notification center

---

# Role-Based Experiences

Design separate navigation experiences for:

## Super Admin

Focus:

* Clinics
* Users
* Subscriptions
* Platform Analytics

---

## Clinic Admin

Focus:

* Doctors
* Staff
* Patients
* Appointments
* Documents

---

## Doctor

Focus:

* Today's Schedule
* Patients
* Visit Notes
* Reports

---

## Patient

Focus:

* Appointments
* Medical History
* Documents
* Notifications

---

# Dashboard Design Requirements

Every dashboard should contain:

* KPI Cards
* Recent Activity
* Quick Actions
* Status Indicators

Avoid empty dashboards.

Every screen should answer:

"What should this user do next?"

---

# Tables

All data tables must support:

* Search
* Sorting
* Pagination
* Filtering
* Empty States
* Loading States

---

# Forms

All forms must include:

* Validation
* Error Handling
* Success Feedback
* Loading States

---

# UX Requirements

Every page must define:

* Loading State
* Error State
* Empty State
* Success State

No page should exist without them.

---

# Final Objective

Build a frontend experience that feels like a modern healthcare SaaS platform used by real clinics.

The product should look polished enough that a recruiter, engineer, startup founder, or healthcare administrator could reasonably believe it is a commercial product rather than a student project.

---