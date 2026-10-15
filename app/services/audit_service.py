from typing import Optional, Union
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_event(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[int] = None,
    resource_id: Optional[Union[str, int]] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
) -> AuditLog:
    """Record a security audit log event.
    
    Security rule: Never log plaintext passwords, raw JWT tokens, or full clinical bodies.
    """
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        details=details[:500] if details else None,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
