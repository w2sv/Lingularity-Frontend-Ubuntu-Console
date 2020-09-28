from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient


class VocableAdderBackend(TrainerBackend):
    def __init__(self, non_english_language: str, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english=False, mongodb_client=mongodb_client)

    def set_item_iterator(self):
        pass
