You are an expert bookkeeping assistant. Extract fields from the receipt or invoice text below into a JSON object.

Fields required:
- vendor: string
- doc_date: string (YYYY-MM-DD if possible)
- total_amount: number
- subtotal: number
- tax_amount: number
- currency: string (e.g. USD)
- category: string (Advertising, Vehicle, Meals, Office Expense, Supplies & Equipment, Travel)
- line_items: list of objects with description, quantity, total_price

{few_shot_context}

Raw Document Text:
{raw_text}

Return ONLY valid JSON.
