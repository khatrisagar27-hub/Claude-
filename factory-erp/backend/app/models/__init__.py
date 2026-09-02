"""Import every model module here so Base.metadata sees all tables —
Alembic's autogenerate and the test suite's create_all() both depend on it."""

from app.models.plant import Plant, Warehouse, Shift  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.machine import Machine, MachineDowntime, MaintenanceLog  # noqa: F401
from app.models.stock import Product, BOMItem, StockMovement  # noqa: F401
from app.models.production import WorkOrder, RejectionLog  # noqa: F401
