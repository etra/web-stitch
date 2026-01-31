# Database Models Rules

Database models represent **persisted state only**.
All business behavior (rules, decisions, workflows) belongs in the **service layer**.

These rules exist to keep models simple, predictable, and safe for both humans and AI code agents.

---

## 1. What models are for

Models MAY:
- Define persisted fields/columns
- Define basic types, defaults, nullability, and constraints that are purely structural
- Define indexes that improve query performance
- Define relationships **only when required by the ORM** for querying/joins (see Rule 4)

Models MUST:
- Represent the database schema and data shape

---

## 2. What models must NOT do

Models MUST NOT:
- Contain business logic (decisions, invariants, workflows)
- Perform database writes (`commit`, `flush`, `rollback`) or manage sessions
- Call services or external systems
- Perform validation that depends on business rules
- Hide side effects behind property setters or magic methods

If logic is needed, move it to a service.

---

## 3. Who is allowed to touch models

- **Services** MAY read and write models (including queries and persistence).
- **Routes/controllers** MUST NOT access models directly.
- **Models** MUST NOT call services.

Services are the only layer allowed to enforce business invariants and coordinate multi-model changes.

---

## 4. Relationships and foreign keys

### 4.1 Preferred approach
Prefer **application-level relationships** coordinated in services.

### 4.2 Foreign keys
If your project rule is “no DB-level foreign keys”, then:
- Do NOT add database-enforced FK constraints
- You MAY store foreign key *ids* (e.g., `user_id: UUID`) as plain fields
- Enforce referential integrity in services

If DB-enforced foreign keys ARE allowed in this repo, this file must explicitly say so.
(Do not guess. Follow the repository rule.)

---

## 5. Model documentation is mandatory

### 5.1 Per-model docstrings
Each model class MUST include a docstring that documents:
- Purpose (what entity it represents)
- Key fields and what they mean
- Allowed states (if applicable, but describe states — do not implement behavior here)

### 5.2 models/README.md
`models/README.md` is the authoritative index of the model layer.

It MUST list:
- All models
- One-line description of each model’s purpose
- Key identifiers (primary key, any external identifiers)

This README must be updated whenever models change.

---

## 6. Migrations

- Any schema change MUST be accompanied by a migration.
- Migration code MUST match the documented model shape.
- If documentation and schema drift apart, fix documentation immediately.

---

## 7. Practical checklist

When adding or changing a model:
- [ ] Does it represent persisted state only?
- [ ] Is there **zero** business logic in the model?
- [ ] Are all DB writes happening in services?
- [ ] Did you update `models/README.md`?
- [ ] Did you add/adjust the migration?

If any answer is “no”, stop and fix before proceeding.
