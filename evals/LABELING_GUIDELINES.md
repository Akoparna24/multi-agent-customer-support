CATEGORIES (copied from src/supervisor.py prompt)
- billing: payment issues, refunds, invoices, subscription charges, pricing
- technical: app bugs, crashes, errors, login issues, performance problems
- general: working hours, contact info, company info, account settings, policies

TIE-BREAKER RULES
1. Two problems in one message → label the one blocking the customer from
   using the product; if neither is, label the first one mentioned.
   e.g. "charged twice and the app is slow" → billing
2. Paid but feature not unlocked → billing.
   e.g. "bought premium, still showing free plan" → billing
3. Password/login problems → technical. Profile/settings changes → general.
   e.g. "can't reset my password" → technical
   e.g. "how do I change my email address?" → general
4. Price questions → billing.
   e.g. "how much is the pro plan?" → billing