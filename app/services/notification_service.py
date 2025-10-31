"""
Notification Service

This service handles notifications for job status updates, system events,
and user alerts. It supports multiple notification channels including
database logging, Redis pub/sub, and external integrations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session

from app.core.redis_client import redis_client
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class NotificationLevel(str, Enum):
    """Notification severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    DATABASE = "database"
    REDIS = "redis"
    EMAIL = "email"
    WEBHOOK = "webhook"
    PUSH = "push"


@dataclass
class Notification:
    """Notification data structure."""
    id: Optional[str] = None
    title: str = ""
    message: str = ""
    level: NotificationLevel = NotificationLevel.INFO
    channel: NotificationChannel = NotificationChannel.REDIS
    recipient_id: Optional[int] = None
    recipient_type: str = "user"  # user, admin, system
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationService:
    """Service for managing notifications across different channels."""
    
    def __init__(self, redis_client_instance=None):
        """
        Initialize the notification service.
        
        Args:
            redis_client_instance: Optional Redis client instance
        """
        self.redis_client = redis_client_instance or redis_client
    
    def send_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        channels: List[NotificationChannel] = None,
        recipient_id: Optional[int] = None,
        recipient_type: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_seconds: Optional[int] = None
    ) -> str:
        """
        Send a notification through specified channels.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification severity level
            channels: List of channels to send through
            recipient_id: ID of the recipient (user, admin, etc.)
            recipient_type: Type of recipient
            metadata: Additional metadata
            expires_in_seconds: Expiration time in seconds
            
        Returns:
            Notification ID
        """
        if channels is None:
            channels = [NotificationChannel.REDIS]
        
        # Create notification object
        notification = Notification(
            id=self._generate_notification_id(),
            title=title,
            message=message,
            level=level,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc)
        )
        
        if expires_in_seconds:
            notification.expires_at = datetime.now(timezone.utc).timestamp() + expires_in_seconds
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == NotificationChannel.REDIS:
                    self._send_redis_notification(notification)
                elif channel == NotificationChannel.DATABASE:
                    self._send_database_notification(notification)
                elif channel == NotificationChannel.EMAIL:
                    self._send_email_notification(notification)
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook_notification(notification)
                elif channel == NotificationChannel.PUSH:
                    self._send_push_notification(notification)
                
                logger.info(f"Notification {notification.id} sent via {channel.value}")
                
            except Exception as e:
                logger.error(f"Failed to send notification {notification.id} via {channel.value}: {e}")
        
        return notification.id
    
    def send_job_notification(
        self,
        job_id: str,
        job_name: str,
        status: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        recipient_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a job-specific notification.
        
        Args:
            job_id: Celery task ID
            job_name: Name of the job/task
            status: Job status (success, failure, retry, etc.)
            message: Notification message
            level: Notification level
            recipient_id: User ID to notify
            metadata: Additional job metadata
            
        Returns:
            Notification ID
        """
        title = f"Job {status.title()}: {job_name}"
        
        job_metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "job_status": status,
            "notification_type": "job_status"
        }
        
        if metadata:
            job_metadata.update(metadata)
        
        return self.send_notification(
            title=title,
            message=message,
            level=level,
            channels=[NotificationChannel.REDIS, NotificationChannel.DATABASE],
            recipient_id=recipient_id,
            recipient_type="user",
            metadata=job_metadata,
            expires_in_seconds=86400  # 24 hours
        )
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            unread_only: Whether to return only unread notifications
            
        Returns:
            List of notification dictionaries
        """
        try:
            # Get notifications from Redis
            key = f"user_notifications:{user_id}"
            notifications_data = self.redis_client.lrange(key, 0, limit - 1)
            
            notifications = []
            for data in notifications_data:
                try:
                    notification_dict = json.loads(data)
                    
                    # Filter unread if requested
                    if unread_only and notification_dict.get('read_at'):
                        continue
                    
                    notifications.append(notification_dict)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse notification data: {e}")
                    continue
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications for user {user_id}: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID
            
        Returns:
            True if marked successfully
        """
        try:
            # Update in Redis
            key = f"user_notifications:{user_id}"
            notifications_data = self.redis_client.lrange(key, 0, -1)
            
            updated_notifications = []
            found = False
            
            for data in notifications_data:
                try:
                    notification_dict = json.loads(data)
                    
                    if notification_dict.get('id') == notification_id:
                        notification_dict['read_at'] = datetime.now(timezone.utc).isoformat()
                        found = True
                    
                    updated_notifications.append(json.dumps(notification_dict))
                    
                except json.JSONDecodeError:
                    updated_notifications.append(data)  # Keep original if can't parse
            
            if found:
                # Replace the entire list
                self.redis_client.delete(key)
                if updated_notifications:
                    self.redis_client.lpush(key, *reversed(updated_notifications))
                    self.redis_client.expire(key, 86400)  # 24 hours
                
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {e}")
            return False
    
    def get_system_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get system-wide notifications.
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of system notification dictionaries
        """
        try:
            key = "system_notifications"
            notifications_data = self.redis_client.lrange(key, 0, limit - 1)
            
            notifications = []
            for data in notifications_data:
                try:
                    notification_dict = json.loads(data)
                    notifications.append(notification_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse system notification data: {e}")
                    continue
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get system notifications: {e}")
            return []
    
    def cleanup_expired_notifications(self) -> int:
        """
        Clean up expired notifications from Redis.
        
        Returns:
            Number of notifications cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Get all notification keys
            keys = self.redis_client.client.keys("*notifications*")
            
            for key in keys:
                try:
                    notifications_data = self.redis_client.lrange(key, 0, -1)
                    valid_notifications = []
                    
                    for data in notifications_data:
                        try:
                            notification_dict = json.loads(data)
                            expires_at = notification_dict.get('expires_at')
                            
                            if expires_at and expires_at < current_time:
                                cleaned_count += 1
                                continue  # Skip expired notification
                            
                            valid_notifications.append(data)
                            
                        except json.JSONDecodeError:
                            valid_notifications.append(data)  # Keep if can't parse
                    
                    # Update the list with only valid notifications
                    if len(valid_notifications) != len(notifications_data):
                        self.redis_client.delete(key)
                        if valid_notifications:
                            self.redis_client.lpush(key, *reversed(valid_notifications))
                            self.redis_client.expire(key, 86400)
                
                except Exception as e:
                    logger.error(f"Failed to cleanup notifications for key {key}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} expired notifications")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired notifications: {e}")
            return 0
    
    def _generate_notification_id(self) -> str:
        """Generate a unique notification ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _send_redis_notification(self, notification: Notification):
        """Send notification via Redis."""
        notification_dict = asdict(notification)
        notification_dict['created_at'] = notification.created_at.isoformat()
        
        if notification.expires_at:
            notification_dict['expires_at'] = notification.expires_at
        
        notification_json = json.dumps(notification_dict)
        
        # Store in user-specific list if recipient specified
        if notification.recipient_id:
            key = f"user_notifications:{notification.recipient_id}"
            self.redis_client.lpush(key, notification_json)
            self.redis_client.ltrim(key, 0, 99)  # Keep last 100
            self.redis_client.expire(key, 86400)  # 24 hours
        
        # Store in system notifications for admin/system level
        if notification.recipient_type in ["admin", "system"]:
            key = "system_notifications"
            self.redis_client.lpush(key, notification_json)
            self.redis_client.ltrim(key, 0, 199)  # Keep last 200
            self.redis_client.expire(key, 86400)  # 24 hours
        
        # Publish to Redis pub/sub for real-time updates
        channel = f"notifications:{notification.recipient_type}"
        if notification.recipient_id:
            channel = f"notifications:user:{notification.recipient_id}"
        
        self.redis_client.client.publish(channel, notification_json)
    
    def _send_database_notification(self, notification: Notification):
        """Send notification via database storage."""
        # This would store notifications in a database table
        # For now, just log the notification
        logger.info(f"Database notification: {notification.title} - {notification.message}")
    
    def _send_email_notification(self, notification: Notification):
        """Send notification via email."""
        # This would integrate with an email service
        # For now, just log the notification
        logger.info(f"Email notification: {notification.title} - {notification.message}")
    
    def _send_webhook_notification(self, notification: Notification):
        """Send notification via webhook."""
        # This would send HTTP POST to configured webhook URLs
        # For now, just log the notification
        logger.info(f"Webhook notification: {notification.title} - {notification.message}")
    
    def _send_push_notification(self, notification: Notification):
        """Send push notification."""
        # This would integrate with push notification services
        # For now, just log the notification
        logger.info(f"Push notification: {notification.title} - {notification.message}")


# Global notification service instance
notification_service = NotificationService()