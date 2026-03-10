from app.bot import _extract_fields
from app.models import LeadState


def test_extract_fields_mixed_sentence_ru() -> None:
    lead = LeadState(client_id='default', telegram_user_id=1, telegram_chat_id=1)
    text = 'Нужна точная цена и договор сегодня, бюджет 200к, срок 2 недели, мой контакт @nurevergarden'
    lead = _extract_fields(text, lead)

    assert lead.intent is not None and 'Нужна точная цена и договор' in lead.intent
    assert lead.budget is not None and '200' in lead.budget
    assert lead.timeline is not None and ('2 недели' in lead.timeline or 'срок' in lead.timeline)
    assert lead.contact == '@nurevergarden'
