# Software Architecture Document (SAD)

## HR Training Request Module (`hr_training_request`)

---

| **Document Title** | Software Architecture Document — HR Training Request Module |
| :--- | :--- |
| **Project** | `hr_training_request` — Custom Odoo Module |
| **Platform** | Odoo 17 / 18 Community |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Relates To** | SRS v1.0.0 — HR Training Request Module |
| **Date** | 2026-07-25 |

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Scope](#12-scope)
   - 1.3 [Definitions, Acronyms & Abbreviations](#13-definitions-acronyms--abbreviations)
   - 1.4 [References](#14-references)
2. [Architectural Goals & Constraints](#2-architectural-goals--constraints)
   - 2.1 [Architectural Goals](#21-architectural-goals)
   - 2.2 [Architectural Constraints](#22-architectural-constraints)
3. [System Context](#3-system-context)
   - 3.1 [System Context Diagram](#31-system-context-diagram)
   - 3.2 [External Interfaces](#32-external-interfaces)
4. [Architectural Overview](#4-architectural-overview)
   - 4.1 [Odoo Layered Architecture](#41-odoo-layered-architecture)
   - 4.2 [Module Position in the Ecosystem](#42-module-position-in-the-ecosystem)
5. [Module Decomposition](#5-module-decomposition)
   - 5.1 [Component Overview](#51-component-overview)
   - 5.2 [Models Layer](#52-models-layer)
   - 5.3 [Security Layer](#53-security-layer)
   - 5.4 [Views Layer](#54-views-layer)
   - 5.5 [Data Layer](#55-data-layer)
6. [Data Architecture](#6-data-architecture)
   - 6.1 [Entity-Relationship Diagram](#61-entity-relationship-diagram)
   - 6.2 [Database Table Schema](#62-database-table-schema)
   - 6.3 [Data Flow](#63-data-flow)
7. [Security Architecture](#7-security-architecture)
   - 7.1 [Defense-in-Depth Strategy](#71-defense-in-depth-strategy)
   - 7.2 [Security Group Hierarchy](#72-security-group-hierarchy)
   - 7.3 [Access Control Layers](#73-access-control-layers)
   - 7.4 [Record Rule Architecture](#74-record-rule-architecture)
   - 7.5 [Field-Level Security](#75-field-level-security)
8. [State Machine Architecture](#8-state-machine-architecture)
   - 8.1 [State Diagram](#81-state-diagram)
   - 8.2 [Guard Pattern Design](#82-guard-pattern-design)
   - 8.3 [Transition Method Signatures](#83-transition-method-signatures)
9. [View Architecture](#9-view-architecture)
   - 9.1 [View Rendering Pipeline](#91-view-rendering-pipeline)
   - 9.2 [Form View Architecture](#92-form-view-architecture)
   - 9.3 [List View Architecture](#93-list-view-architecture)
   - 9.4 [Search View Architecture](#94-search-view-architecture)
   - 9.5 [Menu & Action Architecture](#95-menu--action-architecture)
10. [Component Interaction & Sequence Diagrams](#10-component-interaction--sequence-diagrams)
    - 10.1 [Submit Request Flow](#101-submit-request-flow)
    - 10.2 [Manager Approval Flow](#102-manager-approval-flow)
    - 10.3 [HR Final Approval Flow](#103-hr-final-approval-flow)
11. [Employee Extension Architecture](#11-employee-extension-architecture)
12. [Key Architectural Decisions (ADRs)](#12-key-architectural-decisions-adrs)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Traceability Matrix](#14-traceability-matrix)

---

## 1. Introduction

### 1.1 Purpose

This Software Architecture Document (SAD) describes the technical architecture of the `hr_training_request` Odoo custom module. It translates the requirements captured in the SRS into concrete architectural decisions, component designs, data structures, and interaction patterns.

This document is intended for:
- The developer implementing the module
- Code reviewers and technical evaluators
- Future maintainers who need to understand architectural intent

### 1.2 Scope

This SAD covers the complete internal architecture of the `hr_training_request` module, including:
- All Python model components and their responsibilities
- Security architecture across multiple enforcement layers
- State machine design and guard pattern
- View decomposition and role-aware rendering
- Database schema and data relationships
- Component interaction and request flows

### 1.3 Definitions, Acronyms & Abbreviations

| Term | Definition |
| :--- | :--- |
| **SAD** | Software Architecture Document |
| **SRS** | Software Requirements Specification |
| **ADR** | Architectural Decision Record |
| **ORM** | Object-Relational Mapping — Odoo's model abstraction over PostgreSQL |
| **ACL** | Access Control List — model-level CRUD rights (`ir.model.access.csv`) |
| **RLS** | Row-Level Security — achieved via `ir.rule` domain filters |
| **FSM** | Finite State Machine — the `state` field lifecycle |
| **DID** | Defense-in-Depth — layered security strategy |
| **M2O** | Many2one — Odoo relational field type |
| **QWeb** | Odoo's XML-based template engine used for view rendering |
| **XML-RPC / JSON-RPC** | External API protocols Odoo exposes; security must hold here too |
| **`ir.rule`** | Odoo model for row-level record rules |
| **`ir.model.access`** | Odoo model for model-level CRUD permissions |
| **`mail.thread`** | Odoo mixin providing chatter, followers, and tracking |

### 1.4 References

| Document | Description |
| :--- | :--- |
| SRS v1.0.0 | Software Requirements Specification — HR Training Request Module |
| Odoo 17/18 Developer Docs | https://www.odoo.com/documentation/17.0/developer/ |
| Odoo Security Guide | `ir.model.access`, `ir.rule`, `groups` attribute documentation |
| IEEE 1471 / ISO/IEC 42010 | Software Architecture Description standards |

---

## 2. Architectural Goals & Constraints

### 2.1 Architectural Goals

| ID | Goal | Priority |
| :--- | :--- | :--- |
| AG-01 | **Security correctness over feature breadth** — a smaller, correctly secured module is preferred over a large feature-rich one with access holes | Critical |
| AG-02 | **Defense-in-depth** — security enforced at every layer: record rules, ACL, Python guards, and XML UI | Critical |
| AG-03 | **Idiomatic Odoo** — follow standard Odoo ORM patterns, conventions, and naming | High |
| AG-04 | **Immutable state machine** — no illegal state transitions possible via any interface (UI, API, shell) | Critical |
| AG-05 | **Non-invasive extension** — extend `hr.employee` without modifying or breaking core HR module | High |
| AG-06 | **Testability** — demo data and clean guard methods enable automated or manual workflow verification | Medium |
| AG-07 | **Maintainability** — clear separation of concerns, no dead code, clean commit history | Medium |

### 2.2 Architectural Constraints

| ID | Constraint | Source |
| :--- | :--- | :--- |
| AC-01 | Must run on Odoo 17 or 18 Community Edition | SRS CON-01 |
| AC-02 | No `sudo()` without inline justification comment | SRS CON-02 |
| AC-03 | Python-level enforcement mandatory for all state guards | SRS CON-03 |
| AC-04 | `ir.rule` required for row-level security — ACL alone is insufficient | SRS CON-04 |
| AC-05 | `hr.employee` extended via inheritance only — no full view replacement | SRS CON-05 |
| AC-06 | Module must be self-contained with demo data | SRS CON-06 |
| AC-07 | Standard Odoo module file structure required | SRS NFR-MNT-01..05 |

---

## 3. System Context

### 3.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ODOO INSTANCE                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Odoo Web Client                        │   │
│  │           (QWeb / JavaScript / OWL Framework)            │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │ HTTP / JSON-RPC                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │                  Odoo Server (Python)                     │   │
│  │                                                           │   │
│  │   ┌─────────────┐    ┌──────────────────────────────┐    │   │
│  │   │  hr module  │◄───│   hr_training_request        │    │   │
│  │   │  (core)     │    │   (this module)               │    │   │
│  │   └─────────────┘    └──────────────────────────────┘    │   │
│  │                                                           │   │
│  │   ┌─────────────────────────────────────────────────┐    │   │
│  │   │          Odoo ORM / Security Framework           │    │   │
│  │   │  (ir.model.access, ir.rule, groups, sudo)        │    │   │
│  │   └─────────────────────────────────────────────────┘    │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │ SQL / psycopg2                       │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │                   PostgreSQL Database                     │   │
│  │         (hr_training_request, hr_employee tables)        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

External Actors:
  [Employee User]         ──► Web Browser ──► Odoo Web Client
  [Manager User]          ──► Web Browser ──► Odoo Web Client
  [HR Approver User]      ──► Web Browser ──► Odoo Web Client
  [Admin / Developer]     ──► XML-RPC / JSON-RPC / ORM Shell
```

### 3.2 External Interfaces

| Interface | Protocol | Direction | Notes |
| :--- | :--- | :--- | :--- |
| End-user browser | HTTP/HTTPS + JSON-RPC | Bidirectional | Primary user interaction channel |
| Odoo XML-RPC API | XML-RPC over HTTP | Bidirectional | External integrations; security guards must hold here too |
| Odoo shell (`odoo-bin shell`) | Direct ORM calls | Inbound | Developer/admin shell; Python guards must hold here too |
| PostgreSQL | TCP/IP + psycopg2 | Bidirectional | Internal only; never exposed directly |
| `hr` core module | Odoo internal import | Inbound dependency | `hr.employee`, `hr.employee` views inherited |

---

## 4. Architectural Overview

### 4.1 Odoo Layered Architecture

The module follows Odoo's standard three-tier architecture:

```
┌──────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│                                                              │
│  ┌────────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐  │
│  │ Form View  │  │ List View │  │Search View│  │  Menu  │  │
│  │ (QWeb XML) │  │ (QWeb XML)│  │ (QWeb XML)│  │ Action │  │
│  └────────────┘  └───────────┘  └───────────┘  └────────┘  │
│         Role-based visibility / attrs / groups               │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              hr.training.request (Model)             │   │
│  │                                                       │   │
│  │  action_submit()       ◄── Guard: owner + draft      │   │
│  │  action_manager_approve() ◄── Guard: manager group   │   │
│  │  action_hr_approve()   ◄── Guard: HR group           │   │
│  │  action_reject()       ◄── Guard: role + state       │   │
│  │  action_cancel()       ◄── Guard: owner + state      │   │
│  │  _check_dates()        ◄── @api.constrains           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              hr.employee (Extended Model)            │   │
│  │                                                       │   │
│  │  training_request_count (computed, read_group)       │   │
│  │  action_open_training_requests()                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│         Odoo ORM Security: ACL + Record Rules applied        │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                     DATA LAYER                               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               PostgreSQL Database                    │   │
│  │                                                       │   │
│  │  hr_training_request  ──────────► hr_employee        │   │
│  │  (employee_id FK)                                    │   │
│  │  (manager_id related)                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│         ir.rule filters applied at SQL query level           │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Module Position in the Ecosystem

```
odoo/addons/
  ├── base/            (Odoo core — res.users, ir.rule, ir.model.access)
  ├── hr/              (hr.employee, hr.department — DEPENDENCY)
  ├── mail/            (mail.thread, mail.activity.mixin — OPTIONAL DEPENDENCY)
  └── hr_training_request/   ◄── THIS MODULE
```

**Dependency Chain:**
- `base` → always present
- `hr` → required dependency (declared in `__manifest__.py`)
- `mail` → optional; add to `depends` only if chatter is implemented

---

## 5. Module Decomposition

### 5.1 Component Overview

```
hr_training_request/
│
├── [COMPONENT: Manifest]
│   └── __manifest__.py
│
├── [COMPONENT: Models]
│   ├── models/__init__.py
│   ├── models/hr_training_request.py     ← Primary business model
│   └── models/hr_employee.py             ← Extension of core model
│
├── [COMPONENT: Security]
│   ├── security/groups.xml               ← Group definitions
│   ├── security/ir.model.access.csv      ← Model-level ACL
│   └── security/ir_rules.xml             ← Row-level record rules
│
├── [COMPONENT: Views]
│   ├── views/hr_training_request_views.xml  ← Form + List + Search
│   ├── views/hr_employee_views.xml          ← Smart button inheritance
│   └── views/menus.xml                      ← Menu items + window actions
│
└── [COMPONENT: Demo Data]
    └── data/demo_data.xml                ← Test users, employees, requests
```

### 5.2 Models Layer

#### 5.2.1 `hr_training_request.py` — Responsibilities

| Responsibility | Implementation |
| :--- | :--- |
| Define all fields of `hr.training.request` | `fields.*` declarations |
| Enforce state transition guards | `action_*()` methods with role/state checks |
| Validate business rules | `@api.constrains` on `start_date`, `end_date`, `cost` |
| Compute `manager_id` from employee | `related='employee_id.parent_id'` |
| Default `employee_id` to current user's employee | `default=lambda self: self.env.user.employee_id` |

#### 5.2.2 `hr_employee.py` — Responsibilities

| Responsibility | Implementation |
| :--- | :--- |
| Add `training_request_count` computed field | `@api.depends` + `read_group()` query |
| Provide action to open training requests | `action_open_training_requests()` method returning `ir.actions.act_window` |

### 5.3 Security Layer

Three files, each with a distinct security responsibility:

| File | Responsibility | Odoo Model |
| :--- | :--- | :--- |
| `groups.xml` | Define the three security groups and their hierarchy | `res.groups` |
| `ir.model.access.csv` | Grant model-level CRUD rights per group | `ir.model.access` |
| `ir_rules.xml` | Define row-level record filters per group | `ir.rule` |

### 5.4 Views Layer

| File | Views Contained | Purpose |
| :--- | :--- | :--- |
| `hr_training_request_views.xml` | Form, List (Tree), Search | Primary UI for the new model |
| `hr_employee_views.xml` | Inherited `hr.employee` form | Add smart button via `<xpath>` |
| `menus.xml` | `ir.ui.menu` + `ir.actions.act_window` | Navigation, default filters per role |

### 5.5 Data Layer

| File | Contents |
| :--- | :--- |
| `data/demo_data.xml` | 3 `res.users` (employee/manager/HR), 3 `hr.employee` records with correct `parent_id` links, sample `hr.training.request` records in various states |

---

## 6. Data Architecture

### 6.1 Entity-Relationship Diagram

```
┌─────────────────────┐          ┌────────────────────────────┐
│     res.users       │          │       hr.employee          │
│─────────────────────│          │────────────────────────────│
│ id (PK)             │ 1      * │ id (PK)                    │
│ name                │◄─────────│ user_id (FK → res.users)   │
│ login               │          │ name                       │
│ password            │          │ parent_id (FK → self)      │◄──┐
│ groups_id (M2M)     │          │ department_id              │   │ (manager)
└─────────────────────┘          │ training_request_count     │   │
                                 │   (computed)               │───┘
                                 └──────────┬─────────────────┘
                                            │ 1
                                            │ employee_id (FK)
                                            │ *
                                 ┌──────────▼─────────────────┐
                                 │   hr.training.request      │
                                 │────────────────────────────│
                                 │ id (PK)                    │
                                 │ employee_id (FK)           │
                                 │ manager_id (related/FK)    │
                                 │ course_name (Char)         │
                                 │ training_provider (Char)   │
                                 │ start_date (Date)          │
                                 │ end_date (Date)            │
                                 │ cost (Float)               │
                                 │ justification (Text)       │
                                 │ state (Selection)          │
                                 │ hr_notes (Text)            │
                                 └────────────────────────────┘
```

### 6.2 Database Table Schema

**Table: `hr_training_request`** (auto-generated by Odoo ORM)

| Column | PostgreSQL Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | PRIMARY KEY | Auto-increment |
| `employee_id` | `INTEGER` | NOT NULL, FK → `hr_employee.id` | Requesting employee |
| `manager_id` | `INTEGER` | FK → `hr_employee.id` | Stored related field |
| `course_name` | `VARCHAR` | NOT NULL | Required field |
| `training_provider` | `VARCHAR` | NULLABLE | Optional |
| `start_date` | `DATE` | NULLABLE | |
| `end_date` | `DATE` | NULLABLE | |
| `cost` | `DOUBLE PRECISION` | NULLABLE | |
| `justification` | `TEXT` | NULLABLE | |
| `state` | `VARCHAR` | NOT NULL, DEFAULT `'draft'` | Selection field |
| `hr_notes` | `TEXT` | NULLABLE | HR-only; no DB-level restriction (enforced at ORM/view level) |
| `create_uid` | `INTEGER` | FK → `res_users.id` | Odoo standard audit field |
| `create_date` | `TIMESTAMP` | | Odoo standard audit field |
| `write_uid` | `INTEGER` | FK → `res_users.id` | Odoo standard audit field |
| `write_date` | `TIMESTAMP` | | Odoo standard audit field |

> **Note on `hr_notes`:** PostgreSQL has no column-level access control. Restriction of this field to HR Approvers is enforced entirely at the Odoo ORM/view layer — `groups=` attribute in XML and field-level group check in model.

### 6.3 Data Flow

```
Employee Browser              Odoo Server                 PostgreSQL
      │                           │                            │
      │  POST /web/dataset/call_kw│                            │
      │──────────────────────────►│                            │
      │                           │  1. ACL check              │
      │                           │     (ir.model.access)      │
      │                           │  2. Record Rule filter     │
      │                           │     (ir.rule → SQL WHERE)  │
      │                           │──────────────────────────►│
      │                           │  SELECT * FROM             │
      │                           │  hr_training_request       │
      │                           │  WHERE employee_id.user_id │
      │                           │  = current_user            │
      │                           │◄──────────────────────────│
      │                           │  3. Field-level group check│
      │                           │     (hr_notes hidden)      │
      │◄──────────────────────────│                            │
      │  JSON response (filtered) │                            │
```

---

## 7. Security Architecture

### 7.1 Defense-in-Depth Strategy

The module implements security at **four distinct layers**, each independently capable of blocking unauthorized access:

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 4: UI / Presentation Layer                          │
│  ─ XML attrs (invisible/readonly based on state/role)      │
│  ─ groups= attribute hides buttons and fields              │
│  ─ Purpose: UX convenience only — NOT enforcement          │
├────────────────────────────────────────────────────────────┤
│  LAYER 3: Python Business Logic Layer (ENFORCEMENT)        │
│  ─ action_*() methods check state + user role/ownership    │
│  ─ @api.constrains validates business rules                │
│  ─ Raises UserError / AccessError / ValidationError        │
│  ─ Purpose: TRUE enforcement — applies to all channels     │
├────────────────────────────────────────────────────────────┤
│  LAYER 2: ORM / ACL Layer                                  │
│  ─ ir.model.access.csv: CRUD rights per group              │
│  ─ Field-level groups= on hr_notes field                   │
│  ─ Purpose: Coarse-grained model access control            │
├────────────────────────────────────────────────────────────┤
│  LAYER 1: Database / Record Rule Layer (ENFORCEMENT)       │
│  ─ ir.rule: SQL WHERE clause injected per user/group       │
│  ─ Purpose: Row-level data isolation — applies to ALL      │
│    queries including XML-RPC, JSON-RPC, ORM shell          │
└────────────────────────────────────────────────────────────┘
```

### 7.2 Security Group Hierarchy

```
res.groups
  └── hr.group_hr_user  (base Odoo HR group)
        └── group_training_requester  (Training Requester)
              └── group_training_manager  (Training Manager Approver)
                    └── group_training_hr  (Training HR Approver)
```

**Inheritance semantics:**
- `group_training_hr` inherits all permissions of `group_training_manager`
- `group_training_manager` inherits all permissions of `group_training_requester`
- Each level **adds** capabilities; none remove capabilities from the parent

**Group definitions in `security/groups.xml`:**

```xml
<record id="group_training_requester" model="res.groups">
    <field name="name">Training Requester</field>
    <field name="category_id" ref="base.module_category_human_resources"/>
    <field name="implied_ids" eval="[(4, ref('hr.group_hr_user'))]"/>
</record>

<record id="group_training_manager" model="res.groups">
    <field name="name">Training Manager Approver</field>
    <field name="category_id" ref="base.module_category_human_resources"/>
    <field name="implied_ids" eval="[(4, ref('group_training_requester'))]"/>
</record>

<record id="group_training_hr" model="res.groups">
    <field name="name">Training HR Approver</field>
    <field name="category_id" ref="base.module_category_human_resources"/>
    <field name="implied_ids" eval="[(4, ref('group_training_manager'))]"/>
</record>
```

### 7.3 Access Control Layers

**`security/ir.model.access.csv`:**

```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_training_request_requester,training.request.requester,model_hr_training_request,group_training_requester,1,1,1,0
access_training_request_manager,training.request.manager,model_hr_training_request,group_training_manager,1,1,1,0
access_training_request_hr,training.request.hr,model_hr_training_request,group_training_hr,1,1,1,1
```

### 7.4 Record Rule Architecture

**`security/ir_rules.xml` — Three rules, one per group:**

```xml
<!-- Rule 1: Requesters see only their own records -->
<record id="rule_training_request_requester" model="ir.rule">
    <field name="name">Training Request: Requester sees own</field>
    <field name="model_id" ref="model_hr_training_request"/>
    <field name="groups" eval="[(4, ref('group_training_requester'))]"/>
    <field name="domain_force">
        [('employee_id.user_id', '=', user.id)]
    </field>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- Rule 2: Managers see own + direct reports -->
<record id="rule_training_request_manager" model="ir.rule">
    <field name="name">Training Request: Manager sees team</field>
    <field name="model_id" ref="model_hr_training_request"/>
    <field name="groups" eval="[(4, ref('group_training_manager'))]"/>
    <field name="domain_force">
        ['|',
            ('employee_id.user_id', '=', user.id),
            ('employee_id.parent_id.user_id', '=', user.id)
        ]
    </field>
</record>

<!-- Rule 3: HR Approvers see all -->
<record id="rule_training_request_hr" model="ir.rule">
    <field name="name">Training Request: HR sees all</field>
    <field name="model_id" ref="model_hr_training_request"/>
    <field name="groups" eval="[(4, ref('group_training_hr'))]"/>
    <field name="domain_force">[(1, '=', 1)]</field>
</record>
```

> **Critical:** These rules are **not global** — they are group-scoped. When a user belongs to a higher group, the most permissive matching rule applies (Odoo ORs rules within the same model for the same user).

### 7.5 Field-Level Security

The `hr_notes` field is restricted using Odoo's `groups` attribute on the field definition:

```python
hr_notes = fields.Text(
    string='HR Notes',
    groups='hr_training_request.group_training_hr',
)
```

This causes the ORM to:
1. **Exclude** the field from `fields_get()` responses for non-HR users
2. **Raise `AccessError`** on any direct read/write attempt by non-HR users
3. **Strip** the field from any RPC response automatically

---

## 8. State Machine Architecture

### 8.1 State Diagram

```
                              ┌─────────────────────────────────────┐
                              │      FINITE STATE MACHINE           │
                              │      hr.training.request            │
                              └─────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │   ┌─────────┐  action_submit()         ┌─────────────┐          │
    │   │  DRAFT  │─────────────────────────►│  SUBMITTED  │          │
    │   └─────────┘  [Guard: owner, dates,   └─────────────┘          │
    │        │        cost ≥ 0]               │           │            │
    │        │                         Approve│           │Reject      │
    │        │ action_cancel()          [mgr] │           │[mgr]       │
    │        ▼                               ▼           ▼            │
    │   ┌───────────┐              ┌──────────────────┐  ┌──────────┐ │
    │   │ CANCELLED │◄─────────── │ MANAGER_APPROVED  │  │ REJECTED │ │
    │   └───────────┘  (from sub) └──────────────────┘  └──────────┘ │
    │   (terminal)                  │            │       (terminal)   │
    │                         Final │            │Reject              │
    │                        Approve│[HR]        │[HR]                │
    │                               ▼            ▼                    │
    │                        ┌─────────────┐  ┌──────────┐           │
    │                        │ HR_APPROVED │  │ REJECTED │           │
    │                        └─────────────┘  └──────────┘           │
    │                        (terminal)        (terminal)             │
    └──────────────────────────────────────────────────────────────────┘

    Terminal States: DRAFT→CANCELLED, SUBMITTED→CANCELLED,
                     SUBMITTED→REJECTED, MANAGER_APPROVED→REJECTED,
                     MANAGER_APPROVED→HR_APPROVED
```

### 8.2 Guard Pattern Design

Every transition method follows a **consistent four-step guard pattern**:

```
Step 1: State Pre-condition Check
  → Is the record in the expected source state?
  → If not: raise UserError

Step 2: Actor Authorization Check
  → Does the calling user have the right role or relationship?
  → If not: raise AccessError

Step 3: Business Rule Validation
  → Are all business constraints satisfied? (dates, cost)
  → If not: raise ValidationError

Step 4: State Transition Execution
  → Write the new state value
  → Log change if mail.thread is active
```

**Implementation example — `action_submit`:**

```python
def action_submit(self):
    """
    Transition: draft → submitted
    Actor: Request owner (employee)
    Guards: state=draft, owner check, date validation, cost >= 0
    """
    for rec in self:
        # Step 1: State pre-condition
        if rec.state != 'draft':
            raise UserError(_(
                "Only draft requests can be submitted. "
                "Current state: %s") % rec.state)

        # Step 2: Actor authorization
        if rec.employee_id.user_id != self.env.user:
            raise AccessError(_(
                "Only the request owner can submit this request."))

        # Step 3: Business rule validation
        if rec.end_date and rec.start_date:
            if rec.end_date <= rec.start_date:
                raise ValidationError(_(
                    "End date must be after start date."))
        if rec.cost is not None and rec.cost < 0:
            raise ValidationError(_(
                "Training cost cannot be negative."))

        # Step 4: Execute transition
        rec.state = 'submitted'
```

### 8.3 Transition Method Signatures

| Method | Transition | Actor Check | State Pre-condition |
| :--- | :--- | :--- | :--- |
| `action_submit()` | `draft` → `submitted` | `employee_id.user_id == env.user` | `state == 'draft'` |
| `action_cancel()` | `draft/submitted` → `cancelled` | `employee_id.user_id == env.user` | `state in ('draft', 'submitted')` |
| `action_manager_approve()` | `submitted` → `manager_approved` | `env.user in group_training_manager` OR `manager_id.user_id == env.user` | `state == 'submitted'` |
| `action_manager_reject()` | `submitted` → `rejected` | Same as manager_approve | `state == 'submitted'` |
| `action_hr_approve()` | `manager_approved` → `hr_approved` | `env.user in group_training_hr` | `state == 'manager_approved'` |
| `action_hr_reject()` | `manager_approved` → `rejected` | `env.user in group_training_hr` | `state == 'manager_approved'` |

---

## 9. View Architecture

### 9.1 View Rendering Pipeline

```
Browser Request
     │
     ▼
ir.actions.act_window (domain + context pre-filtered per role)
     │
     ▼
ir.ui.view (QWeb XML template)
     │
     ├─ groups= attributes filtered by user's groups (server-side)
     ├─ attrs invisible/readonly evaluated against record state
     └─ field widget rendering (statusbar, badge, many2one, etc.)
     │
     ▼
Rendered HTML + JSON response → Browser
```

### 9.2 Form View Architecture

```xml
<!-- Structural outline: view_hr_training_request_form -->
<form string="Training Request">
    <header>
        <!-- State bar -->
        <field name="state" widget="statusbar"
               statusbar_visible="draft,submitted,manager_approved,hr_approved"/>

        <!-- Buttons: shown based on state + role (attrs + groups) -->
        <button name="action_submit"     string="Submit"
                attrs="{'invisible': [('state','!=','draft')]}"
                groups="group_training_requester"/>

        <button name="action_cancel"     string="Cancel"
                attrs="{'invisible': [('state','not in',['draft','submitted'])]}"
                groups="group_training_requester"/>

        <button name="action_manager_approve" string="Approve"
                attrs="{'invisible': [('state','!=','submitted')]}"
                groups="group_training_manager"/>

        <button name="action_manager_reject"  string="Reject"
                attrs="{'invisible': [('state','!=','submitted')]}"
                groups="group_training_manager"/>

        <button name="action_hr_approve"  string="Final Approve"
                attrs="{'invisible': [('state','!=','manager_approved')]}"
                groups="group_training_hr"/>

        <button name="action_hr_reject"   string="Reject"
                attrs="{'invisible': [('state','!=','manager_approved')]}"
                groups="group_training_hr"/>
    </header>

    <sheet>
        <group>
            <!-- Core fields -->
            <field name="employee_id"/>
            <field name="manager_id" readonly="1"/>
            <field name="course_name"/>
            <field name="training_provider"/>
            <field name="start_date"/>
            <field name="end_date"/>

            <!-- cost + justification: editable only in draft -->
            <field name="cost"
                   attrs="{'readonly': [('state','!=','draft')]}"/>
            <field name="justification"
                   attrs="{'readonly': [('state','!=','draft')]}"/>
        </group>

        <notebook>
            <!-- HR Notes tab: only visible to HR Approver group -->
            <page string="HR Notes" groups="group_training_hr">
                <field name="hr_notes"/>
            </page>
        </notebook>
    </sheet>

    <!-- Optional: chatter (if mail.thread) -->
    <div class="oe_chatter">
        <field name="message_follower_ids"/>
        <field name="message_ids"/>
    </div>
</form>
```

### 9.3 List View Architecture

```xml
<!-- view_hr_training_request_tree -->
<tree string="Training Requests"
      decoration-muted="state in ('draft','cancelled')"
      decoration-info="state == 'submitted'"
      decoration-warning="state == 'manager_approved'"
      decoration-success="state == 'hr_approved'"
      decoration-danger="state == 'rejected'">

    <field name="employee_id"/>
    <field name="course_name"/>
    <field name="training_provider"/>
    <field name="start_date"/>
    <field name="end_date"/>
    <field name="cost"/>
    <field name="state" widget="badge"
           decoration-info="state == 'submitted'"
           decoration-warning="state == 'manager_approved'"
           decoration-success="state == 'hr_approved'"
           decoration-danger="state == 'rejected'"/>
</tree>
```

### 9.4 Search View Architecture

```xml
<!-- view_hr_training_request_search -->
<search string="Search Training Requests">
    <!-- Searchable fields -->
    <field name="employee_id"/>
    <field name="course_name"/>

    <!-- State filters -->
    <filter string="Draft"            name="filter_draft"
            domain="[('state','=','draft')]"/>
    <filter string="Submitted"        name="filter_submitted"
            domain="[('state','=','submitted')]"/>
    <filter string="Manager Approved" name="filter_mgr_approved"
            domain="[('state','=','manager_approved')]"/>
    <filter string="HR Approved"      name="filter_hr_approved"
            domain="[('state','=','hr_approved')]"/>
    <filter string="Rejected"         name="filter_rejected"
            domain="[('state','=','rejected')]"/>
    <filter string="Cancelled"        name="filter_cancelled"
            domain="[('state','=','cancelled')]"/>

    <separator/>

    <!-- User-context filters -->
    <filter string="My Requests"      name="filter_my_requests"
            domain="[('employee_id.user_id','=',uid)]"/>
    <filter string="My Team"          name="filter_my_team"
            domain="[('employee_id.parent_id.user_id','=',uid)]"
            groups="group_training_manager"/>

    <!-- Group by options -->
    <group expand="0" string="Group By">
        <filter string="Employee"     name="groupby_employee"
                context="{'group_by':'employee_id'}"/>
        <filter string="State"        name="groupby_state"
                context="{'group_by':'state'}"/>
    </group>
</search>
```

### 9.5 Menu & Action Architecture

```
ir.ui.menu: Training (top-level or under HR)
  │
  ├── ir.actions.act_window: My Requests
  │     domain: [('employee_id.user_id','=',uid)]
  │     groups: group_training_requester
  │
  ├── ir.actions.act_window: Pending Manager Approval
  │     domain: [('state','=','submitted')]
  │     search_default_filter_my_team: 1
  │     groups: group_training_manager
  │
  ├── ir.actions.act_window: Pending HR Approval
  │     domain: [('state','=','manager_approved')]
  │     groups: group_training_hr
  │
  └── ir.actions.act_window: All Requests
        domain: []  (no restriction — RLS handles it)
        groups: group_training_hr
```

---

## 10. Component Interaction & Sequence Diagrams

### 10.1 Submit Request Flow

```
Employee Browser       Odoo Server              PostgreSQL
      │                    │                        │
      │─── Click "Submit" ─►│                        │
      │                    │                        │
      │                    ├─ ACL check ────────────►│
      │                    │  (can user write?)      │
      │                    │◄───────────────── OK ───│
      │                    │                        │
      │                    ├─ Record Rule check ────►│
      │                    │  (owns this record?)   │
      │                    │◄───────────────── OK ──│
      │                    │                        │
      │                    ├─ action_submit():       │
      │                    │   ✓ state == 'draft'   │
      │                    │   ✓ owner == env.user  │
      │                    │   ✓ end_date > start_date
      │                    │   ✓ cost >= 0          │
      │                    │                        │
      │                    ├─ UPDATE hr_training_request
      │                    │  SET state='submitted' ─►│
      │                    │◄───────────────── OK ───│
      │                    │                        │
      │◄─────── Success ───│                        │
      │   (state bar updates)                       │
```

### 10.2 Manager Approval Flow

```
Manager Browser        Odoo Server              PostgreSQL
      │                    │                        │
      │── Click "Approve" ─►│                        │
      │                    │                        │
      │                    ├─ ACL check             │
      │                    ├─ Record Rule check     │
      │                    │  (employee.parent_id   │
      │                    │   .user_id == mgr?)    │
      │                    │                        │
      │                    ├─ action_manager_approve():
      │                    │   ✓ state == 'submitted'
      │                    │   ✓ user in group_training_manager
      │                    │     OR manager_id.user_id == user
      │                    │                        │
      │                    ├─ UPDATE state='manager_approved'
      │                    │─────────────────────►  │
      │◄─────── Success ───│                        │
```

### 10.3 HR Final Approval Flow

```
HR Browser             Odoo Server              PostgreSQL
      │                    │                        │
      │─ Click "Final      │                        │
      │   Approve" ────────►│                        │
      │                    ├─ ACL check             │
      │                    ├─ Record Rule: hr_all   │
      │                    │  [(1,'=',1)] → sees all│
      │                    │                        │
      │                    ├─ action_hr_approve():  │
      │                    │   ✓ state == 'manager_approved'
      │                    │   ✓ user in group_training_hr
      │                    │                        │
      │                    ├─ UPDATE state='hr_approved'
      │                    │─────────────────────►  │
      │◄─────── Success ───│                        │
```

---

## 11. Employee Extension Architecture

### 11.1 Extension Strategy

The `hr.employee` model is extended using Odoo's standard `_inherit` mechanism — no core files are modified.

```python
# models/hr_employee.py
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    training_request_count = fields.Integer(
        string='Training Requests',
        compute='_compute_training_request_count',
    )

    def _compute_training_request_count(self):
        # Efficient: single read_group query
        data = self.env['hr.training.request'].read_group(
            domain=[('employee_id', 'in', self.ids)],
            fields=['employee_id'],
            groupby=['employee_id'],
        )
        count_map = {d['employee_id'][0]: d['employee_id_count'] for d in data}
        for emp in self:
            emp.training_request_count = count_map.get(emp.id, 0)

    def action_open_training_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Training Requests',
            'res_model': 'hr.training.request',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            # Record rules further filter what the viewer can see
        }
```

### 11.2 Smart Button XML (Inherited View)

```xml
<!-- views/hr_employee_views.xml -->
<record id="view_hr_employee_training_button" model="ir.ui.view">
    <field name="name">hr.employee.training.button</field>
    <field name="model">hr.employee</field>
    <field name="inherit_id" ref="hr.view_employee_form"/>
    <field name="arch" type="xml">
        <xpath expr="//div[@name='button_box']" position="inside">
            <button class="oe_stat_button"
                    type="object"
                    name="action_open_training_requests"
                    icon="fa-graduation-cap"
                    groups="hr_training_request.group_training_requester">
                <field name="training_request_count"
                       widget="statinfo"
                       string="Training Requests"/>
            </button>
        </xpath>
    </field>
</record>
```

> **Design decision:** `read_group` is used instead of `search_count` in a loop to avoid N+1 queries when multiple employee records are loaded simultaneously (e.g., in employee list with smart button visible).

---

## 12. Key Architectural Decisions (ADRs)

### ADR-01: Selection Field State Machine vs. `mail.thread` Stages

| | |
| :--- | :--- |
| **Decision** | Use a plain `state` Selection field with guarded button methods as the primary state machine |
| **Rationale** | Simpler, more explicit, and easier to guard against illegal transitions. `mail.thread` is additive (for chatter logging) — not the state machine itself |
| **Alternatives Considered** | `mail.activity.mixin`, `base.automation`, Kanban stage model |
| **Tradeoff** | Less flexible stage ordering, but more secure and predictable |
| **SRS Reference** | SRS §3.3, NFR-SEC-05 |

### ADR-02: Three-Group Inheritance Hierarchy

| | |
| :--- | :--- |
| **Decision** | Training Requester → Manager → HR Approver, each group inheriting from the one below |
| **Rationale** | Cumulative permissions via `implied_ids` — HR always has all manager capabilities. Simplifies group management. |
| **Alternatives Considered** | Flat three groups with no inheritance; separate category-level groups |
| **Tradeoff** | HR inherits Submit/Cancel buttons (not wanted in UX) — mitigated by XML `attrs` visibility and Python guard checking ownership |
| **SRS Reference** | SRS §3.2.1 |

### ADR-03: Python Guards as Primary Security Enforcement

| | |
| :--- | :--- |
| **Decision** | All security enforcement lives in Python action methods; XML `groups`/`attrs` is UI-only |
| **Rationale** | XML is client-rendered and bypassable via direct RPC calls. Python `action_*()` methods are server-side and apply to all access channels (UI, XML-RPC, JSON-RPC, shell) |
| **Alternatives Considered** | Relying solely on XML `groups=` attribute |
| **Tradeoff** | More code; but the only secure approach |
| **SRS Reference** | SRS CON-03, NFR-SEC-01, NFR-SEC-05 |

### ADR-04: `read_group` for `training_request_count`

| | |
| :--- | :--- |
| **Decision** | Use `read_group()` aggregation query for the computed count field on `hr.employee` |
| **Rationale** | A single SQL `GROUP BY` is orders of magnitude more efficient than iterating `search_count()` per employee record |
| **Alternatives Considered** | `search_count()` per employee in a loop |
| **Tradeoff** | Slightly more complex compute method code |
| **SRS Reference** | SRS NFR-PERF-01 |

### ADR-05: `hr_notes` Field-Level Group Restriction

| | |
| :--- | :--- |
| **Decision** | Use `groups='hr_training_request.group_training_hr'` directly on the `fields.Text` definition |
| **Rationale** | Odoo ORM natively handles field exclusion from `fields_get()`, RPC responses, and raises `AccessError` on direct access — no extra Python code needed |
| **Alternatives Considered** | Custom `read()` override to strip the field; separate model for HR notes |
| **Tradeoff** | None — this is the idiomatic Odoo approach |
| **SRS Reference** | SRS §3.4.1 FV-05, NFR-SEC-04 |

### ADR-06: Non-Global Record Rules Per Group

| | |
| :--- | :--- |
| **Decision** | Each `ir.rule` is scoped to its specific group (not `global=True`) |
| **Rationale** | Global rules apply to ALL users. Group-scoped rules allow Odoo to OR rules for a user's groups, letting higher-permission groups see more data without conflicting with lower-group rules |
| **Alternatives Considered** | One global rule with complex domain logic |
| **Tradeoff** | Three rule records instead of one — clearer and more maintainable |
| **SRS Reference** | SRS §3.2.3 |

---

## 13. Deployment Architecture

### 13.1 Module Installation Sequence

```
1. Place hr_training_request/ in Odoo addons path
2. Restart Odoo server (or update apps list)
3. Install module via Settings → Apps → "HR Training Request"

Odoo install process:
  a. Load __manifest__.py
  b. Execute data files in order:
     - security/groups.xml          (create res.groups records)
     - security/ir.model.access.csv (create ir.model.access records)
     - security/ir_rules.xml        (create ir.rule records)
     - views/*.xml                  (register ir.ui.view records)
     - views/menus.xml              (register ir.ui.menu + ir.actions records)
  c. If demo mode: execute data/demo_data.xml
  d. Run any _init() or post_init_hook() if defined
```

### 13.2 Deployment Stack

```
┌─────────────────────────────────────────────────────┐
│            Production Environment                   │
│                                                     │
│  ┌────────────┐    ┌──────────────────────────┐     │
│  │   Nginx    │    │   Odoo Server (Python)   │     │
│  │ (Reverse   │───►│   Port 8069              │     │
│  │  Proxy)    │    │   + hr_training_request  │     │
│  └────────────┘    └──────────────────────────┘     │
│                               │                     │
│                    ┌──────────▼──────────┐           │
│                    │    PostgreSQL        │           │
│                    │    Port 5432        │           │
│                    └─────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### 13.3 `__manifest__.py` Data Load Order

The `data` key in `__manifest__.py` controls the exact installation order. **Order matters** — groups must be created before ACL which references them:

```python
'data': [
    'security/groups.xml',           # 1st: groups must exist for ACL
    'security/ir.model.access.csv',  # 2nd: references groups
    'security/ir_rules.xml',         # 3rd: references groups + model
    'views/hr_training_request_views.xml',
    'views/hr_employee_views.xml',
    'views/menus.xml',               # Last: references views + groups
],
```

---

## 14. Traceability Matrix

| SRS Requirement | SAD Section | Component | Implementation |
| :--- | :--- | :--- | :--- |
| F-01 (create/submit/cancel) | §8.2, §8.3 | `hr_training_request.py` | `action_submit()`, `action_cancel()` |
| F-02 (manager approval) | §8.3 | `hr_training_request.py` | `action_manager_approve()`, `action_manager_reject()` |
| F-03 (HR approval) | §8.3 | `hr_training_request.py` | `action_hr_approve()`, `action_hr_reject()` |
| F-04 (rejection) | §8.3 | `hr_training_request.py` | `action_*_reject()` |
| F-05 (role-based field visibility) | §9.2 | `hr_training_request_views.xml` | `attrs readonly`, `groups=` |
| F-06 (record visibility) | §7.4 | `ir_rules.xml` | `ir.rule` domain filters |
| F-07 (business validation) | §8.2 | `hr_training_request.py` | `@api.constrains`, guard step 3 |
| F-08 (smart button) | §11 | `hr_employee.py`, `hr_employee_views.xml` | `training_request_count`, `<button>` |
| F-09 (contextual filters) | §9.5 | `menus.xml` | `ir.actions.act_window` domain/context |
| F-10 (HR notes) | §7.5, §9.2 | `hr_training_request.py`, `views.xml` | `groups=` on field + XML page |
| NFR-SEC-01 | §7.1, §8.2 | `hr_training_request.py` | Python method guards (Layer 3) |
| NFR-SEC-02 | §7.4 | `ir_rules.xml` | `ir.rule` SQL WHERE injection |
| NFR-SEC-03 | §7.1 | All Python files | Documented `sudo()` usage policy |
| NFR-SEC-04 | §7.5 | `hr_training_request.py` | `groups=` on `hr_notes` field |
| NFR-SEC-05 | §8.2 | `hr_training_request.py` | Guard pattern applied to all channels |
| NFR-PERF-01 | §11.1 | `hr_employee.py` | `read_group()` compute |
| NFR-COMP-02/03 | §11.2 | `hr_employee_views.xml` | `inherit_id` + `<xpath>` only |
| CON-02 | §7.1, ADR-03 | All Python files | No undocumented `sudo()` |
| CON-03 | §7.1, §8.2 | `hr_training_request.py` | Python guards mandatory |
| CON-04 | §7.4 | `ir_rules.xml` | `ir.rule` in addition to ACL |
| CON-05 | §11.2 | `hr_employee_views.xml` | `inherit_id` + `<xpath>` |

---

*End of Software Architecture Document*

---

**Document Version History**

| Version | Date | Author | Notes |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-07-25 | — | Initial SAD derived from SRS v1.0.0 and assignment specification |
