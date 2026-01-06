"""
Chainlit MongoDB Data Layer
Custom data layer for storing threads and messages in MongoDB
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from chainlit.data import BaseDataLayer
from chainlit.types import ThreadDict, PaginatedResponse, Pagination, Feedback
from chainlit.step import StepDict
from chainlit.element import ElementDict
from chainlit.user import User, PersistedUser
from pymongo import MongoClient
from bson import ObjectId
import os


class MongoDBDataLayer(BaseDataLayer):
    """MongoDB data layer for Chainlit persistence"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.db_name = os.getenv("MONGODB_DB_NAME", "trading-bot")
        self.client = None
        self.db = None
        
        if self.mongodb_url:
            try:
                self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                print(f"[ChainlitDataLayer] Connected to MongoDB: {self.db_name}")
            except Exception as e:
                print(f"[ChainlitDataLayer] MongoDB connection failed: {e}")
    
    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        """Get user by identifier"""
        if not self.db:
            return None
        
        user_doc = self.db.users.find_one({"identifier": identifier})
        if user_doc:
            return PersistedUser(
                id=str(user_doc["_id"]),
                identifier=user_doc["identifier"],
                metadata=user_doc.get("metadata", {}),
                createdAt=user_doc.get("created_at", datetime.now()).isoformat()
            )
        return None
    
    async def create_user(self, user: User) -> Optional[PersistedUser]:
        """Create a new user"""
        if not self.db:
            return None
        
        user_doc = {
            "identifier": user.identifier,
            "metadata": user.metadata or {},
            "created_at": datetime.now()
        }
        result = self.db.users.insert_one(user_doc)
        
        return PersistedUser(
            id=str(result.inserted_id),
            identifier=user.identifier,
            metadata=user.metadata or {},
            createdAt=datetime.now().isoformat()
        )
    
    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        """Update or create a thread"""
        if not self.db:
            return
        
        update_doc = {"updated_at": datetime.now()}
        if name:
            update_doc["name"] = name
        if user_id:
            update_doc["user_id"] = user_id
        if metadata:
            update_doc["metadata"] = metadata
        if tags:
            update_doc["tags"] = tags
        
        self.db.threads.update_one(
            {"thread_id": thread_id},
            {
                "$set": update_doc,
                "$setOnInsert": {"created_at": datetime.now(), "thread_id": thread_id}
            },
            upsert=True
        )
    
    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        """Get a thread by ID"""
        if not self.db:
            return None
        
        thread_doc = self.db.threads.find_one({"thread_id": thread_id})
        if not thread_doc:
            return None
        
        # Get steps for this thread
        steps = list(self.db.steps.find({"thread_id": thread_id}).sort("created_at", 1))
        
        return ThreadDict(
            id=thread_doc["thread_id"],
            name=thread_doc.get("name", "Untitled"),
            createdAt=thread_doc.get("created_at", datetime.now()).isoformat(),
            metadata=thread_doc.get("metadata", {}),
            userId=thread_doc.get("user_id"),
            userIdentifier=thread_doc.get("user_identifier"),
            tags=thread_doc.get("tags", []),
            steps=[self._step_doc_to_dict(s) for s in steps]
        )
    
    async def get_thread_author(self, thread_id: str) -> str:
        """Get the author of a thread"""
        if not self.db:
            return ""
        
        thread_doc = self.db.threads.find_one({"thread_id": thread_id})
        return thread_doc.get("user_id", "") if thread_doc else ""
    
    async def delete_thread(self, thread_id: str):
        """Delete a thread and its steps"""
        if not self.db:
            return
        
        self.db.threads.delete_one({"thread_id": thread_id})
        self.db.steps.delete_many({"thread_id": thread_id})
    
    async def list_threads(
        self, pagination: Pagination, filters: Dict
    ) -> PaginatedResponse[ThreadDict]:
        """List threads with pagination"""
        if not self.db:
            return PaginatedResponse(data=[], pageInfo={"hasNextPage": False})
        
        query = {}
        if "userId" in filters:
            query["user_id"] = filters["userId"]
        
        cursor = self.db.threads.find(query).sort("updated_at", -1).limit(pagination.first + 1)
        threads = list(cursor)
        
        has_next = len(threads) > pagination.first
        if has_next:
            threads = threads[:-1]
        
        thread_dicts = []
        for t in threads:
            thread_dicts.append(ThreadDict(
                id=t["thread_id"],
                name=t.get("name", "Untitled"),
                createdAt=t.get("created_at", datetime.now()).isoformat(),
                metadata=t.get("metadata", {}),
                userId=t.get("user_id"),
                userIdentifier=t.get("user_identifier"),
                tags=t.get("tags", []),
                steps=[]
            ))
        
        return PaginatedResponse(
            data=thread_dicts,
            pageInfo={"hasNextPage": has_next, "endCursor": threads[-1]["thread_id"] if threads else None}
        )
    
    async def create_step(self, step_dict: StepDict):
        """Create a step"""
        if not self.db:
            return
        
        step_doc = {
            "step_id": step_dict.get("id"),
            "thread_id": step_dict.get("threadId"),
            "parent_id": step_dict.get("parentId"),
            "name": step_dict.get("name"),
            "type": step_dict.get("type"),
            "output": step_dict.get("output"),
            "input": step_dict.get("input"),
            "created_at": datetime.now(),
            "start_time": step_dict.get("startTime"),
            "end_time": step_dict.get("endTime"),
            "metadata": step_dict.get("metadata", {})
        }
        self.db.steps.insert_one(step_doc)
    
    async def update_step(self, step_dict: StepDict):
        """Update a step"""
        if not self.db:
            return
        
        self.db.steps.update_one(
            {"step_id": step_dict.get("id")},
            {"$set": {
                "output": step_dict.get("output"),
                "end_time": step_dict.get("endTime"),
                "metadata": step_dict.get("metadata", {})
            }}
        )
    
    async def delete_step(self, step_id: str):
        """Delete a step"""
        if not self.db:
            return
        
        self.db.steps.delete_one({"step_id": step_id})
    
    async def create_element(self, element: ElementDict):
        """Create an element"""
        pass  # Not implemented for now
    
    async def get_element(self, thread_id: str, element_id: str) -> Optional[ElementDict]:
        """Get an element"""
        return None
    
    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        """Delete an element"""
        pass
    
    async def upsert_feedback(self, feedback: Feedback) -> str:
        """Upsert feedback"""
        if not self.db:
            return ""
        
        result = self.db.feedback.update_one(
            {"step_id": feedback.forId},
            {"$set": {"value": feedback.value, "comment": feedback.comment}},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else feedback.forId
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback"""
        if not self.db:
            return False
        
        result = self.db.feedback.delete_one({"_id": ObjectId(feedback_id)})
        return result.deleted_count > 0
    
    def _step_doc_to_dict(self, step_doc: Dict) -> StepDict:
        """Convert MongoDB document to StepDict"""
        return StepDict(
            id=step_doc.get("step_id"),
            threadId=step_doc.get("thread_id"),
            parentId=step_doc.get("parent_id"),
            name=step_doc.get("name"),
            type=step_doc.get("type"),
            output=step_doc.get("output"),
            input=step_doc.get("input"),
            startTime=step_doc.get("start_time"),
            endTime=step_doc.get("end_time"),
            metadata=step_doc.get("metadata", {})
        )
    
    def build_debug_url(self) -> str:
        """Build debug URL for the data layer"""
        return ""
    
    async def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()
            print("[ChainlitDataLayer] MongoDB connection closed")
