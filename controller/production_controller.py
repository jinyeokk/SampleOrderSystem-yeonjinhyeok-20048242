from app import AppContext
from view.production_view import ProductionView


class ProductionController:

    def __init__(self, ctx: AppContext, view: ProductionView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        items = sorted(
            self._ctx.production_service.get_in_progress(),
            key=lambda x: x[1].queued_at,
        )
        sample_map = {
            order.sample_id: self._ctx.sample_service.get(order.sample_id)
            for order, _ in items
        }
        self._view.show_dashboard(items, sample_map)
