class LarkUser:
    def __init__(self, email: str, en_name: str, name: str, id: str) -> None:
        self.email = email
        self.en_name = en_name
        self.name = name
        self.id = id
        pass

    def __str__(self) -> str:
        return f"name: {self.name}, id: {self.id}"

    def dict(self) -> dict:
        return {
            "email": self.email,
            "en_name": self.en_name,
            "name": self.name,
            "id": self.id,
        }
