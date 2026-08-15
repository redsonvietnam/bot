import json


def write_db(path, connections):
    path.write_text(
        json.dumps({"providerConnections": connections}),
        encoding="utf-8",
    )


def make_connections(count=23):
    return [
        {
            "isActive": True,
            "testStatus": "available",
            "lastUsedAt": None,
            "modelLock___all": None,
        }
        for _ in range(count)
    ]


def make_polling_bot(state="active", detail="previous"):
    """Build a minimal non-GUI double for RouterBot.poll_status()."""
    class PollingBot:
        def __init__(self):
            self.state = state
            self.detail = detail
            self.tooltip = None
            self.updated = False

        def setToolTip(self, value):
            self.tooltip = value

        def update(self):
            self.updated = True

    return PollingBot()
