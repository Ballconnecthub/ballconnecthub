from django.urls import path
from . import views


urlpatterns = [

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "profile-setup/",
        views.profile_setup,
        name="profile_setup"
    ),

    path(
        "terms/",
        views.terms_view,
        name="terms"
    ),

    path(
        "profile/<str:username>/",
        views.profile_view,
        name="profile"
    ),

    path(
        "delete-account/",
        views.delete_account,
        name="delete_account"
    ),

    path(
        "edit-profile/",
        views.edit_profile,
        name="edit_profile"
    ),

    path(
        "edit-video/<int:video_id>/",
        views.edit_video,
        name="edit_video"
    ),

    path(
        "follow/<str:username>/",
        views.follow_player,
        name="follow_player"
    ),

    path(
        "upload-video/",
        views.upload_video,
        name="upload_video"
    ),

    path(
        "like-video/<int:video_id>/",
        views.like_video,
        name="like_video"
    ),

    path(
        "comment-video/<int:video_id>/",
        views.add_comment,
        name="add_comment"
    ),

    path(
        "video/<int:video_id>/",
        views.watch_video,
        name="watch_video"
    ),

    path(
        "delete-video/<int:video_id>/",
        views.delete_video,
        name="delete_video"
    ),

    path(
        "save-video/<int:video_id>/",
        views.save_video,
        name="save_video"
    ),

    path(
        "share-video/<int:video_id>/",
        views.share_video,
        name="share_video"
    ),

    path(
    "report-video/<int:video_id>/",
    views.report_video,
    name="report_video"
),

    path(
        "scout-interest/<int:video_id>/",
        views.scout_interest,
        name="scout_interest"
    ),

    path(
        "trending/",
        views.trending_videos,
        name="trending_videos"
    ),

    path(
        "football-news/",
        views.football_news,
        name="football_news"
    ),

    path(
    "football-news/<slug:slug>/",
    views.football_news_article,
    name="football_news_article"
),

path(
    "moderation/",
    views.moderation_dashboard,
    name="moderation_dashboard"
),

]