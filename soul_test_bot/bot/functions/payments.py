import yookassa
from yookassa import Payment

from config import SHOP_ID, SECRET_KEY

yookassa.Configuration.account_id = SHOP_ID
yookassa.Configuration.secret_key = SECRET_KEY


def create(amount: int, user_id: int) -> (str, str):
    payment = Payment.create({
        'amount': {
            'value': str(amount),
            'currency': 'RUB'
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': 'https://t.me/SoulnearBot'
        },
        'capture': True,
        'description': f"Оплата подписки для пользователя {user_id}"
    })
    payment_url = payment.confirmation.confirmation_url
    payment_id = payment.id

    return payment_url, payment_id


async def check(payment_id: str) -> bool:
    payment = Payment.find_one(payment_id)

    return True if payment.status == "succeeded" else False


