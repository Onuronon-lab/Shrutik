# Engineering Conventions & Philosophy

> **Why this exists**
>
> This document is not about rules for the sake of rules.
> It exists to reduce confusion, remove unnecessary discussion, and protect engineering quality.
>
> Conventions are not constraints, they are _agreements_.
> Agreements let teams move fast without stepping on each other.

---

## 1. Philosophy (Read this first)

- Engineering is about **clarity**, not cleverness.
- If something needs explanation, it’s already slightly wrong.
- Conventions exist so that:
  - No one has to ask questions repeatedly
  - No one has to justify decisions emotionally
  - The system explains itself

> We don’t optimize for personal preference.
> We optimize for **collective understanding** and **future maintainability**.

Everything here follows one principle:

> **Do not raise unnecessary questions for the next person reading your work.**

That next person might be your teammate.
Or future you at 3 AM.

---

## 2. Branch Naming Convention

Branch names must follow this format:

```
<prefix>/<short-description>
```

### Allowed prefixes

- `feat/` → New features
- `fix/` → Bug fixes
- `hotfix/` → Critical production fixes
- `docs/` → Documentation-only changes

### Examples

- `feat/auth-verification`
- `fix/password-reset-token`
- `docs/api-guidelines`

### Why this matters

- Branch lists should be scannable at a glance
- Prefixes instantly communicate _intent_
- Consistency removes cognitive load

If every branch uses a different word (`feature/`, `new/`, `stuff/`), the system slowly becomes noisy.
Noise kills velocity.

---

## 3. Commit Message Convention

We follow **Conventional Commits**.

Format:

```
<type>(<scope>): <clear, concrete description>
```

### Allowed types

- `feat` → New functionality
- `fix` → Bug fix
- `docs` → Documentation
- `refactor` → Code restructure without behavior change
- `test` → Tests
- `chore` → Tooling / config

### Examples

- `feat(auth): add email verification flow`
- `fix(auth): prevent reset token reuse`
- `docs(readme): add setup instructions`

### What commit messages are **not**

- Not marketing
- Not self-evaluation
- Not emotion

Avoid words like:

- strong
- robust
- powerful
- improved (without context)

> A commit message should describe **what changed**, not **how good it feels**.

If something is buggy → it’s wrong.
If something works → that’s the baseline, not an achievement.

---

## 4. Pull Requests

- A PR should do **one logical thing**
- The title should summarize the change
- The description should answer:
  - What changed?
  - Why was it needed?

No philosophy debates inside PRs.
If a rule is violated, it will be requested to change, not discussed.

---

## 5. Source of Truth

- **WIP project docs are not the source of truth**
- External standards, official documentation, and established practices take priority

Always question:

- outdated docs
- informal assumptions
- "this is how we’ve been doing it"

Engineering grows by questioning, not by accepting.

---

## 6. Ego & Engineering

- Software is never perfect
- Everything has limits
- Everything breaks eventually

That’s exactly why we aim for:

- clarity over cleverness
- simplicity over ego
- consistency over preference

Having strong opinions is good.
Letting conventions decide instead of ego is better.

---

## 7. Final Note

These conventions are not optional.
They exist so we can:

- move faster
- argue less
- build things that last

If something here feels strict, that’s intentional.
Discipline is what gives freedom later.

> Clean systems scale. Messy ones don’t.

Follow the convention.
Save your energy for real problems.
