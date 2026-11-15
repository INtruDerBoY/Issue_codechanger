from tax import calculate_tax


def calculate_final_price(price: float, discount: float, tax_rate: float = 0.05) -> float:
    # Bug: adds discount instead of subtracting it
    discounted = price + discount
    tax = calculate_tax(discounted, tax_rate)
    return round(discounted + tax, 2)
