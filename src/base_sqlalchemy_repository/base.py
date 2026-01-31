import logging
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    Tuple,
)

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from .ops import (
    OP_EQ,
    OP_NE,
    OP_LT,
    OP_LTE,
    OP_GT,
    OP_GTE,
    OP_LIKE,
    OP_ILIKE,
    OP_IN,
)
from .types import (
    M,
    SQLOperationsDict,
)


log = logging.getLogger(__name__)


class BaseSQLAlchemyRepository(Generic[M]):
    """
    Generic asynchronous repository for SQLAlchemy models.
    """

    OPS: ClassVar[SQLOperationsDict] = {
        "eq": OP_EQ,
        "ne": OP_NE,
        "lt": OP_LT,
        "lte": OP_LTE,
        "gt": OP_GT,
        "gte": OP_GTE,
        "like": OP_LIKE,
        "ilike": OP_ILIKE,
        "in_": OP_IN,
    }

    def __init__(
        self,
        model: Type[M],
        session: AsyncSession,
    ):
        """
        Initialize repository with a model class and async session.

        Args:
            model: SQLAlchemy declarative model class
            session: Active AsyncSession instance
        """
        from sqlalchemy import inspect

        self.model = model
        self._mapper = inspect(self.model)
        self.session = session

    async def create(
        self,
        data: Dict[str, Any],
        *,
        commit: bool = True,
    ) -> M:
        """
        Create and persist a new model instance.

        Args:
            data: Mapping of model fields to values
            commit: Whether to commit the transaction immediately

        Returns:
            The created and persisted model instance

        Raises:
            Any database exception is re-raised after rollback
        """
        log.debug(
            "Creating %s",
            self.model.__name__,
            extra={"data_keys": list(data.keys())},
        )

        new_instance = self.model(**data)
        self.session.add(new_instance)

        try:
            if commit:
                await self.session.commit()
                await self.session.refresh(new_instance)

                log.info(
                    "%s created",
                    self.model.__name__,
                    extra={"id": getattr(new_instance, "id", None)},
                )
            else:
                # Flush ensures PKs and defaults are generated
                await self.session.flush()
                log.debug("%s flushed (no commit)", self.model.__name__)
        except Exception:
            log.exception(
                "Failed to create %s",
                self.model.__name__,
            )
            await self.session.rollback()
            raise

        return new_instance

    def _apply_filters(
        self,
        stmt: Select[Any],
        filters: Dict[str, Any],
    ) -> Select[Tuple[M]]:
        """
        Apply dynamic filters to a SQLAlchemy Select statement.

        Supported syntax:
            field=value            -> equality
            field__gte=value       -> >=
            field__ilike="%text%"  -> ILIKE
            field__in=[a, b, c]    -> IN (...)

        Args:
            stmt: Base Select statement
            filters: Dictionary of filters using Django-like syntax

        Returns:
            Modified Select statement with WHERE conditions applied

        Raises:
            ValueError: If field or operator is invalid
        """

        OPERATOR_ALIASES = {
            "in": "in_",
        }

        for key, value in filters.items():
            field, _, raw_op = key.partition("__")
            operator = OPERATOR_ALIASES.get(raw_op or "eq", raw_op or "eq")

            if field not in self._mapper.column_attrs:
                raise ValueError(f"Invalid field '{field}' for {self.model.__name__}")

            assert operator in self.OPS, f"Unsupported operator '{operator}'"

            column = getattr(self.model, field)
            stmt = stmt.where(self.OPS[operator](column, value))

        return stmt

    def _build_query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Select[Tuple[M]]:
        """
        Build a Select query with optional filtering, sorting, and pagination.

        Args:
            filters: Dynamic filter definitions
            order_by: Field name for sorting.
                      Prefix with '-' for descending order (e.g. "-created_at")
            offset: Number of rows to skip
            limit: Maximum number of rows to return

        Returns:
            Fully constructed Select statement
        """
        stmt = select(self.model)

        if filters is not None:
            stmt = self._apply_filters(stmt=stmt, filters=filters)

        # Sorting (e.g. "-created_at" for DESC)
        if order_by is not None:
            desc = order_by.startswith("-")
            field = order_by.lstrip("-")

            if field not in self._mapper.columns:
                raise ValueError(
                    f"Invalid order_by field '{field}' for {self.model.__name__}"
                )

            column = getattr(self.model, field)
            stmt = stmt.order_by(column.desc() if desc else column.asc())

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return stmt

    async def get_many(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[M]:
        """
        Retrieve multiple records matching provided criteria.

        Returns:
            List of model instances
        """
        stmt = self._build_query(
            filters=filters,
            order_by=order_by,
            offset=offset,
            limit=limit,
        )

        res = await self.session.scalars(stmt)
        return list(res.all())

    async def get_one(
        self,
        *,
        filters: Optional[Dict[str, Any]],
    ) -> Optional[M]:
        """
        Retrieve a single record matching the provided filters.

        If multiple records match, the first one is returned.

        Returns:
            Model instance or None if not found
        """
        stmt = self._build_query(filters=filters).limit(1)
        return await self.session.scalar(stmt)

    async def update(
        self,
        model_id: Any,
        data: Dict[str, Any],
        *,
        commit: bool = True,
    ) -> bool:
        """
        Update an existing record by primary key.

        Args:
            model_id: Primary key value
            data: Fields to update
            commit: Whether to commit the transaction immediately

        Returns:
            True if record was updated, False if not found
        """
        log.debug(
            "Updating %s",
            self.model.__name__,
            extra={"id": model_id, "fields": list(data.keys())},
        )

        instance = await self.get_one(filters={"id": model_id})
        if instance is None:
            return False

        for field, value in data.items():
            if field not in self._mapper.column_attrs:
                raise ValueError(f"Invalid field '{field}' for {self.model.__name__}")
            setattr(instance, field, value)

        try:
            if commit:
                await self.session.commit()
                log.info(
                    "%s updated",
                    self.model.__name__,
                    extra={"id": model_id},
                )
            else:
                await self.session.flush()
                log.debug("%s flushed (no commit)", self.model.__name__)
        except Exception:
            log.exception(
                "Failed to update %s",
                self.model.__name__,
                extra={"id": model_id},
            )

            await self.session.rollback()
            raise

        return True

    async def delete(
        self,
        model_id: Any,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Delete a record by primary key.

        Args:
            model_id: Primary key value
            commit: Whether to commit the transaction immediately

        Returns:
            True if record was deleted, False if not found
        """
        log.debug(
            "Deleting %s",
            self.model.__name__,
            extra={"id": model_id},
        )

        instance = await self.get_one(
            filters={
                "id": model_id,
            }
        )
        if not instance:
            return False

        try:
            await self.session.delete(instance)

            if commit:
                await self.session.commit()
                log.info(
                    "%s deleted",
                    self.model.__name__,
                    extra={"id": model_id},
                )
            else:
                await self.session.flush()
        except Exception:
            log.exception(
                "Failed to delete %s",
                self.model.__name__,
                extra={"id": model_id},
            )
            await self.session.rollback()
            raise

        return True
