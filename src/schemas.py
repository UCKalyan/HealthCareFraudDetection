from pydantic import BaseModel

class NpiRequest(BaseModel):
    npi: int

class ManualDataRequest(BaseModel):
    total_service_cost: float
    total_services: int
    total_benes_phys: int
    total_drug_cost: float
    total_scripts: int
    total_benes_presc: int
    specialty: str
