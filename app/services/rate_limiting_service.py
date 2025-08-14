from sqlalchemy.orm import Session
from app.models.user_usage import UserUsage, get_db
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib

class RateLimitingService:
    def __init__(self):
        self.daily_limit = 25
        self.monthly_limit = 750
    
    def _get_user_hash(self, user_identifier: str) -> str:
        """Create a hash of user identifier for privacy"""
        return hashlib.sha256(user_identifier.encode()).hexdigest()[:16]
    
    def _get_or_create_user_usage(self, db: Session, user_id: str) -> UserUsage:
        """Get or create user usage record"""
        user_usage = db.query(UserUsage).filter(UserUsage.user_id == user_id).first()
        
        if not user_usage:
            user_usage = UserUsage(
                user_id=user_id,
                daily_message_count=0,
                monthly_message_count=0,
                last_reset_date=datetime.utcnow()
            )
            db.add(user_usage)
            db.commit()
            db.refresh(user_usage)
        
        return user_usage
    
    def _reset_daily_count_if_needed(self, user_usage: UserUsage) -> bool:
        """Reset daily count if it's a new day"""
        now = datetime.utcnow()
        last_reset = user_usage.last_reset_date
        
        # Check if it's a new day
        if last_reset.date() < now.date():
            user_usage.daily_message_count = 0
            user_usage.last_reset_date = now
            return True
        return False
    
    def _reset_monthly_count_if_needed(self, user_usage: UserUsage) -> bool:
        """Reset monthly count if it's a new month"""
        now = datetime.utcnow()
        last_reset = user_usage.last_reset_date
        
        # Check if it's a new month
        if (last_reset.year, last_reset.month) < (now.year, now.month):
            user_usage.monthly_message_count = 0
            return True
        return False
    
    def check_rate_limit(self, user_identifier: str, db: Session) -> Tuple[bool, str, dict]:
        """
        Check if user has exceeded rate limits
        Returns: (is_allowed, message, usage_info)
        """
        user_id = self._get_user_hash(user_identifier)
        user_usage = self._get_or_create_user_usage(db, user_id)
        
        # Reset counts if needed
        daily_reset = self._reset_daily_count_if_needed(user_usage)
        monthly_reset = self._reset_monthly_count_if_needed(user_usage)
        
        if daily_reset or monthly_reset:
            db.commit()
            db.refresh(user_usage)
        
        # Check daily limit
        if user_usage.daily_message_count >= self.daily_limit:
            usage_info = {
                "daily_used": user_usage.daily_message_count,
                "daily_limit": self.daily_limit,
                "monthly_used": user_usage.monthly_message_count,
                "monthly_limit": self.monthly_limit
            }
            return False, f"Daily limit of {self.daily_limit} messages exceeded. Try again tomorrow.", usage_info
        
        # Check monthly limit
        if user_usage.monthly_message_count >= self.monthly_limit:
            usage_info = {
                "daily_used": user_usage.daily_message_count,
                "daily_limit": self.daily_limit,
                "monthly_used": user_usage.monthly_message_count,
                "monthly_limit": self.monthly_limit
            }
            return False, f"Monthly limit of {self.monthly_limit} messages exceeded. Limit resets next month.", usage_info
        
        usage_info = {
            "daily_used": user_usage.daily_message_count,
            "daily_limit": self.daily_limit,
            "monthly_used": user_usage.monthly_message_count,
            "monthly_limit": self.monthly_limit
        }
        
        return True, "Request allowed", usage_info
    
    def increment_usage(self, user_identifier: str, db: Session) -> None:
        """Increment user's message count"""
        user_id = self._get_user_hash(user_identifier)
        user_usage = self._get_or_create_user_usage(db, user_id)
        
        # Reset counts if needed
        self._reset_daily_count_if_needed(user_usage)
        self._reset_monthly_count_if_needed(user_usage)
        
        # Increment counts
        user_usage.daily_message_count += 1
        user_usage.monthly_message_count += 1
        
        db.commit()
    
    def get_usage_stats(self, user_identifier: str, db: Session) -> dict:
        """Get user's current usage statistics"""
        user_id = self._get_user_hash(user_identifier)
        user_usage = self._get_or_create_user_usage(db, user_id)
        
        # Reset counts if needed
        self._reset_daily_count_if_needed(user_usage)
        self._reset_monthly_count_if_needed(user_usage)
        
        return {
            "daily_used": user_usage.daily_message_count,
            "daily_remaining": max(0, self.daily_limit - user_usage.daily_message_count),
            "daily_limit": self.daily_limit,
            "monthly_used": user_usage.monthly_message_count,
            "monthly_remaining": max(0, self.monthly_limit - user_usage.monthly_message_count),
            "monthly_limit": self.monthly_limit
        }
