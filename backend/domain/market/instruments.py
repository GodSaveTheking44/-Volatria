from dataclasses import dataclass

@dataclass
class Instrument:
    symbol: str
    name: str
    asset_class: str
    sector: str = "N/A"

@dataclass
class Exchange:
    name: str
    mic: str # Market Identifier Code
    location: str
