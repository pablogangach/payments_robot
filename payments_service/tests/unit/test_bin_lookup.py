from unittest.mock import MagicMock
from payments_service.app.core.repositories.metadata_repository import CardBINRepository
from payments_service.app.core.models.metadata import CardBIN
from payments_service.tests.factories import create_mock

def test_bin_lookup():
    # 1. Setup mock store
    mock_store = MagicMock()
    repo = CardBINRepository(mock_store)
    
    # 2. Mock behavior
    mock_bin_data = create_mock(
        CardBIN,
        bin="411111",
        brand="Visa",
        type="credit",
        country="United States"
    )
    mock_store.find_by_id.return_value = mock_bin_data
    
    # 3. Execute
    result = repo.find_by_bin("411111")
    
    # 4. Assert
    assert result is not None
    assert result.brand == "Visa"
    assert result.country == "United States"
    mock_store.find_by_id.assert_called_with("411111")
    print("BIN lookup test passed!")

if __name__ == "__main__":
    test_bin_lookup()
