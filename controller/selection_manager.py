class SelectionManager:
    def __init__(self):
        self.selected = []

    def select(self, element):
        self.selected.append(element)

    def deselect(self, element):
        self.selected.remove(element)

    def clear(self):
        self.selected = []