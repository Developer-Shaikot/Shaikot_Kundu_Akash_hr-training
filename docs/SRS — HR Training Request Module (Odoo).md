# Software Requirements Specification (SRS)

## HR Training Request Module (`hr_training_request`)

---

| **Document Title**   | Software Requirements Specification — HR Training Request Module |
| :------------------- | :--------------------------------------------------------------- |
| **Project**          | `hr_training_request` — Custom Odoo Module                       |
| **Platform**         | Odoo 17 / 18 Community                                           |
| **Version**          | 1.0.0                                                            |
| **Status**           | Draft                                                            |
| **Prepared For**     | Mid-Level Software Engineer (Odoo) Assignment                    |
| **Date**             | 2026-07-25                                                       |

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Scope](#12-scope)
   - 1.3 [Definitions, Acronyms & Abbreviations](#13-definitions-acronyms--abbreviations)
   - 1.4 [References](#14-references)
   - 1.5 [Overview](#15-overview)
2. [Overall Description](#2-overall-description)
   - 2.1 [Product Perspective](#21-product-perspective)
   - 2.2 [Product Functions Summary](#22-product-functions-summary)
   - 2.3 [User Classes and Characteristics](#23-user-classes-and-characteristics)
   - 2.4 [Operating Environment](#24-operating-environment)
   - 2.5 [Design and Implementation Constraints](#25-design-and-implementation-constraints)
   - 2.6 [Assumptions and Dependencies](#26-assumptions-and-dependencies)
3. [System Features (Functional Requirements)](#3-system-features-functional-requirements)
   - 3.1 [Data Model — `hr.training.request`](#31-data-model--hrtrainingrequest)
   - 3.2 [Security Groups & Record Rules](#32-security-groups--record-rules)
   - 3.3 [State Machine & Workflow Transitions](#33-state-machine--workflow-transitions)
   - 3.4 [Views & User Interface](#34-views--user-interface)
   - 3.5 [Employee Extension — `hr.employee`](#35-employee-extension--hremployee)
4. [Non-Functional Requirements](#4-non-functional-requirements)
   - 4.1 [Security](#41-security)
   - 4.2 [Performance](#42-performance)
   - 4.3 [Maintainability & Code Quality](#43-maintainability--code-quality)
   - 4.4 [Usability](#44-usability)
   - 4.5 [Compatibility](#45-compatibility)
5. [Technical Architecture & Module Structure](#5-technical-architecture--module-structure)
6. [Workflow & State Diagram](#6-workflow--state-diagram)
7. [Role-Based Access Matrix](#7-role-based-access-matrix)
8. [Validation Rules](#8-validation-rules)
9. [Deliverables](#9-deliverables)
10. [Evaluation Criteria](#10-evaluation-criteria)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document describes the complete functional and non-functional requirements for the `hr_training_request` custom Odoo module. The purpose of this module is to enable employees to formally request external training or certification, and to route those requests through a structured, role-gated multi-stage approval workflow involving their line manager and an HR approver.

This document is intended for:
- The developer assigned to build the module
- Reviewers and evaluators assessing the implementation
- Any future maintainers of the codebase

### 1.2 Scope

The `hr_training_request` module will be built as a standalone Odoo add-on that:

- Introduces a new model `hr.training.request` for managing training requests
- Extends the existing `hr.employee` model with a computed count field and a smart button
- Defines three new security groups with appropriate record-level access rules
- Implements a multi-step approval workflow (draft → submitted → manager approved → HR approved) with guarded state transitions
- Provides role-aware form, list, and search views
- Includes demo data for immediate testing post-installation

**Out of Scope:**
- Integration with external LMS (Learning Management Systems)
- Budget tracking beyond a simple cost field
- Email notifications or scheduled jobs (unless optionally using `mail.thread`)
- Mobile-specific UI layouts
- Multi-currency support (standard Odoo monetary field behavior applies)

### 1.3 Definitions, Acronyms & Abbreviations

| Term | Definition |
| :--- | :--- |
| **SRS** | Software Requirements Specification |
| **ORM** | Object-Relational Mapping (Odoo's model layer) |
| **HR** | Human Resources |
| **Requester** | An employee who submits a training request |
| **Manager Approver** | A user who can approve/reject requests at the `submitted` stage |
| **HR Approver** | A user who gives final approval/rejection at the `manager_approved` stage |
| **Record Rule** | Odoo's row-level security filter (`ir.rule`) applied per user/group |
| **ACL** | Access Control List (`ir.model.access.csv`) — model-level CRUD permissions |
| **State** | The current lifecycle stage of a training request |
| **Smart Button** | An Odoo UI element (stat button) in a form view that shows a count and links to related records |
| **`sudo()`** | Odoo ORM method that bypasses access checks — usage must be explicitly justified |
| **Chatter / `mail.thread`** | Odoo's internal messaging/logging mixin that tracks field changes and allows internal notes |

### 1.4 References

- [Odoo 17 Developer Documentation](https://www.odoo.com/documentation/17.0/developer/)
- [Odoo 18 Developer Documentation](https://www.odoo.com/documentation/18.0/developer/)
- Mid-Level Software Engineer (Odoo) — Assignment Specification (source document)
- Odoo Security Guide: `ir.model.access`, `ir.rule`, `groups` attribute

### 1.5 Overview

The remainder of this document is organized as follows:
- **Section 2** provides an overall description of the product context and constraints.
- **Section 3** details all functional requirements (features).
- **Section 4** defines non-functional requirements.
- **Section 5** specifies the expected module file structure.
- **Section 6** illustrates the full workflow state diagram.
- **Section 7** presents the role-based access matrix.
- **Section 8** documents all validation rules.
- **Section 9** lists required deliverables.
- **Section 10** outlines the evaluation criteria used for assessment.

---

## 2. Overall Description

### 2.1 Product Perspective

`hr_training_request` is a custom add-on module that integrates directly within the existing Odoo HR application ecosystem. It depends on the standard `hr` module and optionally `mail` (for chatter support). It does not replace or fundamentally alter any core HR functionality — it extends it through standard Odoo inheritance mechanisms.

```
Odoo Core
  └── hr (base HR module)
        └── hr_training_request (this module)
              ├── Extends: hr.employee
              └── Introduces: hr.training.request
```

### 2.2 Product Functions Summary

| # | Function |
| :- | :--- |
| F-01 | Allow employees to create, edit, submit, and cancel training requests |
| F-02 | Route requests through a manager approval stage |
| F-03 | Route approved requests through a final HR approval stage |
| F-04 | Allow managers and HR to reject requests at their respective stages |
| F-05 | Enforce role-based field visibility and editability at each stage |
| F-06 | Restrict record visibility via row-level record rules per user role |
| F-07 | Validate business rules before state transitions (dates, cost) |
| F-08 | Display training request count on the `hr.employee` form via a smart button |
| F-09 | Provide contextual default filters per role in the list view |
| F-10 | Expose HR-only notes field invisible to Requesters and Managers |

### 2.3 User Classes and Characteristics

#### 2.3.1 Training Requester (Employee)

- **Description:** Any employee of the company who wishes to request external training or a certification
- **Technical proficiency:** Basic — end users, not technically trained
- **Access level:** Can only view and manage their own requests
- **Key actions:** Create, edit, submit, cancel (own requests only)

#### 2.3.2 Training Manager Approver

- **Description:** A line manager who oversees direct reports; responsible for first-stage review
- **Technical proficiency:** Basic to intermediate
- **Access level:** Sees own requests + direct reports' requests
- **Key actions:** Approve or reject requests submitted by their direct reports

#### 2.3.3 Training HR Approver

- **Description:** An HR department member responsible for final authorization and budget awareness
- **Technical proficiency:** Intermediate
- **Access level:** Sees all training requests company-wide
- **Key actions:** Final approve or reject; view and edit HR-only notes field

### 2.4 Operating Environment

- **Platform:** Odoo 17 or 18 Community Edition
- **Database:** PostgreSQL (managed by Odoo)
- **Operating System:** Linux (typical Odoo deployment) or Windows (local development)
- **Browser:** Modern web browser (Chrome, Firefox, Edge — latest 2 major versions)
- **Python version:** As required by the chosen Odoo version (Python 3.10+ for Odoo 17/18)

### 2.5 Design and Implementation Constraints

- **CON-01:** Must follow standard Odoo module structure conventions.
- **CON-02:** Must not use `sudo()` to silently bypass security — any usage must be explicitly commented with justification.
- **CON-03:** Security enforcement must be implemented in Python (`write()`, action methods) — client-side XML `groups=` attribute alone is insufficient.
- **CON-04:** Record rules (`ir.rule`) must be used for row-level access — ACL alone is insufficient.
- **CON-05:** Must not break or override core `hr.employee` views — only extend via `inherit`.
- **CON-06:** Must include demo data allowing the module to be installed and tested without manual user/record creation.

### 2.6 Assumptions and Dependencies

- **ASS-01:** The standard `hr` module is installed and active.
- **ASS-02:** Each employee in the system has a correctly configured `parent_id` (line manager) on their `hr.employee` record for manager-based record rules to function correctly.
- **ASS-03:** Users are assigned to exactly one of the three training security groups; edge cases of users in multiple groups are not in scope.
- **ASS-04:** Multi-company support is optional; the core implementation targets single-company.
- **ASS-05:** Email notifications are not a requirement — `mail.thread` integration is a bonus only.
- **DEP-01:** Depends on Odoo module `hr`.
- **DEP-02:** Optionally depends on `mail` if chatter logging is implemented.

---

## 3. System Features (Functional Requirements)

### 3.1 Data Model — `hr.training.request`

**Model Technical Name:** `hr.training.request`  
**Description:** The primary model representing a single employee training request through its entire lifecycle.

#### 3.1.1 Field Specifications

| Field Name | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `employee_id` | `Many2one` → `hr.employee` | Required, default = current user's employee | The requesting employee |
| `manager_id` | `Many2one` → `hr.employee` | Related: `employee_id.parent_id`, Read-only | Auto-populated from employee's line manager |
| `course_name` | `Char` | Required | Name of the training course or certification |
| `training_provider` | `Char` | Optional | Name of the external training provider/institution |
| `start_date` | `Date` | Optional | Scheduled start date of the training |
| `end_date` | `Date` | Optional | Scheduled end date of the training |
| `cost` | `Float` or `Monetary` | Optional | Estimated or actual cost of the training |
| `justification` | `Text` | Optional | Employee's written justification for the request |
| `state` | `Selection` | Required, default = `draft` | Current lifecycle state (see Section 3.3) |
| `hr_notes` | `Text` | Optional, groups = HR Approver only | Internal HR notes — invisible to Requester and Manager |

#### 3.1.2 State Selection Values

| Value | Label | Description |
| :--- | :--- | :--- |
| `draft` | Draft | Initial state; request is being prepared by the employee |
| `submitted` | Submitted | Employee has submitted for manager review |
| `manager_approved` | Manager Approved | Line manager has approved; awaiting HR final approval |
| `hr_approved` | HR Approved | HR has given final approval; request is fully authorized |
| `rejected` | Rejected | Request rejected by manager or HR at their respective stage |
| `cancelled` | Cancelled | Request cancelled by the employee before full manager approval |

### 3.2 Security Groups & Record Rules

#### 3.2.1 Security Groups

Three custom groups must be defined in `security/groups.xml`:

| Group Name | XML ID | Inherits From | Description |
| :--- | :--- | :--- | :--- |
| Training Requester | `group_training_requester` | `hr.group_hr_user` (or base employee) | Base access — all employees |
| Training Manager Approver | `group_training_manager` | `group_training_requester` | First-stage approver for direct reports |
| Training HR Approver | `group_training_hr` | `group_training_manager` | Final approver; company-wide visibility |

**Hierarchy Rationale:**  
Each higher group inherits from the one below, ensuring cumulative permissions. HR Approvers have all Manager Approver capabilities plus full company-wide read access and HR-notes visibility.

#### 3.2.2 Model-Level Access Control (`ir.model.access.csv`)

| Group | Read | Write | Create | Delete |
| :--- | :---: | :---: | :---: | :---: |
| Training Requester | Yes | Yes | Yes | No |
| Training Manager Approver | Yes | Yes | Yes | No |
| Training HR Approver | Yes | Yes | Yes | Yes |

> **Note:** Delete is restricted to HR Approvers only. Employees and Managers may not permanently delete records.

#### 3.2.3 Record Rules (`ir.rule`)

Row-level security must be implemented via `ir.rule` entries. These operate as SQL domain filters applied to every query for the model.

| Rule Name | Applied To Group | Domain Filter | Description |
| :--- | :--- | :--- | :--- |
| `rule_requester_own` | Training Requester | `[('employee_id.user_id', '=', user.id)]` | Employees see only their own requests |
| `rule_manager_team` | Training Manager Approver | `['|', ('employee_id.user_id', '=', user.id), ('employee_id.parent_id.user_id', '=', user.id)]` | Managers see own + direct reports' requests |
| `rule_hr_all` | Training HR Approver | `[(1, '=', 1)]` (or company filter) | HR Approvers see all records (optionally filtered by company) |

> **Important:** Record rules are additive when a user belongs to multiple groups. The `global` flag and `groups` linkage on each rule must be configured correctly. The HR rule should not be a global rule — it should be explicitly scoped to the HR Approver group.

### 3.3 State Machine & Workflow Transitions

#### 3.3.1 Allowed Transitions

| From State | To State | Trigger Action | Authorized Role | Validation Required |
| :--- | :--- | :--- | :--- | :--- |
| `draft` | `submitted` | **Submit** button | Request owner (employee) | `end_date` > `start_date`; `cost` >= 0 |
| `draft` | `cancelled` | **Cancel** button | Request owner (employee) | None |
| `submitted` | `manager_approved` | **Approve** button | Manager of the employee OR Manager Approver group | None |
| `submitted` | `rejected` | **Reject** button | Manager of the employee OR Manager Approver group | None |
| `submitted` | `cancelled` | **Cancel** button | Request owner (employee) | None |
| `manager_approved` | `hr_approved` | **Final Approve** button | HR Approver group | None |
| `manager_approved` | `rejected` | **Reject** button | HR Approver group | None |

> **Illegal transitions are blocked at the Python level** — no client-side bypass is possible.

#### 3.3.2 Guard Implementation Requirements

Every action button method (e.g., `action_submit`, `action_manager_approve`, `action_hr_approve`, `action_reject`, `action_cancel`) **must**:

1. Verify the current `state` of the record is the expected prerequisite state
2. Verify the calling `user` has the appropriate group or relationship (owner / manager)
3. Raise `UserError` or `AccessError` if either check fails
4. Only then perform the state write

```python
# Pseudocode for submit guard
def action_submit(self):
    for rec in self:
        if rec.state != 'draft':
            raise UserError("Only draft requests can be submitted.")
        if rec.employee_id.user_id != self.env.user:
            raise AccessError("Only the request owner can submit.")
        if rec.end_date and rec.start_date and rec.end_date <= rec.start_date:
            raise ValidationError("End date must be after start date.")
        if rec.cost is not None and rec.cost < 0:
            raise ValidationError("Cost cannot be negative.")
        rec.state = 'submitted'
```

### 3.4 Views & User Interface

#### 3.4.1 Form View

**Purpose:** Main data-entry and workflow action screen.

**Requirements:**

| # | Requirement |
| :- | :--- |
| FV-01 | Must include a `statusbar` widget bound to the `state` field at the top of the form |
| FV-02 | Header must display contextually appropriate action buttons (`Submit`, `Approve`, `Reject`, `Cancel`, `Final Approve`) based on current state and user role |
| FV-03 | `cost` and `justification` fields must be editable only in `draft` state; read-only in all other states |
| FV-04 | `manager_id` field must always be read-only (computed from employee) |
| FV-05 | An "HR Notes" tab or field section must be present, but visible and editable **only** to HR Approver group |
| FV-06 | The form must be consistent with Odoo UX conventions (standard footer buttons, chatter at bottom if `mail.thread` is used) |

#### 3.4.2 List (Tree) View

**Purpose:** Overview of training requests with visual state differentiation.

**Required Columns:**

| Column | Field | Notes |
| :--- | :--- | :--- |
| Employee | `employee_id` | |
| Course Name | `course_name` | |
| Provider | `training_provider` | |
| Start Date | `start_date` | |
| End Date | `end_date` | |
| Cost | `cost` | |
| State | `state` | Must use `badge` widget or `decoration-*` for visual distinction |

**State decorations (suggested):**

| State | Suggested Decoration |
| :--- | :--- |
| `draft` | `decoration-muted` / grey |
| `submitted` | `decoration-info` / blue |
| `manager_approved` | `decoration-warning` / orange |
| `hr_approved` | `decoration-success` / green |
| `rejected` | `decoration-danger` / red |
| `cancelled` | `decoration-muted` / grey italic |

#### 3.4.3 Search View

**Required Filters:**

| Filter Label | Domain / Context |
| :--- | :--- |
| Draft | `[('state', '=', 'draft')]` |
| Submitted | `[('state', '=', 'submitted')]` |
| Manager Approved | `[('state', '=', 'manager_approved')]` |
| HR Approved | `[('state', '=', 'hr_approved')]` |
| Rejected | `[('state', '=', 'rejected')]` |
| Cancelled | `[('state', '=', 'cancelled')]` |
| My Requests | `[('employee_id.user_id', '=', uid)]` |
| My Team | `[('employee_id.parent_id.user_id', '=', uid)]` |

**Required Group By Options:**

| Group By Label | Field |
| :--- | :--- |
| Employee | `employee_id` |
| State | `state` |

#### 3.4.4 Menu & Actions

| Menu Level | Label | Notes |
| :--- | :--- | :--- |
| Top-level or under Employees | **Training** | New top-level menu or sub-menu under the HR app |
| Child item | **My Requests** | Default domain: `[('employee_id.user_id', '=', uid)]` |
| Child item | **Pending Manager Approval** | Default domain: `[('state', '=', 'submitted')]`, visible to Manager Approver |
| Child item | **Pending HR Approval** | Default domain: `[('state', '=', 'manager_approved')]`, visible to HR Approver |
| Child item | **All Requests** | Visible to HR Approver only; no domain restriction |

Each action's `context` and `domain` must be pre-set so users land on the most relevant filtered view upon clicking their menu item.

#### 3.4.5 Role-Based Button Visibility Rules

| Button | Visible When (State) | Visible To (Role) | Python Guard Required |
| :--- | :--- | :--- | :---: |
| Submit | `draft` | Request owner | Yes |
| Cancel | `draft`, `submitted` | Request owner | Yes |
| Approve (Manager) | `submitted` | Manager of employee OR Manager Approver group | Yes |
| Reject (Manager) | `submitted` | Manager of employee OR Manager Approver group | Yes |
| Final Approve (HR) | `manager_approved` | HR Approver group | Yes |
| Reject (HR) | `manager_approved` | HR Approver group | Yes |

> **Reminder:** Button visibility in XML (`attrs`, `groups`) is a UI convenience only. The Python method must independently enforce the same rules.

### 3.5 Employee Extension — `hr.employee`

#### 3.5.1 Computed Field

| Field Name | Type | Compute Method | Description |
| :--- | :--- | :--- | :--- |
| `training_request_count` | `Integer` | Count of `hr.training.request` records where `employee_id = self.id` | Displayed in smart button |

The compute method must be correctly filtered to only count records visible to the current user (respect existing record rules — do **not** use `sudo()` unless explicitly justified and commented).

#### 3.5.2 Smart Button

- **Location:** On the `hr.employee` form view (inherited via `<xpath>`)
- **Icon:** `fa-graduation-cap` (or equivalent)
- **Label:** `Training Requests` with the count displayed
- **Action:** Opens a filtered list of `hr.training.request` records for the specific employee, with the viewer's own record rules applied

---

## 4. Non-Functional Requirements

### 4.1 Security

| ID | Requirement |
| :--- | :--- |
| NFR-SEC-01 | All state transition methods must validate user permissions server-side via Python; client-side attribute hiding alone is insufficient |
| NFR-SEC-02 | Record rules must prevent cross-user data leakage at the database query level |
| NFR-SEC-03 | Use of `sudo()` must be accompanied by an inline comment explaining why and confirming it does not expose data to unauthorized users |
| NFR-SEC-04 | The `hr_notes` field must be inaccessible (read and write) to any user not in the HR Approver group, enforced at the model/field level |
| NFR-SEC-05 | No illegal state jumps must be possible via any channel: UI, XML-RPC, JSON-RPC, or ORM shell |

### 4.2 Performance

| ID | Requirement |
| :--- | :--- |
| NFR-PERF-01 | The `training_request_count` computed field must use a single SQL query (`read_group`) rather than iterating through records |
| NFR-PERF-02 | List views must not trigger N+1 query issues — use `_rec_name` and avoid unindexed computed fields in list columns |

### 4.3 Maintainability & Code Quality

| ID | Requirement |
| :--- | :--- |
| NFR-MNT-01 | All Python code must follow PEP 8 style conventions |
| NFR-MNT-02 | Model, field, and method names must follow Odoo naming conventions (snake_case, descriptive) |
| NFR-MNT-03 | No dead code, commented-out blocks, or debug artifacts in the final submission |
| NFR-MNT-04 | Odoo ORM must be used idiomatically — avoid raw SQL unless strictly necessary |
| NFR-MNT-05 | XML views must follow Odoo view ID naming conventions (`view_hr_training_request_form`, etc.) |

### 4.4 Usability

| ID | Requirement |
| :--- | :--- |
| NFR-USE-01 | State progression must be clearly visible via the `statusbar` widget |
| NFR-USE-02 | Each user role must land on a contextually relevant default view/filter upon accessing the Training menu |
| NFR-USE-03 | Buttons unavailable due to state or role must be hidden (XML `groups`, `attrs`) to avoid user confusion — Python guards handle actual enforcement |
| NFR-USE-04 | Error messages from validation (e.g., invalid dates, negative cost) must be user-friendly `UserError` / `ValidationError` messages, not raw Python exceptions |

### 4.5 Compatibility

| ID | Requirement |
| :--- | :--- |
| NFR-COMP-01 | The module must be compatible with Odoo 17 **or** Odoo 18 Community; the README must state which version was used |
| NFR-COMP-02 | The module must not modify or break any standard `hr` module views, models, or workflows |
| NFR-COMP-03 | Extension of `hr.employee` must use standard `<record model="ir.ui.view">` with `inherit_id` — no full view replacement |

---

## 5. Technical Architecture & Module Structure

```
hr_training_request/
├── __init__.py
├── __manifest__.py                     # Module manifest (name, version, depends, data, demo)
│
├── models/
│   ├── __init__.py
│   ├── hr_training_request.py          # Main model: hr.training.request
│   └── hr_employee.py                  # Extension: hr.employee (computed field + smart button logic)
│
├── security/
│   ├── groups.xml                      # Three security groups definition
│   ├── ir.model.access.csv             # Model-level ACL (CRUD per group)
│   └── ir_rules.xml                    # Row-level record rules (ir.rule)
│
├── views/
│   ├── hr_training_request_views.xml   # Form, List, Search views for hr.training.request
│   ├── hr_employee_views.xml           # Inherited hr.employee form (smart button)
│   └── menus.xml                       # Menu items and window actions
│
├── data/
│   └── demo_data.xml                   # Demo users, employees, and sample training requests
│
└── README.md                           # Developer README (assumptions, security hierarchy, improvements)
```

### 5.1 `__manifest__.py` Key Fields

```python
{
    'name': 'HR Training Request',
    'version': '17.0.1.0.0',       # or 18.0.1.0.0
    'category': 'Human Resources',
    'summary': 'Employee training request and approval workflow',
    'depends': ['hr'],              # Add 'mail' if using mail.thread
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/hr_training_request_views.xml',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

---

## 6. Workflow & State Diagram

```
                   [Employee]        [Manager / Mgr Approver]    [HR Approver]

                      |                        |                       |
                   CREATE                      |                       |
                      |                        |                       |
                      v                        |                       |
                  +-------+  Submit()          |                       |
                  | DRAFT |-------------------> +------------+         |
                  +-------+                    | SUBMITTED  |         |
                      |  Cancel()              +------------+         |
                      <--------------------------- |    |             |
                      |                    Approve |    | Reject      |
                      v                            |    |             |
               +-----------+            +------------------+  +----------+
               | CANCELLED |            | MANAGER_APPROVED |  | REJECTED |
               +-----------+            +------------------+  +----------+
                                                  |    |
                                         Final    |    | Reject
                                        Approve   |    +----------------->
                                                  v
                                         +-------------+
                                         | HR_APPROVED |  (Terminal)
                                         +-------------+

Terminal states: hr_approved, rejected, cancelled
```

---

## 7. Role-Based Access Matrix

### 7.1 Record Visibility

| User Role | Own Requests | Direct Reports' Requests | All Company Requests |
| :--- | :---: | :---: | :---: |
| Training Requester | Yes | No | No |
| Training Manager Approver | Yes | Yes | No |
| Training HR Approver | Yes | Yes | Yes |

### 7.2 Field Editability by Role & State

| Field | Requester (draft) | Requester (other states) | Manager Approver | HR Approver |
| :--- | :---: | :---: | :---: | :---: |
| `employee_id` | Editable | Read-only | Read-only | Read-only |
| `course_name` | Editable | Read-only | Read-only | Read-only |
| `training_provider` | Editable | Read-only | Read-only | Read-only |
| `start_date` / `end_date` | Editable | Read-only | Read-only | Read-only |
| `cost` | Editable | Read-only | Read-only | Read-only |
| `justification` | Editable | Read-only | Read-only | Read-only |
| `manager_id` | Read-only | Read-only | Read-only | Read-only |
| `hr_notes` | Hidden | Hidden | Hidden | Editable |

### 7.3 Button Availability by Role & State

| Action Button | Requester | Manager Approver | HR Approver | Required State |
| :--- | :---: | :---: | :---: | :--- |
| Submit | Yes (own) | No | No | `draft` |
| Cancel | Yes (own) | No | No | `draft` or `submitted` |
| Approve (Manager stage) | No | Yes (direct reports) | Yes | `submitted` |
| Reject (Manager stage) | No | Yes (direct reports) | Yes | `submitted` |
| Final Approve (HR stage) | No | No | Yes | `manager_approved` |
| Reject (HR stage) | No | No | Yes | `manager_approved` |

---

## 8. Validation Rules

| Rule ID | Trigger | Condition | Error Message |
| :--- | :--- | :--- | :--- |
| VAL-01 | `action_submit` | `end_date` is set AND `end_date <= start_date` | "The end date must be after the start date." |
| VAL-02 | `action_submit` | `cost` is set AND `cost < 0` | "Training cost cannot be a negative value." |
| VAL-03 | Any state write | Caller does not have required group/relationship | `AccessError`: "You do not have permission to perform this action." |
| VAL-04 | Any state write | Record is not in the expected source state | `UserError`: "This action is not allowed in the current state." |
| VAL-05 | `onchange` or `_check_dates` constraint | `end_date < start_date` (form-level) | Warning or validation error on save |

---

## 9. Deliverables

| # | Deliverable | Required | Notes |
| :- | :--- | :---: | :--- |
| D-01 | GitHub repository containing the complete Odoo module | Yes | Preferred over zip; clean commit history expected |
| D-02 | Zip of the module (alternative to GitHub) | One of D-01/D-02 | |
| D-03 | `README.md` inside the module | Yes | Must explain security group hierarchy, assumptions, and improvements |
| D-04 | Demo data (`data/demo_data.xml`) | Yes | Must allow install-and-test without manual setup |
| D-05 | Three PNG wireframes (Employee, Manager, HR Approver views) | Yes | As specified in Section 4 of the assignment |
| D-06 | 2-3 min screen recording of the workflow across three user logins | Optional | Bonus — highly appreciated |

---

## 10. Evaluation Criteria

| Area | Weight | What is Evaluated |
| :--- | :--- | :--- |
| **Security Correctness** | High | Record rules and ACL actually restrict data at the database level — not just view-level hiding. No security bypass possible. |
| **State Machine Design** | High | Clean, guarded transitions; no illegal state jumps possible via any route (UI, XML-RPC, ORM shell). All guards implemented in Python. |
| **Role-Based UX** | High | Right buttons and fields are visible/editable to the right role at the right stage — consistently across form and list views. |
| **Code Quality** | Medium | Idiomatic Odoo ORM usage; sensible naming; no dead code; PEP 8 compliance; no raw SQL unless justified. |
| **Inheritance Handling** | Medium | Clean `hr.employee` extension that does not break or override core views. Standard inheritance patterns used. |
| **Communication** | Medium | README is clear and well-reasoned. Commit history is logical. Assumptions are documented explicitly rather than left silent. |

> **Grading philosophy:** A smaller, correctly-secured and well-documented module is rated higher than a large, feature-rich module with security holes or access bypasses.

---

*End of Software Requirements Specification*

---

**Document Version History**

| Version | Date | Author | Notes |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-07-25 | — | Initial SRS derived from assignment specification |
