class PipelineError(Exception):
    pass


class PluginError(PipelineError):
    def __init__(self, plugin_id: str, message: str):
        self.plugin_id = plugin_id
        self.message = message
        super().__init__(f"[{plugin_id}] {message}")


class StageError(PipelineError):
    def __init__(self, stage_name: str, message: str):
        self.stage_name = stage_name
        self.message = message
        super().__init__(f"[{stage_name}] {message}")


class HandlerNotFoundError(PipelineError):
    def __init__(self, event_type: str):
        self.event_type = event_type
        super().__init__(f"No handler registered for event type: {event_type}")
