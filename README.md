# Async SQLAlchemy Repository

Lightweight, typed, and extensible **async repository pattern** for SQLAlchemy 2.x.

This library provides a generic `BaseAsyncRepository` with:

- dynamic Django-like filters
- strict typing (mypy / Pyright friendly)
- async-first design
- zero magic, zero hidden queries

Perfect fit for **FastAPI**, **SQLAlchemy async**, and clean architecture projects.

---

## ✨ Features

- ✅ Async-first (`AsyncSession`)
- ✅ Generic repository (`Generic[M]`)
- ✅ Dynamic filters (`field=value`, `field__gte=value`, `field__in=[...]`)
- ✅ Fully typed filter operators
- ✅ Safe SQLAlchemy expressions (no raw SQL)
- ✅ Easy to extend with custom operators

---

## 📦 Installation

```bash
git clone https://github.com/SaidKamol0612/base-sqlalchemy-repository.git
```

---

## 🚀 Quick Start

### Define a model

```python
# models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    age: Mapped[int]
```

---

### Create repository

```python
# repositories.py
from sqlalchemy.ext.asyncio import AsyncSession

from base_sqlalchemy_repository import BaseSQLAlchemyRepository

from .models import User


class UserRepository(BaseSQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        self.model = User
        self.session = session


user_repo = UserRepository(session=session)
```

---

### Create record

```python
user = await user_repo.create(
    {
        "email": "test@example.com",
        "age": 25,
    }
)
```

---

### Query records with filters

```python
users = await repo.get_many(
    filters={
        "age__gte": 18,
        "email__ilike": "%@example.com",
    },
    order_by="-age",
    limit=10,
)
```

Supported filter syntax:

| Syntax               | Meaning    |
| -------------------- | ---------- |
| `field=value`        | `=`        |
| `field__ne=value`    | `!=`       |
| `field__lt=value`    | `<`        |
| `field__lte=value`   | `<=`       |
| `field__gt=value`    | `>`        |
| `field__gte=value`   | `>=`       |
| `field__like=value`  | `LIKE`     |
| `field__ilike=value` | `ILIKE`    |
| `field__in=[a, b]`   | `IN (...)` |

---

### Get single record

```python
user = await repo.get_one(
    filters={"email": "test@example.com"}
)
```

Return `None` if not found.

---

### Update record

```python
updated = await repo.update(
    model_id=1,
    data={"age": 30},
)

if not updated:
    print("User not found")

```

---

### Delete record

```python
deleted = await repo.delete(model_id=1)
```

---

## 🧠 Design Principles

- No ORM abstraction leakage
- SQLAlchemy stays SQLAlchemy
- Explicit > implicit
- Typing is a feature, not decoration

This repository does **not**:

- hide joins
- auto-generate relations
- invent query DSLs

---

## 🧪 Requirements

- Python 3.12+
- SQLAlchemy 2.x

---

## 📄 License

MIT License.

---

## 🤝 Contributing

PRs and discussions are welcome:

- bug fixes
- typing improvements
- new operators
- docs improvements

---

## ⭐ Motivation

This project exists because:

> writing the same code over and over is boring

If this saves you time — ⭐ the repo.

---
