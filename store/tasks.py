from django.core.mail import send_mail
from storefront.celery import celery


@celery.task
def send_order_confirmation(order_id):
    print('NOTIFICATION')
    print(order_id)
    return send_mail('subject', 'message', 'from@moshbuy.com', ['programmingwithmosh@gmail.com'])
