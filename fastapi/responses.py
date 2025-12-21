class PlainTextResponse:
    def __init__(self, content: str = "", media_type: str = "text/plain"):
        self.content = content
        self.media_type = media_type

    def __call__(self, *args, **kwargs):  # pragma: no cover - compatibility
        return self
