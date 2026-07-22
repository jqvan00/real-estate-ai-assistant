from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.property import Property
from app.models.property_profile import PropertyProfile


def generate_reply(db: Session, property_id: int, message: str) -> tuple[str, int]:
    prop = db.query(Property).filter(Property.id == property_id).first()
    profile = db.query(PropertyProfile).filter(PropertyProfile.property_id == property_id).first()

    convo = db.query(Conversation).filter(Conversation.property_id == property_id).first()
    if not convo:
        convo = Conversation(user_id=1, property_id=property_id, topic=prop.address if prop else "Property chat")
        db.add(convo)
        db.commit()
        db.refresh(convo)

    db.add(Message(conversation_id=convo.id, role="user", content=message))

    facts = profile.verified_payload if profile else {}
    reply = (
        f"Based on the verified profile for {prop.address if prop else 'this property'}, "
        f"I see {facts.get('beds', 'unknown')} beds, {facts.get('baths', 'unknown')} baths, "
        f"and about {facts.get('sqft', 'unknown')} sqft. "
        f"Ask me about value, schools, flood risk, commute, or renovation upside."
    )

    db.add(Message(conversation_id=convo.id, role="assistant", content=reply))
    db.commit()
    return reply, convo.id
