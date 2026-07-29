from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.property import Property
from app.models.property_verified_profile import PropertyVerifiedProfile
from app.services.llm_assistant_service import PropertyAssistant


def generate_reply(db: Session, property_id: int, message: str) -> tuple[str, int]:
    prop = db.query(Property).filter(Property.id == property_id).first()
    profile = db.query(PropertyVerifiedProfile).filter(PropertyVerifiedProfile.property_id == property_id).first()

    convo = db.query(Conversation).filter(Conversation.property_id == property_id).first()
    if not convo:
        convo = Conversation(user_id=1, property_id=property_id, topic=prop.address if prop else "Property chat")
        db.add(convo)
        db.commit()
        db.refresh(convo)

    db.add(Message(conversation_id=convo.id, role="user", content=message))

    facts = profile.verified_payload if profile else {}
    history = [
        {"role": item.role, "content": item.content}
        for item in (
            db.query(Message)
            .filter(Message.conversation_id == convo.id)
            .order_by(Message.id.asc())
            .all()
        )
    ]
    reply = PropertyAssistant().answer_question(message, facts, history)

    db.add(Message(conversation_id=convo.id, role="assistant", content=reply))
    db.commit()
    return reply, convo.id
