from .permissions import (
    can_access_gate as user_can_access_gate,
    can_mark_payment as user_can_mark_payment,
    is_gate_operator as user_is_gate_operator,
    is_parking_admin as user_is_parking_admin,
)


def staff_roles(request):
    user = request.user

    return {
        'is_parking_admin': user_is_parking_admin(user),
        'is_gate_operator': user_is_gate_operator(user),
        'can_access_gate': user_can_access_gate(user),
        'can_mark_payment': user_can_mark_payment(user),
    }
