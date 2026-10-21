from .controlFlow import ControlFlow

class ContinueFlow(ControlFlow):
    def to_dict(self):
        return {"type": "ContinueFlow"}
