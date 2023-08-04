from context.database import db

class BaseDbModel(db.Model):
    __abstract__ = True
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}