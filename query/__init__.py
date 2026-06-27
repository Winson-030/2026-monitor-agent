"""Query module for natural language GCP resource queries."""

from .intent import QueryIntent, parse_intent
from .executor import execute_query

__all__ = ['QueryIntent', 'parse_intent', 'execute_query']
