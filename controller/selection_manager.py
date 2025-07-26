class SelectionManager:
    def __init__(self):
        self.selected = []

    def select(self, element):
        if element in self.selected:
            self.selected.remove(element)
        else:
            self.selected.append(element)

    def clear(self):
        self.selected = []