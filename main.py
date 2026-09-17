from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 1. THE BOUNCER: Defines exactly what data we expect
class TaxInput(BaseModel):
    gross_salary: float
    deductions_80c: float = 0.0
    deductions_80d: float = 0.0
    hra_exemption: float = 0.0

@app.get("/")
def read_root():
    return {"message": "The Tax Engine is alive!"}

# 2. THE CALCULATOR: Receives data, does math, returns answer
@app.post("/api/calculate")
def calculate_tax(profile: TaxInput):
    # Old Regime: Subtract 50k standard deduction, plus all 80C/80D/HRA
    taxable_old = profile.gross_salary - 50000 - profile.deductions_80c - profile.deductions_80d - profile.hra_exemption
    taxable_old = max(0, taxable_old) # Prevents negative income
    
    # New Regime (Budget 2025): Only subtract the new 75k standard deduction
    taxable_new = profile.gross_salary - 75000
    taxable_new = max(0, taxable_new)
    
    # Send the processed data back
    return {
        "status": "success",
        "taxable_income_old_regime": taxable_old,
        "taxable_income_new_regime": taxable_new,
        "note": "We will add the actual tax slab percentages next!"
    }
