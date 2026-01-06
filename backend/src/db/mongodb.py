"""
MongoDB Client for Chat History Storage
Stores analyses and chat messages for retrieval
"""

import os
from datetime import datetime
from typing import Optional, List, Dict
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment from project root (.env in Ai-project/)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_project_root, '.env'))


class MongoDBClient:
    """MongoDB client for storing and retrieving chat history"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.db_name = os.getenv("MONGODB_DB_NAME", "chat-ui")
        self.client = None
        self.db = None
        
        if self.mongodb_url:
            try:
                self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                print(f"[MongoDB] Connected to database: {self.db_name}")
            except Exception as e:
                print(f"[MongoDB] Connection failed: {e}")
                print("[MongoDB] Continuing without database persistence")
                self.client = None
                self.db = None
        else:
            print("[MongoDB] MONGODB_URL not found in environment")
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        return self.db is not None
    
    def save_analysis(self, ticker: str, final_decision: str, report_content: str, 
                      sections: Optional[Dict] = None) -> Optional[str]:
        """
        Save stock analysis to MongoDB
        
        Args:
            ticker: Stock ticker symbol
            final_decision: BUY/SELL/HOLD
            report_content: Full report content
            sections: Optional dict with individual sections
            
        Returns:
            Inserted document ID or None if failed
        """
        if not self.is_connected():
            return None
        
        try:
            doc = {
                "ticker": ticker.upper(),
                "analysis_date": datetime.now(),
                "final_decision": final_decision,
                "report_content": report_content,
                "sections": sections or {}
            }
            
            result = self.db.analyses.insert_one(doc)
            print(f"[MongoDB] Saved analysis for {ticker}: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"[MongoDB] Error saving analysis: {e}")
            return None
    
    def get_latest_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Get the most recent analysis for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Analysis document or None
        """
        if not self.is_connected():
            return None
        
        try:
            doc = self.db.analyses.find_one(
                {"ticker": ticker.upper()},
                sort=[("analysis_date", -1)]
            )
            return doc
        except Exception as e:
            print(f"[MongoDB] Error getting analysis: {e}")
            return None
    
    def get_analyses_history(self, ticker: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get analysis history
        
        Args:
            ticker: Optional ticker to filter by
            limit: Max number of results
            
        Returns:
            List of analysis documents
        """
        if not self.is_connected():
            return []
        
        try:
            query = {"ticker": ticker.upper()} if ticker else {}
            cursor = self.db.analyses.find(query).sort("analysis_date", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"[MongoDB] Error getting history: {e}")
            return []
    
    def save_message(self, session_id: str, ticker: str, role: str, content: str) -> Optional[str]:
        """
        Save a chat message
        
        Args:
            session_id: Chainlit session ID
            ticker: Related stock ticker
            role: "user" or "assistant"
            content: Message content
            
        Returns:
            Inserted document ID or None
        """
        if not self.is_connected():
            return None
        
        try:
            doc = {
                "session_id": session_id,
                "ticker": ticker.upper() if ticker else None,
                "role": role,
                "content": content,
                "timestamp": datetime.now()
            }
            
            result = self.db.chat_messages.insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"[MongoDB] Error saving message: {e}")
            return None
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Get chat history for a session
        
        Args:
            session_id: Chainlit session ID
            limit: Max number of messages
            
        Returns:
            List of message documents
        """
        if not self.is_connected():
            return []
        
        try:
            cursor = self.db.chat_messages.find(
                {"session_id": session_id}
            ).sort("timestamp", 1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"[MongoDB] Error getting chat history: {e}")
            return []

    def get_chat_history_by_ticker(self, ticker: str, limit: int = 50) -> List[Dict]:
        """
        Get chat history for a specific ticker
        """
        if not self.is_connected():
            return []
        
        try:
            # Get messages where ticker matches
            cursor = self.db.chat_messages.find(
                {"ticker": ticker.upper()}
            ).sort("timestamp", 1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"[MongoDB] Error getting ticker chat history: {e}")
            return []
    
    def search_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search analyses by text
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching analyses
        """
        if not self.is_connected():
            return []
        
        try:
            # Simple text search in report content
            cursor = self.db.analyses.find(
                {"report_content": {"$regex": query, "$options": "i"}}
            ).sort("analysis_date", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"[MongoDB] Error searching: {e}")
            return []


# Singleton instance
_mongo_client = None

def get_mongo_client() -> MongoDBClient:
    """Get or create MongoDB client singleton"""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoDBClient()
    return _mongo_client
