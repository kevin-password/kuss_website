from .models import Leadership, Member

def leadership_context(request):
    """Add leadership info to the context for every template."""
    member_id = request.session.get('member_id')
    context = {
        'is_treasurer': False,
        'is_leader': False,
        'leader_roles': [],
    }
    
    if member_id:
        try:
            member = Member.objects.get(id=member_id, is_active=True)
            
            # Check Treasurer
            context['is_treasurer'] = Leadership.objects.filter(
                member=member,
                role__in=['EXEC_TREASURER', 'BOARD_TREASURER'],
                is_current=True
            ).exists()
            
            # Check any leadership role
            leader_roles = Leadership.objects.filter(member=member, is_current=True).values_list('role', flat=True)
            context['is_leader'] = leader_roles.exists()
            context['leader_roles'] = list(leader_roles)
            
        except Member.DoesNotExist:
            pass
    
    return context
