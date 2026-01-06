"""
Database package - Data persistence layer
"""

from .mongodb import MongoDBClient, get_mongo_client

__all__ = ['MongoDBClient', 'get_mongo_client']
