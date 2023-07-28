class Person:
    def __init__(self, id, name, email, guid, photo, access_id, secret_id):
        self.id = id
        self.name = name
        self.email = email
        self.guid = guid
        self.photo = photo
        self.access_id = access_id
        self.secret_id = secret_id

    def __iter__(self):
        yield from {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "guid": self.guid,
            "photo": self.photo,
            "access_id": self.access_id,
            "secret_id": self.secret_id
        }.items()
