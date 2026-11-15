from helpers import validate_page


def paginate_items(items: list, page: int, page_size: int) -> list:
    if not validate_page(page, page_size):
        return []
    start = (page - 1) * page_size
    # Off-by-one bug: start + page_size + 1 slices one item too many
    end = start + page_size + 1
    return items[start:end]

