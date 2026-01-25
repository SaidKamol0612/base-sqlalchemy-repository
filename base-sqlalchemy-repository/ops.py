from .types import (
    BinaryOp,
    NumericOp,
    StringOp,
    InclusionOp,
)


OP_EQ: BinaryOp = lambda c, v: c == v
OP_NE: BinaryOp = lambda c, v: c != v
OP_LT: NumericOp = lambda c, v: c < v
OP_LTE: NumericOp = lambda c, v: c <= v
OP_GT: NumericOp = lambda c, v: c > v
OP_GTE: NumericOp = lambda c, v: c >= v
OP_LIKE: StringOp = lambda c, v: c.like(v)
OP_ILIKE: StringOp = lambda c, v: c.ilike(v)
OP_IN: InclusionOp = lambda c, v: c.in_(v)
