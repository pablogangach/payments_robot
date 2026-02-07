import csv
from typing import List, Any
from payments_service.app.routing.ingestion.interfaces import DataProvider
from payments_service.app.routing.ingestion.parsers import BaseTransactionParser
from payments_service.app.routing.ingestion.models import RawTransactionRecord

class LocalFileDataProvider(DataProvider):
    """
    Test-only data provider that reads from a local CSV file.
    Simulates the flow of fetching a file from S3 and parsing it.
    """
    def __init__(self, file_path: str, parser: BaseTransactionParser):
        self.file_path = file_path
        self.parser = parser

    def fetch_data(self) -> List[RawTransactionRecord]:
        """
        Reads the CSV file and uses the provided parser to return canonical records.
        """
        records = []
        with open(self.file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(self.parser.parse(row))
        return records
