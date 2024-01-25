import frappe 



def check_if_previously_paid(fees):
    for schedule in fees.payment_schedule:
        if schedule.outstanding == 0:
             return 1 
    return 0
         

def get_first_unpaid_term(fees):
    """
    Get the payment term of the first unpaid term in the payment schedule.

    Args:
    - fees: Object representing fees with a payment schedule.

    Returns:
    - payment_term: Payment term of the first unpaid term.
    """
    for schedule in fees.payment_schedule:
        if schedule.outstanding > 0:
            return schedule.payment_term

def get_last_term(fees):
    """
    Get the payment term of the last term in the payment schedule.

    Args:
    - fees: Object representing fees with a payment schedule.

    Returns:
    - payment_term: Payment term of the last term.
    """
    no_of_terms = len(fees.payment_schedule)
    for schedule in fees.payment_schedule:
        if schedule.idx == no_of_terms:
            return schedule.payment_term