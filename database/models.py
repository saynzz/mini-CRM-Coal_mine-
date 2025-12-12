from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Coal:
    mark: str
    ash_content: float
    moisture: float
    calorific_value: int
    price_per_ton: float

@dataclass
class Position:
    id: int
    name: str

@dataclass
class Section:
    id: int
    name: str
    area: float
    height: float
    manager_id: Optional[int] = None

@dataclass
class Worker:
    tab_number: int
    full_name: str
    section_id: int
    position_id: int
    iin: str
    address: str
    phone: str
    gender: str
    birth_date: date

@dataclass
class Mining:
    date: date
    shift: int
    volume: float
    coal_mark: str
    section_id: int
    rock_volume: float

@dataclass
class Limits:
    section_id: int
    month: int
    year: int
    plan_production: float
    plan_rock: float
    plan_electricity: float
    plan_fuel: float