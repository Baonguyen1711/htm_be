from apscheduler.schedulers.background import BackgroundScheduler
import datetime, logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()
from typing import Callable, List, Tuple

def schedule_timer_multiplayer_game(room_id: str, trigger_time: str, question_number: int, trigger_function: Callable, args: List|Tuple):
    # from ..dependencies.router_dependencies import get_game_data_service  # lazy import
    # game = get_game_data_service()  # cached singleton
    run_at = datetime.datetime.fromtimestamp(trigger_time / 1000, tz=datetime.timezone.utc)
    
    scheduler.add_job(
        trigger_function,
        "date",
        run_date=run_at,
        args=args,
        id=f"{room_id}-q{question_number+1}-{trigger_function.__name__}",
        replace_existing=True
    )

    logger.info(f"Scoreboard scheduled for room {room_id}, q{question_number+1} at {run_at}")

def remove_all_jobs_for_room(room_id: str):
    for job in scheduler.get_jobs():
        if room_id in job.id:
            scheduler.remove_job(job.id)
            logger.info(f"Removed job {job.id} for room {room_id}")

