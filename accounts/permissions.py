from django.contrib.auth.decorators import user_passes_test


PARKING_ADMIN_GROUP = 'Адміністратор'
GATE_OPERATOR_GROUP = 'Оператор КПП'


def _is_active_staff(user):
    return user.is_authenticated and user.is_active and user.is_staff


def is_parking_admin(user):
    if not _is_active_staff(user):
        return False

    return user.is_superuser or user.groups.filter(name=PARKING_ADMIN_GROUP).exists()


def is_gate_operator(user):
    if not _is_active_staff(user):
        return False

    return user.groups.filter(name=GATE_OPERATOR_GROUP).exists()


def can_access_gate(user):
    return is_parking_admin(user) or is_gate_operator(user)


def can_mark_payment(user):
    return is_parking_admin(user)


parking_admin_required = user_passes_test(is_parking_admin)
gate_access_required = user_passes_test(can_access_gate)
payment_admin_required = user_passes_test(can_mark_payment)
