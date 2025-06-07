from pydantic import BaseModel
from typing import Optional

class BasicDataForm(BaseModel):
    month: int
    year: int
    clients_served: int
    sales_revenue: float
    sales_expenses: float
    input_product_expenses: float
    fixed_costs: Optional[float] = None
    ideal_profit_margin: Optional[float] = None
    service_capacity: Optional[str] = None
    pro_labore: Optional[float] = None
    work_hours_per_week: Optional[float] = None
    other_fixed_costs: Optional[float] = None
    ideal_service_profit_margin: Optional[float] = None
    is_current: Optional[bool] = False
    activity_type: Optional[str] = None 