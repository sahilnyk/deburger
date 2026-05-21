from deburger.analyzers.patterns.unindexed_query import UnindexedQueryDetector
from deburger.analyzers.patterns.cold_start import ColdStartDetector
from deburger.analyzers.patterns.no_connection_pool import ConnectionPoolDetector
from deburger.analyzers.patterns.unbounded_query import UnboundedQueryDetector
from deburger.analyzers.patterns.s3_in_loop import S3InLoopDetector
from deburger.analyzers.patterns.expensive_logging import ExpensiveLoggingDetector

ALL_PATTERNS = [
    UnindexedQueryDetector(),
    ColdStartDetector(),
    ConnectionPoolDetector(),
    UnboundedQueryDetector(),
    S3InLoopDetector(),
    ExpensiveLoggingDetector(),
]

__all__ = [
    "UnindexedQueryDetector",
    "ColdStartDetector",
    "ConnectionPoolDetector",
    "UnboundedQueryDetector",
    "S3InLoopDetector",
    "ExpensiveLoggingDetector",
    "ALL_PATTERNS",
]
