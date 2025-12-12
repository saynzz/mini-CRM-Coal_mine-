# Импорты всех менеджеров для удобного доступа
from .coal_manager import CoalManager
from .section_manager import SectionManager
from .position_manager import PositionManager
from .worker_manager import WorkerManager
from .mining_manager import MiningManager
from .cost_manager import CostManager
from .timesheet_manager import TimesheetManager
from .limit_manager import LimitManager

__all__ = [
    'CoalManager',
    'SectionManager', 
    'PositionManager',
    'WorkerManager',
    'MiningManager',
    'CostManager',
    'TimesheetManager',
    'LimitManager'
]