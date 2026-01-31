# Service Layer Rules

The service layer contains **all business logic**. Services coordinate work between routes/controllers, database models, and external systems.

These rules exist to keep behavior explicit, testable, and discoverable by both humans and AI code agents.

---

## 1. Service shape and responsibilities

**Default:** A service is a **class** that groups related business operations.

A function-only service is allowed **only** when it is:

* Stateless
* Pure (no database writes, no external/network calls)
* Small enough to be immediately understandable

Each service class **must be documented** with:

* What the service is responsible for
* What the service explicitly does not do

Services:

* MAY call other services
* MAY directly read from and write to database models
* MUST contain all business rules and decision-making logic
* MUST NOT contain HTTP, request, response, or framework-specific logic

---

## 2. Interaction with database models

Services are the **only layer** allowed to:

* Create, update, or delete database records
* Enforce business invariants across multiple models
* Coordinate transactional changes

Models:

* Represent persisted state only
* MUST NOT contain business logic

Routes/controllers:

* MUST NOT access database models directly
* MUST delegate all business behavior to services

---

## 3. Public method documentation

Each **public** service method must document:

* Purpose (what problem it solves)
* Inputs (types and meaning)
* Outputs (return type and meaning)
* Side effects (database writes, events, external calls)

Private/helper methods do not require documentation.

---

## 4. services/README.md is mandatory

`services/README.md` acts as the **authoritative index** of the service layer.

It must list:

* Available services
* Service class names
* One-line responsibility description
* High-level input/output summary

This README **must be updated whenever services change**.

---

## 5. Documentation is the source of truth

If documentation and code drift apart:

* The documentation is considered **wrong**
* It must be fixed **immediately**

Undocumented services or undocumented public methods are treated as incomplete work.
