from .models import Leadership, Member

def is_treasurer_context(request):
    """Add is_treasurer to the context for every template."""
    member_id = request.session.get('member_id')
    if member_id:
        try:
            member = Member.objects.get(id=member_id, is_active=True)
            is_treasurer = Leadership.objects.filter(
                member=member,
                role__in=['EXEC_TREASURER', 'BOARD_TREASURER'],
                is_current=True
            ).exists()
            return {'is_treasurer': is_treasurer}
        except Member.DoesNotExist:
            pass
    return {'is_treasurer': False}
