"""Tests for pattern detectors."""

import pytest
from deburger.analyzers.patterns.cold_start import ColdStartDetector
from deburger.analyzers.patterns.s3_in_loop import S3InLoopDetector
from deburger.analyzers.patterns.unbounded_query import UnboundedQueryDetector
from deburger.analyzers.patterns.no_connection_pool import ConnectionPoolDetector
from deburger.analyzers.base import IssueType


@pytest.fixture
def config():
    return {
        "traffic": {"requests_per_day": 100000, "avg_memory_mb": 1024},
    }


class TestColdStartDetector:
    def test_detects_heavy_imports_in_lambda(self, config):
        detector = ColdStartDetector()
        code = """import tensorflow
import torch
import pandas

def handler(event, context):
    return process(event)
"""
        issues = detector.detect("handler.py", code, config)
        assert len(issues) == 1
        assert "cold start" in issues[0].description

    def test_ignores_non_lambda_files(self, config):
        detector = ColdStartDetector()
        code = """import tensorflow
import pandas

def process_data():
    return []
"""
        issues = detector.detect("utils.py", code, config)
        assert len(issues) == 0

    def test_ignores_light_imports(self, config):
        detector = ColdStartDetector()
        code = """import os
import json

def handler(event, context):
    return {}
"""
        issues = detector.detect("handler.py", code, config)
        assert len(issues) == 0


class TestS3InLoopDetector:
    def test_detects_s3_in_loop(self, config):
        detector = S3InLoopDetector()
        code = """
for key in keys:
    s3.get_object(Bucket='my-bucket', Key=key)
"""
        issues = detector.detect("process.py", code, config)
        assert len(issues) == 1
        assert "S3" in issues[0].description

    def test_no_false_positive_outside_loop(self, config):
        detector = S3InLoopDetector()
        code = """
result = s3.get_object(Bucket='my-bucket', Key='file.json')
"""
        issues = detector.detect("process.py", code, config)
        assert len(issues) == 0


class TestUnboundedQueryDetector:
    def test_detects_all_without_limit(self, config):
        detector = UnboundedQueryDetector()
        code = """
results = User.objects.filter(active=True).all()
"""
        issues = detector.detect("views.py", code, config)
        assert len(issues) >= 1

    def test_no_false_positive_with_limit(self, config):
        detector = UnboundedQueryDetector()
        code = """
results = User.objects.filter(active=True).all()[:100]
"""
        issues = detector.detect("views.py", code, config)
        assert len(issues) == 0


class TestConnectionPoolDetector:
    def test_detects_connection_in_function(self, config):
        detector = ConnectionPoolDetector()
        code = """
def handle_request(request):
    conn = psycopg2.connect(host='localhost', dbname='mydb')
    cursor = conn.cursor()
    return cursor.fetchall()
"""
        issues = detector.detect("views.py", code, config)
        assert len(issues) == 1
        assert "connection" in issues[0].description

    def test_no_false_positive_with_pool(self, config):
        detector = ConnectionPoolDetector()
        code = """
pool = psycopg2.pool.SimpleConnectionPool(1, 10, host='localhost')

def handle_request(request):
    conn = pool.getconn()
    return conn.cursor().fetchall()
"""
        issues = detector.detect("views.py", code, config)
        assert len(issues) == 0
