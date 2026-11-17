from backend.celery_app import celery_app
from backend.services.carbon_calculator import CarbonCalculator
from backend.models.farm import Farm
from backend.models.sustainability import CarbonLedger, SustainabilityScore
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.recalculate_all_offsets')
def recalculate_all_offsets_task():
    """Recalculate carbon offset totals for all farms."""
    logger.info("Starting recalculate_all_offsets_task...")
    farms = Farm.query.all()
    count = 0
    for farm in farms:
        try:
            CarbonCalculator.run_full_audit(farm.id)
            count += 1
        except Exception as e:
            logger.error(f"Offset recalc failed for Farm {farm.id}: {e}")
    return {'status': 'completed', 'farms_processed': count}


@celery_app.task(name='tasks.stale_audit_check')
def stale_audit_check_task():
    """Flag sustainability audits that have gone stale (not updated in 90 days)."""
    from datetime import datetime, timedelta
    logger.info("Running stale audit check...")
    cutoff = datetime.utcnow() - timedelta(days=90)
    stale = SustainabilityScore.query.filter(
        SustainabilityScore.updated_at < cutoff
    ).all()
    for record in stale:
        logger.warning(f"Stale sustainability score for farm_id={record.farm_id}")
    return {'status': 'completed', 'stale_count': len(stale)}


@celery_app.task(name='tasks.annual_credit_revaluation')
def annual_credit_revaluation_task():
    """Annually revalue all carbon credits based on current market prices."""
    logger.info("Running annual carbon credit revaluation...")
    farms = Farm.query.all()
    count = 0
    for farm in farms:
        try:
            score = SustainabilityScore.query.filter_by(farm_id=farm.id).first()
            if score:
                # Apply a 2% market appreciation factor annually
                score.offset_credits_available *= 1.02
                db.session.add(score)
                count += 1
        except Exception as e:
            logger.error(f"Credit revaluation failed for Farm {farm.id}: {e}")
    db.session.commit()
    return {'status': 'completed', 'farms_updated': count}



@celery_app.task(name='tasks.sustainability_compliance_sync')
def sustainability_compliance_sync():
    """
    Daily background task to aggregate farm operations and generate carbon reports.
    Identifies 'Net-Zero' qualified farms.
    """
    logger.info("Starting Sustainability Compliance Sync...")
    farms = Farm.query.all()
    count = 0
    
    for farm in farms:
        try:
            # 1. Run Carbon Audit
            ledger = CarbonCalculator.run_full_audit(farm.id)
            
            # 2. Update Sustainability Score
            score = SustainabilityScore.query.filter_by(farm_id=farm.id).first()
            if not score:
                score = SustainabilityScore(farm_id=farm.id)
                db.session.add(score)
            
            # Simple ratings update
            if ledger.total_footprint < 1000: # Mock thresholds
                score.overall_rating = 95.0
                score.offset_credits_available += 10.0 # Reward net-zero behavior
                ledger.certification_status = 'NET_ZERO'
            else:
                score.overall_rating = 70.0
                
            db.session.add(score)
            count += 1
        except Exception as e:
            logger.error(f"Sustainability sync failed for Farm {farm.id}: {str(e)}")
            
    db.session.commit()
    return {'status': 'completed', 'farms_processed': count}

@celery_app.task(name='tasks.process_carbon_credit_trade')
def process_carbon_credit_trade(from_farm_id, to_farm_id, credits):
    """
    Handles internal arbitrage of carbon credits between farms.
    Executed when a 'BarterExchange' involves sustainability points.
    """
    # Logic to transfer offset_credits_available between SustainabilityScore models
    pass
