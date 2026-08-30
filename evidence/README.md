# Run Record Evidence

Summary of 22 agent pipeline executions.

## Statistics

- **Total runs**: 22
- **Accepted**: 19
- **Rejected**: 1
- **Runs with precedence rules**: 8
- **Runs requiring >1 attempt**: 4

## Run Records

| Timestamp | Question | Sources | Precedence | Attempts | Verdict |
|-----------|----------|---------|------------|----------|----------|
| 2026-08-30T06-08-03.767821Z | How many days of rental am I covered for? | 1 | 1 rules | 1 | ✓ |
| 2026-08-30T06-08-40.646452Z | After my car is repaired, do you pay me for the lost resale ... | 0 | - | 1 | ✗ |
| 2026-08-30T06-45-39.576500Z | How many days of rental am I covered for and at what rate? | 0 | - | 0 | ✗ |
| 2026-08-30T06-46-37.859178Z | What is the total loss threshold? | 0 | - | 0 | ✗ |
| 2026-08-30T06-47-55.163865Z | How many days of rental am I covered for and at what rate? | 2 | 1 rules | 1 | ✓ |
| 2026-08-30T06-48-15.663545Z | After my car is repaired, do you pay me for the lost resale ... | 3 | - | 1 | ✓ |
| 2026-08-30T06-48-34.514855Z | We had a hailstorm damage 200 cars in our fleet. Does that t... | 1 | - | 2 | ✓ |
| 2026-08-30T07-21-19.418172Z | what is coverage for car accident loss claim | 3 | 2 rules | 2 | ✓ |
| 2026-08-30T07-23-12.623732Z | Do I pay a deductible for a cracked windshield? | 3 | - | 1 | ✓ |
| 2026-08-30T07-28-37.660696Z | How many days of rental am I covered for and at what rate? | 3 | 1 rules | 1 | ✓ |
| 2026-08-30T07-30-07.904254Z | A hailstorm damaged 200 cars in one county. How does that ch... | 1 | - | 1 | ✓ |
| 2026-08-30T07-31-05.272294Z | After my car is repaired, do you pay me for the lost resale ... | 3 | 1 rules | 1 | ✓ |
| 2026-08-30T07-43-54.914634Z | My car was totaled. How much do I get? | 1 | 2 rules | 2 | ✓ |
| 2026-08-30T07-44-15.231099Z | Do I pay a deductible for a cracked windshield? | 3 | - | 1 | ✓ |
| 2026-08-30T07-44-25.955801Z | When will an adjuster contact me? | 2 | 1 rules | 1 | ✓ |
| 2026-08-30T07-44-39.960643Z | My company van was hit. Which policy applies and what is the... | 3 | - | 1 | ✓ |
| 2026-08-30T07-44-53.086521Z | The car is garaged in Meridian and it is a total loss. Same ... | 1 | - | 1 | ✓ |
| 2026-08-30T07-45-02.073084Z | Can I use my own repair shop? | 2 | 1 rules | 2 | ✓ |
| 2026-08-30T07-45-21.181459Z | My claim was flagged for fraud. What happens, and who decide... | 2 | - | 1 | ✓ |
| 2026-08-30T07-48-16.434251Z | My company van was hit. Which policy applies and what is the... | 3 | - | 1 | ✓ |
| 2026-08-30T07-49-22.623698Z | When will an adjuster contact me? | 2 | - | 1 | ✓ |
| 2026-08-30T07-50-24.636131Z | The car is garaged in Meridian and it is a total loss. Same ... | 1 | - | 1 | ✓ |

## Precedence Rules Applied

**How many days of rental am I covered for?**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

**How many days of rental am I covered for and at what rate?**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

**what is coverage for car accident loss claim**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

**How many days of rental am I covered for and at what rate?**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

**After my car is repaired, do you pay me for the lost resale value?**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

**My car was totaled. How much do I get?**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

**When will an adjuster contact me?**
- later_effective_date: B2-adjuster-assignment-guideline > C5-catastrophe-surge-rules

**Can I use my own repair shop?**
- later_effective_date: D1-customer-faq > C2-repair-network-rules

## Detailed Records

### 2026-08-30T06-08-03.767821Z

**Question:** How many days of rental am I covered for?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- D4-bulletin-2026-04-rental-limit-change

**Precedence:**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

---

### 2026-08-30T06-08-40.646452Z

**Question:** After my car is repaired, do you pay me for the lost resale value?

**Verdict:** rejected

**Attempts:** 1

**Sources:** None

---

### 2026-08-30T06-45-39.576500Z

**Question:** How many days of rental am I covered for and at what rate?

**Verdict:** failed

**Attempts:** 0

**Sources:** None

**Failures:**
- invalid_input
- invalid_input
- retry_exhausted

---

### 2026-08-30T06-46-37.859178Z

**Question:** What is the total loss threshold?

**Verdict:** failed

**Attempts:** 0

**Sources:** None

**Failures:**
- invalid_input
- invalid_input
- retry_exhausted

---

### 2026-08-30T06-47-55.163865Z

**Question:** How many days of rental am I covered for and at what rate?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- C3-rental-reimbursement-limits
- D4-bulletin-2026-04-rental-limit-change

**Precedence:**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

---

### 2026-08-30T06-48-15.663545Z

**Question:** After my car is repaired, do you pay me for the lost resale value?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- B3-total-loss-valuation-procedure
- B4-total-loss-valuation-procedure-2023
- D1-customer-faq

---

### 2026-08-30T06-48-34.514855Z

**Question:** We had a hailstorm damage 200 cars in our fleet. Does that trigger catastrophe procedures?

**Verdict:** accepted

**Attempts:** 2

**Sources:**
- C5-catastrophe-surge-rules

---

### 2026-08-30T07-21-19.418172Z

**Question:** what is coverage for car accident loss claim

**Verdict:** accepted

**Attempts:** 2

**Sources:**
- B3-total-loss-valuation-procedure
- A1-personal-auto-policy-summary
- A5-exclusions-list

**Precedence:**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

---

### 2026-08-30T07-23-12.623732Z

**Question:** Do I pay a deductible for a cracked windshield?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- C4-glass-claim-handling
- A1-personal-auto-policy-summary
- C1-deductible-table

---

### 2026-08-30T07-28-37.660696Z

**Question:** How many days of rental am I covered for and at what rate?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- A3-endorsement-rental-coverage
- C3-rental-reimbursement-limits
- D4-bulletin-2026-04-rental-limit-change

**Precedence:**
- later_effective_date: D4-bulletin-2026-04-rental-limit-change > C3-rental-reimbursement-limits

---

### 2026-08-30T07-30-07.904254Z

**Question:** A hailstorm damaged 200 cars in one county. How does that change handling?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- C5-catastrophe-surge-rules

---

### 2026-08-30T07-31-05.272294Z

**Question:** After my car is repaired, do you pay me for the lost resale value?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- B3-total-loss-valuation-procedure
- D1-customer-faq
- B4-total-loss-valuation-procedure-2023

**Precedence:**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

---

### 2026-08-30T07-43-54.914634Z

**Question:** My car was totaled. How much do I get?

**Verdict:** accepted

**Attempts:** 2

**Sources:**
- B3-total-loss-valuation-procedure

**Precedence:**
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023
- later_effective_date: B3-total-loss-valuation-procedure > B4-total-loss-valuation-procedure-2023

---

### 2026-08-30T07-44-15.231099Z

**Question:** Do I pay a deductible for a cracked windshield?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- C1-deductible-table
- A1-personal-auto-policy-summary
- C4-glass-claim-handling

---

### 2026-08-30T07-44-25.955801Z

**Question:** When will an adjuster contact me?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- B2-adjuster-assignment-guideline
- C5-catastrophe-surge-rules

**Precedence:**
- later_effective_date: B2-adjuster-assignment-guideline > C5-catastrophe-surge-rules

---

### 2026-08-30T07-44-39.960643Z

**Question:** My company van was hit. Which policy applies and what is the limit?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- A3-endorsement-rental-coverage
- A2-commercial-fleet-policy
- A1-personal-auto-policy-summary

---

### 2026-08-30T07-44-53.086521Z

**Question:** The car is garaged in Meridian and it is a total loss. Same threshold?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- A4-state-amendment-meridian

---

### 2026-08-30T07-45-02.073084Z

**Question:** Can I use my own repair shop?

**Verdict:** accepted

**Attempts:** 2

**Sources:**
- C2-repair-network-rules
- D1-customer-faq

**Precedence:**
- later_effective_date: D1-customer-faq > C2-repair-network-rules

---

### 2026-08-30T07-45-21.181459Z

**Question:** My claim was flagged for fraud. What happens, and who decides?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- D3-escalation-matrix
- D2-fraud-flag-memo

---

### 2026-08-30T07-48-16.434251Z

**Question:** My company van was hit. Which policy applies and what is the limit?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- A2-commercial-fleet-policy
- C3-rental-reimbursement-limits
- A3-endorsement-rental-coverage

---

### 2026-08-30T07-49-22.623698Z

**Question:** When will an adjuster contact me?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- B2-adjuster-assignment-guideline
- C5-catastrophe-surge-rules

---

### 2026-08-30T07-50-24.636131Z

**Question:** The car is garaged in Meridian and it is a total loss. Same threshold?

**Verdict:** accepted

**Attempts:** 1

**Sources:**
- A4-state-amendment-meridian

---

