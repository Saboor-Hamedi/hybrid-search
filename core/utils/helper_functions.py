# Back to the menu
def go_back(text):
    return text.lower() in ["back", "b"]


# Skip empty input
def check_if_empty_input(text):
    return len(text.strip()) == 0
