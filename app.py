import sqlite3

from db.schema import initialize_schema
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from service.monitoring_service import MonitoringService
from service.order_service import OrderService
from service.production_service import ProductionService
from service.release_service import ReleaseService
from service.sample_service import SampleService


class AppContext:
    """애플리케이션 전역 의존성 컨테이너."""

    def __init__(self, conn: sqlite3.Connection | None = None) -> None:
        if conn is None:
            from db.connection import DBConnection
            conn = DBConnection.get()
        initialize_schema(conn)

        self.sample_repo     = SampleRepository(conn)
        self.order_repo      = OrderRepository(conn)
        self.production_repo = ProductionRepository(conn)

        self.sample_service = SampleService(self.sample_repo)
        self.order_service  = OrderService(
            self.order_repo, self.production_repo, self.sample_service
        )
        self.production_service = ProductionService(
            self.order_service, self.order_repo, self.production_repo, self.sample_service
        )
        self.release_service    = ReleaseService(self.order_service, self.order_repo)
        self.monitoring_service = MonitoringService(
            self.order_repo, self.sample_repo, self.production_repo
        )
