# -*- coding: utf-8 -*-

import arrow

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from email.MIMEImage import MIMEImage

from coderdojochi.models import Mentor, Donation
from coderdojochi.util import email

from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received


@receiver(pre_save, sender=Mentor)
def avatar_updated_handler(sender, instance, **kwargs):

    try:
        original_mentor = Mentor.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        return

    if not instance.avatar:
        return

    if original_mentor.avatar != instance.avatar:

        instance.avatar_approved = False

        msg = email(
            subject='{} {} | Mentor Avatar Changed'.format(
                instance.user.first_name,
                instance.user.last_name
            ),
            template_name='avatar-changed-mentor',
            context={
                'first_name': instance.user.first_name,
                'last_name': instance.user.last_name,
                'image': 'avatar',
                'approve_url': instance.get_approve_avatar_url(),
                'reject_url': instance.get_reject_avatar_url(),
            },
            recipients=[settings.CONTACT_EMAIL],
            preheader='Mentor Avatar Changed',
            send=False
        )

        msg.mixed_subtype = 'related'

        img = MIMEImage(instance.avatar.read())
        img.add_header('Content-Id', 'avatar')
        img.add_header("Content-Disposition", "inline", filename="avatar")

        msg.attach(img)

        msg.send()


def donate_callback(sender, **kwargs):
    ipn_obj = sender

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        donation = get_object_or_404(Donation, id=ipn_obj.invoice)
        donation.is_verified = True

        if not donation.receipt_sent:
            email(
                subject='Donations Receipt from CoderDojoChi',
                template_name='donation-receipt',
                context={
                    'first_name': donation.first_name,
                    'last_name': donation.last_name,
                    'email': donation.email,
                    'amount': '${:0,.2f}'.format(donation.amount),
                    'transaction_date': arrow.get(
                        donation.created_at
                    ).to('local').format(
                        'MMMM D, YYYY h:ss a'
                    ),
                    'transaction_id': donation.id
                },
                recipients=[donation.email],
                bcc=[settings.CONTACT_EMAIL],
                preheader='Your generous donation is what'
                          ' makes CoderDojoChi possible.',
            )

            donation.receipt_sent = True

        donation.save()


valid_ipn_received.connect(donate_callback)
