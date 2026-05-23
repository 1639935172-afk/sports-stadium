from django.shortcuts import render

from stadiums.models import Stadium, StadiumAuditStatus


def home(request):
    featured_stadiums = list(
        Stadium.objects.filter(
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
            deletion_requested=False,
        ).order_by('name')[:3]
    )
    return render(request, 'home.html', {'featured_stadiums': featured_stadiums})
