"""
MaintenanceLog model for tracking farm asset maintenance history.
"""
from datetime import datetime
from backend.extensions import db


class MaintenanceLog(db.Model):
    """Records maintenance events for FarmAssets."""
    __tablename__ = 'maintenance_logs'

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('farm_assets.id'), nullable=False, index=True)

    # Maintenance details
    maintenance_type = db.Column(db.String(50), nullable=False, default='ROUTINE')
    # e.g. ROUTINE, REPAIR, EMERGENCY, INSPECTION, OVERHAUL
    description = db.Column(db.Text)
    parts_replaced = db.Column(db.Text)  # JSON list of part names
    cost = db.Column(db.Float, default=0.0)

    # Health tracking
    pre_maintenance_health = db.Column(db.Float)
    post_maintenance_health = db.Column(db.Float)

    # Personnel
    technician_name = db.Column(db.String(100))
    technician_notes = db.Column(db.Text)

    # Scheduling
    status = db.Column(db.String(30), default='SCHEDULED')
    # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    scheduled_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'log_id': self.log_id,
            'asset_id': self.asset_id,
            'maintenance_type': self.maintenance_type,
            'description': self.description,
            'cost': self.cost,
            'pre_maintenance_health': self.pre_maintenance_health,
            'post_maintenance_health': self.post_maintenance_health,
            'technician_name': self.technician_name,
            'status': self.status,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'created_at': self.created_at.isoformat(),
        }
