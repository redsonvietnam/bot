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
