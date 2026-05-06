from django.contrib import admin
from .models import ReportVideo
from .models import (
    Profile,
    Video,
    Like,
    Comment,
    SavedVideo,
    ScoutInterest
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "account_type",
        "country",
        "verified_scout",
        "verified_club",
    )

    list_filter = (
        "account_type",
        "verified_scout",
        "verified_club",
    )

    search_fields = (
        "user__username",
        "country",
    )


admin.site.register(Video)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(SavedVideo)
admin.site.register(ScoutInterest)
admin.site.register(ReportVideo)