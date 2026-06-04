# HelixOps (Pre-AI Version)

Think of HelixOps initially as:

```text
A Clinic Management Platform
```

NOT

```text
An AI Platform
```

yet.

---

# Primary Roles

We will have 4 roles.

```text
Super Admin
Clinic Admin
Doctor
Patient
```

---

# 1. Super Admin

This is YOU.

The SaaS owner.

---

## What can Super Admin do?

### Manage Clinics

```text
Create Clinic
Edit Clinic
Deactivate Clinic
View Clinics
```

Example:

```text
Apollo Clinic
Fortis Clinic
MedCare Clinic
```

all onboarded through HelixOps.

---

### Manage Plans

```text
Free
Pro
Enterprise
```

---

### Platform Analytics

```text
Total Clinics
Total Patients
Total Appointments
Total Doctors
```

---

### Manage Users

```text
Suspend User
Activate User
Reset User
```

---

### Dashboard

```text
Total Clinics: 12

Total Patients: 24,000

Appointments Today: 600

Active Doctors: 80
```

---

# 2. Clinic Admin

This is the hospital manager.

Not a doctor.

---

## What can Clinic Admin do?

### Manage Doctors

```text
Add Doctor
Remove Doctor
Update Doctor
```

Example:

```text
Dr. Sharma
Cardiologist

Dr. Patel
Dermatologist
```

---

### Manage Staff

```text
Receptionist
Nurse
Operations Staff
```

---

### Manage Patients

```text
Register Patient
Edit Patient
View Patient
```

---

### Manage Appointments

```text
Book
Cancel
Reschedule
```

---

### View Documents

```text
Lab Reports
Prescriptions
Medical Documents
```

---

### Clinic Dashboard

```text
Today's Appointments

New Patients

No Shows

Pending Documents
```

---

# 3. Doctor

This is the most important user.

Most workflows revolve around doctors.

---

# Doctor Dashboard

When doctor logs in:

```text
Upcoming Appointments
Today's Patients
Pending Reports
Recent Documents
```

---

## Doctor can view

### Patients

```text
Patient Profile
History
Medications
Allergies
```

---

Example:

```text
John Doe

Allergy:
Penicillin

Medication:
Metformin

Condition:
Diabetes
```

---

### Appointments

Doctor sees:

```text
10:00 AM - John

10:30 AM - Alice

11:00 AM - Mike
```

---

### Visit Notes

After consultation:

```text
Symptoms

Diagnosis

Treatment Plan

Follow Up
```

stored.

---

### Documents

Doctor can open:

```text
Blood Test

MRI

Prescription

Discharge Summary
```

---

# Doctor Workflow

```text
Patient books appointment
        ↓
Doctor sees schedule
        ↓
Consultation happens
        ↓
Doctor writes notes
        ↓
Patient record updated
```

---

# 4. Patient

Patient is the consumer.

---

# Patient Dashboard

When patient logs in:

```text
Upcoming Appointment

Recent Documents

Medical History

Notifications
```

---

# Patient can

### Manage Profile

```text
Name
Phone
Address
Emergency Contact
```

---

### View Medical History

```text
Conditions

Medications

Allergies
```

---

### Book Appointment

Patient chooses:

```text
Clinic
Doctor
Date
Time
```

---

Appointment gets created.

---

### Upload Documents

Example:

```text
Blood Report

Prescription

MRI Scan
```

---

### View Documents

Patient can access:

```text
Old Reports

Prescriptions

Doctor Notes
```

---

### Notifications

Patient receives:

```text
Appointment Confirmed

Appointment Cancelled

Report Reviewed
```

---

# Core Relationships

This is where the entire system becomes clear.

---

## Clinic owns

```text
Doctors

Patients

Appointments

Documents
```

---

## Doctor manages

```text
Appointments

Visit Notes

Patients
```

---

## Patient owns

```text
Medical History

Documents

Appointments
```

---

# Real Flow Example

Let's follow one patient.

---

## Step 1

Patient registers.

```text
Patient
  ↓
Account Created
```

---

## Step 2

Books appointment.

```text
Patient
  ↓
Doctor
  ↓
Date
  ↓
Time
```

creates:

```text
Appointment
```

---

## Step 3

Doctor sees appointment.

```text
Doctor Dashboard
       ↓
Upcoming Appointments
```

---

## Step 4

Consultation happens.

Doctor writes:

```text
Diagnosis

Medication

Follow Up
```

creates:

```text
Visit Note
```

---

## Step 5

Patient uploads blood report.

```text
PDF Uploaded
```

creates:

```text
Document
```

---

## Step 6

Doctor reviews report.

```text
Document Status

Uploaded
    ↓
Reviewed
```

---

## Step 7

Patient sees updated information.

```text
Appointments

Documents

Medical History
```

---

# Database Relationships (Mental Model)

```text
Clinic
│
├── Doctors
│
├── Patients
│
├── Appointments
│
└── Documents


Patient
│
├── Medical History
├── Medications
├── Allergies
├── Documents
└── Appointments


Doctor
│
├── Appointments
├── Visit Notes
└── Patients


Appointment
│
├── Patient
├── Doctor
└── Visit Note


Document
│
├── Patient
├── Appointment (optional)
└── Doctor Review
```

---

# Where AI Fits Later

After all this exists:

```text
Patient uploads report
       ↓
Document Agent

Patient asks question
       ↓
RAG Agent

Patient wants appointment
       ↓
Scheduling Agent

Critical report
       ↓
Risk Agent

Appointment completed
       ↓
Follow-up Agent
```

Notice something important:

**Every AI agent depends on entities that already exist.**

That's why building the SaaS foundation first is the correct approach.

---