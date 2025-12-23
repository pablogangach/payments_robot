# Implementation Plan - Repository Pattern Refactor

Refactoring the routing logic to separate data access (Repository) from business logic (Preprocessing) and data management (Ingestion).

## Goal
Decouple the data storage mechanism from the services. `PreprocessingService` should act as a reader provided with a Repository, and a separate service will handle writing/ingestion.

## Proposed Changes

### 1. New Repository Layer
#### [NEW] `payments_service/app/repositories/performance_repository.py`
- Define `RoutingPerformanceRepository` class.
- Move the in-memory `_store` and retrieval logic (`get_performance_data`) here.
- Add methods for `save_performance` (for the writer).

### 2. Refactor Preprocessing Service (The Reader)
#### [MODIFY] `payments_service/app/services/preprocessing_service.py`
- Change dependency from `RoutingDataService` to `RoutingPerformanceRepository`.
- Logic remains the same, but calls `repository.find_by_dimension(dim)`.

### 3. Refactor Routing Data Service (The Writer)
#### [MODIFY] `payments_service/app/services/routing_data_service.py`
- Rename class (and file if needed) to `RoutingDataManager` or `RoutingDataIngestor`.
- It will depend on `RoutingPerformanceRepository`.
- Responsible for "Writing" data (e.g., `ingest_fees`, `update_metrics`).

## Verification Plan
### Automated Tests
- Run `pytest payments_service/tests/`.
- Update `test_preprocessing_service.py` to mock/use the Repository.
- Update `test_routing_data_service.py` to test the Repository and the Manager separately.
