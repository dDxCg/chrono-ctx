from abc import ABC, abstractmethod

class EventBroker(ABC):

    @abstractmethod
    def publish(self, event):
        pass

    @abstractmethod
    def consume(self):
        pass

    @abstractmethod
    def close(self):
        pass