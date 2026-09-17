from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# --- THE SECURITY GATE (CORS) ---
# This allows your Next.js frontend to securely talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE BOUNCER ---
class TaxInput(BaseModel):
    gross_salary: float
    deductions_80c: float = 0.0
    deductions_80d: float = 0.0
    hra_exemption: float = 0.0

# --- THE MATH HELPERS ---
def calculate_old_regime_tax(taxable_income: float) -> float:
    if taxable_income <= 250000:
        return 0
    elif taxable_income <= 500000:
        # 87A Rebate makes tax 0 if income is under 5L
        return 0
    
    tax = 0
    # 5% slab (2.5L to 5L)
    if taxable_income > 250000:
        tax += min(taxable_income - 250000, 250000) * 0.05
    # 20% slab (5L to 10L)
    if taxable_income > 500000:
        tax += min(taxable_income - 500000, 500000) * 0.20
    # 30% slab (Above 10L)
    if taxable_income > 1000000:
        tax += (taxable_income - 1000000) * 0.30
        
    # Add 4% Health & Education Cess
    return tax + (tax * 0.04)

def calculate_new_regime_tax(taxable_income: float) -> float:
    if taxable_income <= 700000:
        # 87A Rebate makes tax 0 if income is under 7L in New Regime
        return 0
        
    tax = 0
    # Slabs for New Regime
    if taxable_income > 300000:
        tax += min(taxable_income - 300000, 400000) * 0.05   # 3L to 7L
    if taxable_income > 700000:
        tax += min(taxable_income - 700000, 300000) * 0.10   # 7L to 10L
    if taxable_income > 1000000:
        tax += min(taxable_income - 1000000, 200000) * 0.15  # 10L to 12L
    if taxable_income > 1200000:
        tax += min(taxable_income - 1200000, 300000) * 0.20  # 12L to 15L
    if taxable_income > 1500000:
        tax += (taxable_income - 1500000) * 0.30             # Above 15L
        
    # Add 4% Health & Education Cess
    return tax + (tax * 0.04)

# --- THE API ROUTES ---
@app.get("/")
def read_root():
    return {"message": "The Tax Engine is alive and doing real math!"}

@app.post("/api/calculate")
def calculate_tax(profile: TaxInput):
    # 1. Figure out taxable income
    taxable_old = max(0, profile.gross_salary - 50000 - profile.deductions_80c - profile.deductions_80d - profile.hra_exemption)
    taxable_new = max(0, profile.gross_salary - 75000) # Only standard deduction allowed in new regime
    
    # 2. Run the actual tax math
    tax_old = calculate_old_regime_tax(taxable_old)
    tax_new = calculate_new_regime_tax(taxable_new)
    
    # 3. Figure out which one saves the user money
    best_regime = "New Regime" if tax_new < tax_old else "Old Regime"
    money_saved = abs(tax_old - tax_new)

    return {
        "status": "success",
        "gross_salary": profile.gross_salary,
        "old_regime": {
            "taxable_income": taxable_old,
            "final_tax": tax_old
        },
        "new_regime": {
            "taxable_income": taxable_new,
            "final_tax": tax_new
        },
        "recommendation": best_regime,
        "tax_saved": money_saved
    }
