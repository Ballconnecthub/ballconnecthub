from django.contrib import admin

from .models import (
    Profile,
    Video,
    Like,
    Comment,
    SavedVideo,
    ScoutInterest,
    ReportVideo,
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


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "player",
        "category",
        "views",
        "shares",
        "created_at",
    )

    list_filter = (
        "category",
        "created_at",
    )

    search_fields = (
        "title",
        "player__username",
    )


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "video",
        "created_at",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "video",
        "created_at",
    )

    search_fields = (
        "user__username",
        "text",
    )


@admin.register(SavedVideo)
class SavedVideoAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "video",
        "created_at",
    )


@admin.register(ScoutInterest)
class ScoutInterestAdmin(admin.ModelAdmin):
    list_display = (
        "scout",
        "video",
        "created_at",
    )


@admin.register(ReportVideo)
class ReportVideoAdmin(admin.ModelAdmin):
    list_display = (
        "reporter",
        "video",
        "reason",
        "resolved",
        "created_at",
    )

    list_filter = (
        "reason",
        "resolved",
    )

    search_fields = (
        "reporter__username",
        "video__title",
    )