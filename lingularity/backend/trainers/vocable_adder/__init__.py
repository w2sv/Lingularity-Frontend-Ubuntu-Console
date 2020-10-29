from lingularity.backend.trainers.base import TrainerBackend


class VocableAdderBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english=train_english)

    def set_item_iterator(self):
        pass
