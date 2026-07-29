from app.db.session import Base, engine
from app.models import (  # noqa: F401
    Conversation,
    Document,
    Message,
    Property,
    PropertyApiCache,
    PropertyRawSource,
    PropertyVerifiedProfile,
    Report,
    SavedProperty,
    User,
)

Base.metadata.create_all(bind=engine)
print("Database tables created successfully.")