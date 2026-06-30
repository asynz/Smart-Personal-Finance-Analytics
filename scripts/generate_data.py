'''
Generates a realistic synthetic personal finance transaction dataset
for "Asya" — a 25-year-old full-time professional living in Ankara —
covering the full year 2025 (~850 transactions).

Run from the project root:
    python scripts/generate_data.py

Output:
    data/finance.csv
'''

import pandas as pd
import numpy as np
import random
from datetime import date, timedelta

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
random.seed(42)
np.random.seed(42)

START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 12, 31)

# ---------------------------------------------------------
# Reference data
# ---------------------------------------------------------

EXPENSE_CATEGORIES = {
    "Housing":        {"sub": ["Rent"],                              "merchants": ["Landlord"],                         "base": (8500, 8500), "monthly_fixed": True},
    "Food":           {"sub": ["Groceries", "Restaurant", "Cafe"],    "merchants": ["Migros", "Getir", "CarrefourSA", "Starbucks", "Local Cafe"], "base": (40, 650)},
    "Transportation": {"sub": ["Fuel", "Public Transport", "Taxi"],   "merchants": ["Shell", "Ankara EGO", "BiTaksi", "Petrol Ofisi"], "base": (25, 500)},
    "Utilities":       {"sub": ["Electricity", "Water", "Internet", "Phone"], "merchants": ["Enerjisa", "ASKI", "Turkcell", "Superonline"], "base": (150, 700), "monthly_fixed": True},
    "Entertainment":   {"sub": ["Streaming", "Cinema", "Concert"],     "merchants": ["Netflix", "Spotify", "Cinemaximum", "Biletix"], "base": (40, 900)},
    "Shopping":        {"sub": ["Clothing", "Electronics", "Home"],    "merchants": ["Zara", "Trendyol", "MediaMarkt", "IKEA"], "base": (150, 3500)},
    "Health":          {"sub": ["Pharmacy", "Doctor"],                 "merchants": ["Eczane", "Acibadem", "Medical Park"], "base": (50, 1200)},
    "Savings":         {"sub": ["Gold", "FX", "Mutual Fund"],          "merchants": ["IsYatirim", "Garanti BBVA"], "base": (1000, 5000)},
    "Education":       {"sub": ["Course", "Book"],                     "merchants": ["Udemy", "D&R", "Coursera"], "base": (60, 1500)},
    "Personal Care":   {"sub": ["Haircut", "Cosmetics"],                "merchants": ["Beauty Salon", "Gratis", "Sephora"], "base": (80, 900)},
}

INCOME_SOURCES = {
    "Salary":     {"sub": ["Monthly Salary"], "merchants": ["TechCorp A.S."], "base": (32000, 34000), "monthly_fixed": True},
    "Freelance":  {"sub": ["Freelance Project"], "merchants": ["Upwork", "Direct Client"], "base": (1500, 6000)},
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "Cash"]

# Seasonal multipliers per category per month (1.0 = normal)
def seasonal_multiplier(category, month):
    if category == "Transportation" and month in [6, 7, 8]:
        return 1.4  # summer travel
    if category == "Entertainment" and month in [6, 7, 8]:
        return 1.3
    if category == "Shopping" and month in [11, 12]:
        return 1.6  # Black Friday + New Year
    if category == "Health" and month in [1, 2]:
        return 1.2  # winter illnesses
    return 1.0

# ---------------------------------------------------------
# Transaction generation
# ---------------------------------------------------------

transactions = []
txn_counter = 1

def add_transaction(d, category, sub, amount, payment_method, merchant, ttype):
    global txn_counter
    transactions.append({
        "TransactionID": f"TXN{txn_counter:04d}",
        "Date": d,
        "Type": ttype,
        "Category": category,
        "SubCategory": sub,
        "Amount": round(amount, 2),
        "PaymentMethod": payment_method,
        "Merchant": merchant,
    })
    txn_counter += 1

# --- Fixed monthly transactions (Rent, Salary, Utilities) ---
months = pd.date_range(START_DATE, END_DATE, freq="MS")  # month start
for m in months:
    month_num = m.month

    # Salary - 1st of month (or close to it)
    salary_day = m.replace(day=random.choice([1, 1, 1, 28])) if month_num != 12 else m
    base = INCOME_SOURCES["Salary"]["base"]
    amount = random.uniform(*base)
    add_transaction(salary_day.date(), "Salary", "Monthly Salary", amount,
                     "Bank Transfer", "TechCorp A.S.", "Income")

    # Rent - 1st of month
    base = EXPENSE_CATEGORIES["Housing"]["base"]
    amount = random.uniform(*base)
    add_transaction(m.date(), "Housing", "Rent", -amount,
                     "Bank Transfer", "Landlord", "Expense")

    # Utilities - random day early in month
    for sub in EXPENSE_CATEGORIES["Utilities"]["sub"]:
        day = m + timedelta(days=random.randint(2, 10))
        base = EXPENSE_CATEGORIES["Utilities"]["base"]
        amount = random.uniform(*base) / len(EXPENSE_CATEGORIES["Utilities"]["sub"])
        merchant = random.choice(EXPENSE_CATEGORIES["Utilities"]["merchants"])
        add_transaction(day.date(), "Utilities", sub, -amount,
                         random.choice(PAYMENT_METHODS), merchant, "Expense")

# --- Occasional freelance income (random months) ---
freelance_months = random.sample(range(1, 13), k=4)
for month_num in freelance_months:
    d = date(2025, month_num, random.randint(5, 25))
    base = INCOME_SOURCES["Freelance"]["base"]
    amount = random.uniform(*base)
    add_transaction(d, "Freelance", "Freelance Project", amount,
                     "Bank Transfer", random.choice(INCOME_SOURCES["Freelance"]["merchants"]), "Income")

# --- Random day-to-day expense transactions across the year ---
TARGET_TOTAL = 850
remaining = TARGET_TOTAL - len(transactions)

variable_categories = [c for c in EXPENSE_CATEGORIES if c not in ("Housing",)]
# weight categories so Food/Transport/Shopping appear more often than Savings/Education
category_weights = {
    "Food": 0.30, "Transportation": 0.18, "Entertainment": 0.12,
    "Shopping": 0.15, "Health": 0.07, "Savings": 0.08,
    "Education": 0.05, "Personal Care": 0.05, "Utilities": 0.0  # already handled monthly
}
cats = [c for c in category_weights if category_weights[c] > 0]
weights = [category_weights[c] for c in cats]

all_days = pd.date_range(START_DATE, END_DATE, freq="D")

for _ in range(remaining):
    d = random.choice(all_days)
    month_num = d.month
    category = random.choices(cats, weights=weights, k=1)[0]
    info = EXPENSE_CATEGORIES[category]
    sub = random.choice(info["sub"])
    merchant = random.choice(info["merchants"])
    base_min, base_max = info["base"]
    amount = random.uniform(base_min, base_max) * seasonal_multiplier(category, month_num)
    payment_method = random.choice(PAYMENT_METHODS)
    add_transaction(d.date(), category, sub, -amount, payment_method, merchant, "Expense")

# ---------------------------------------------------------
# Build DataFrame
# ---------------------------------------------------------
df = pd.DataFrame(transactions)
df = df.sort_values("Date").reset_index(drop=True)
df["TransactionID"] = [f"TXN{i+1:04d}" for i in range(len(df))]

# ---------------------------------------------------------
# Intentionally introduce realistic data quality issues
# (these will be handled in the Data Cleaning phase)
# ---------------------------------------------------------
n = len(df)

# 1) Some missing PaymentMethod values
missing_idx = df.sample(frac=0.02, random_state=1).index
df.loc[missing_idx, "PaymentMethod"] = np.nan

# 2) A few missing Merchant values
missing_idx = df.sample(frac=0.015, random_state=2).index
df.loc[missing_idx, "Merchant"] = np.nan

# 3) A handful of duplicate rows (common real-world issue)
dup_rows = df.sample(frac=0.005, random_state=3)
df = pd.concat([df, dup_rows], ignore_index=True)

# 4) A couple of inconsistent category labels (case issues)
inconsistent_idx = df[df["Category"] == "Food"].sample(frac=0.05, random_state=4).index
df.loc[inconsistent_idx, "Category"] = "food"

df = df.sort_values("Date").reset_index(drop=True)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
output_path = "data/finance.csv"
df.to_csv(output_path, index=False)

print(f"✅ Dataset generated: {output_path}")
print(f"Total transactions: {len(df)}")
print(df.head(10))