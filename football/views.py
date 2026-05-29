from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

import uuid

from .forms import RegisterForm, VideoUploadForm
from .models import Profile, Video, Like, Comment, SavedVideo, ScoutInterest, ReportVideo


def paginate_queryset(request, queryset, per_page=6):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def calculate_ranking_score(video):
    return (
        video.views +
        (video.likes.count() * 3) +
        (video.comments.count() * 4) +
        (video.saves.count() * 5) +
        (video.shares * 6) +
        (video.scout_interests.count() * 10)
    )


def home(request):
    query = request.GET.get("q", "")

    videos = Video.objects.select_related(
        "player",
        "player__profile"
    ).prefetch_related(
        "likes",
        "comments",
        "saves",
        "scout_interests"
    ).order_by("-created_at")

    players = User.objects.filter(
        profile__account_type="player"
    ).select_related("profile")[:20]

    if query:
        videos = videos.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(player__username__icontains=query) |
            Q(player__profile__country__icontains=query) |
            Q(player__profile__position__icontains=query) |
            Q(player__profile__club_or_academy__icontains=query)
        )

        players = User.objects.filter(
            profile__account_type="player"
        ).select_related("profile").filter(
            Q(username__icontains=query) |
            Q(profile__country__icontains=query) |
            Q(profile__position__icontains=query) |
            Q(profile__club_or_academy__icontains=query)
        )[:20]

    page_obj = paginate_queryset(request, videos, 6)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "video_feed_items.html",
            {"videos": page_obj},
            request=request
        )

        return JsonResponse({
            "html": html,
            "has_next": page_obj.has_next()
        })

    return render(request, "home.html", {
        "videos": page_obj,
        "players": players,
        "query": query,
        "has_next": page_obj.has_next(),
    })


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.is_active = True
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            profile.account_type = form.cleaned_data["account_type"]
            profile.email_verified = False
            profile.email_verification_token = str(uuid.uuid4())
            profile.save()

            verification_link = request.build_absolute_uri(
                f"/verify-email/{profile.email_verification_token}/"
            )

            send_mail(
                "Verify your Ballconnecthub email",
                (
                    f"Hello {user.username},\n\n"
                    f"Welcome to Ballconnecthub.\n\n"
                    f"Please verify your email by clicking this link:\n"
                    f"{verification_link}\n\n"
                    f"Thank you,\n"
                    f"Ballconnecthub Team"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            login(request, user)

            return redirect("email_verification_required")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def verify_email(request, token):
    profile = get_object_or_404(
        Profile,
        email_verification_token=token
    )

    profile.email_verified = True
    profile.email_verification_token = ""
    profile.save()

    return render(request, "email_verified.html")


@login_required
def email_verification_required(request):
    return render(request, "email_verification_required.html")


def login_view(request):
    error_message = None

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("home")

        error_message = "Wrong username or password. Please try again."

    return render(request, "login.html", {
        "error_message": error_message
    })


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_setup(request):
    profile = request.user.profile

    if request.method == "POST":
        profile.country = request.POST.get("country", "")

        if profile.account_type == "player":
            profile.age = request.POST.get("age") or None
            profile.position = request.POST.get("position", "")
            profile.club_or_academy = request.POST.get("club", "")
            profile.height = request.POST.get("height", "")
            profile.strong_foot = request.POST.get("strong_foot", "")
            profile.football_cv = request.POST.get("football_cv", "")

        elif profile.account_type == "scout":
            profile.scout_organization = request.POST.get("scout_organization", "")
            profile.scout_region = request.POST.get("scout_region", "")
            profile.scout_experience = request.POST.get("scout_experience") or None
            profile.scout_bio = request.POST.get("scout_bio", "")

        elif profile.account_type == "coach":
            profile.club_name = request.POST.get("club_name", "")
            profile.club_league = request.POST.get("club_league", "")
            profile.academy_name = request.POST.get("academy_name", "")
            profile.founded_year = request.POST.get("founded_year") or None
            profile.club_bio = request.POST.get("club_bio", "")

        profile.save()
        return redirect("profile", username=request.user.username)

    return render(request, "profile_setup.html", {
        "profile": profile
    })


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=profile_user)

    all_videos = profile_user.videos.prefetch_related(
        "likes",
        "comments",
        "saves",
        "scout_interests"
    ).order_by("-created_at")

    page_obj = paginate_queryset(request, all_videos, 6)

    for video in page_obj:
        video.ranking_score_value = calculate_ranking_score(video)

    total_likes = sum(video.likes.count() for video in all_videos)
    total_views = sum(video.views for video in all_videos)
    shared_videos_count = sum(video.shares for video in all_videos)

    scout_interests_count = ScoutInterest.objects.filter(
        scout=profile_user
    ).count()

    saved_videos_count = SavedVideo.objects.filter(
        user=profile_user
    ).count()

    return render(request, "profile.html", {
        "profile_user": profile_user,
        "profile": profile,
        "videos": page_obj,
        "total_likes": total_likes,
        "total_views": total_views,
        "scout_interests_count": scout_interests_count,
        "saved_videos_count": saved_videos_count,
        "shared_videos_count": shared_videos_count,
    })


def terms_view(request):
    return render(request, "terms.html")


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        return redirect("home")

    return render(request, "delete_account.html")


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        new_username = request.POST.get("username")

        if new_username:
            request.user.username = new_username
            request.user.save()

        profile.country = request.POST.get("country", "")

        if request.FILES.get("profile_photo"):
            profile.profile_photo = request.FILES.get("profile_photo")

        if profile.account_type == "player":
            profile.age = request.POST.get("age") or None
            profile.position = request.POST.get("position", "")
            profile.club_or_academy = request.POST.get("club", "")
            profile.height = request.POST.get("height", "")
            profile.strong_foot = request.POST.get("strong_foot", "")
            profile.football_cv = request.POST.get("football_cv", "")

        elif profile.account_type == "scout":
            profile.scout_organization = request.POST.get("scout_organization", "")
            profile.scout_region = request.POST.get("scout_region", "")
            profile.scout_experience = request.POST.get("scout_experience") or None
            profile.scout_bio = request.POST.get("scout_bio", "")

        elif profile.account_type == "coach":
            profile.club_name = request.POST.get("club_name", "")
            profile.club_league = request.POST.get("club_league", "")
            profile.academy_name = request.POST.get("academy_name", "")
            profile.founded_year = request.POST.get("founded_year") or None
            profile.club_bio = request.POST.get("club_bio", "")

        profile.save()
        return redirect("profile", username=request.user.username)

    return render(request, "edit_profile.html", {
        "profile": profile
    })


@login_required
def follow_player(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = profile_user.profile

    if request.user != profile_user:
        if request.user in profile.fans.all():
            profile.fans.remove(request.user)
        else:
            profile.fans.add(request.user)

    return redirect("profile", username=username)


@login_required
def upload_video(request):
    profile = request.user.profile

    if not request.user.is_staff and not profile.email_verified:
        return redirect("email_verification_required")

    if request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES)

        if form.is_valid():
            video = form.save(commit=False)
            video.player = request.user
            video.save()
            return redirect("profile", username=request.user.username)
    else:
        form = VideoUploadForm()

    return render(request, "upload_video.html", {
        "form": form
    })


@login_required
def like_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        video=video
    )

    if not created:
        like.delete()

    return redirect("profile", username=video.player.username)


@login_required
def add_comment(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.method == "POST":
        text = request.POST.get("text")

        if text:
            Comment.objects.create(
                user=request.user,
                video=video,
                text=text
            )

    return redirect("profile", username=video.player.username)


def watch_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    video.views += 1
    video.save(update_fields=["views"])

    recommended_videos = Video.objects.select_related(
        "player",
        "player__profile"
    ).prefetch_related(
        "likes",
        "comments",
        "saves",
        "scout_interests"
    ).exclude(id=video.id).filter(
        category=video.category
    ).order_by("-created_at")[:6]

    if not recommended_videos:
        recommended_videos = Video.objects.select_related(
            "player",
            "player__profile"
        ).exclude(id=video.id).order_by("-created_at")[:6]

    for recommended in recommended_videos:
        recommended.ranking_score_value = calculate_ranking_score(recommended)

    return render(request, "watch_video.html", {
        "video": video,
        "recommended_videos": recommended_videos,
    })


@login_required
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if video.player != request.user and not request.user.is_staff:
        return redirect("profile", username=video.player.username)

    if request.method == "POST":
        video.delete()

        if request.user.is_staff:
            return redirect("moderation_dashboard")

        return redirect("profile", username=request.user.username)

    return render(request, "delete_video.html", {
        "video": video
    })


@login_required
def edit_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if video.player != request.user:
        return redirect("profile", username=video.player.username)

    if request.method == "POST":
        video.title = request.POST.get("title")
        video.description = request.POST.get("description")
        video.category = request.POST.get("category")

        if request.FILES.get("video_file"):
            video.video_file = request.FILES.get("video_file")

        if request.FILES.get("thumbnail"):
            video.thumbnail = request.FILES.get("thumbnail")

        video.save()
        return redirect("profile", username=request.user.username)

    return render(request, "edit_video.html", {
        "video": video
    })


@login_required
def save_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    saved, created = SavedVideo.objects.get_or_create(
        user=request.user,
        video=video
    )

    if not created:
        saved.delete()

    return redirect("profile", username=video.player.username)


@login_required
def share_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    video.shares += 1
    video.save(update_fields=["shares"])

    share_link = f"https://www.ballconnecthub.com/video/{video.id}/"

    return render(request, "share_video.html", {
        "video": video,
        "share_link": share_link,
    })


@login_required
def scout_interest(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.user.profile.account_type not in ["scout", "coach"]:
        return redirect("profile", username=video.player.username)

    interest, created = ScoutInterest.objects.get_or_create(
        scout=request.user,
        video=video
    )

    if not created:
        interest.delete()

    return redirect("profile", username=video.player.username)


def trending_videos(request):
    videos = Video.objects.all().order_by("-views", "-created_at")

    page_obj = paginate_queryset(request, videos, 6)

    for video in page_obj:
        video.ranking_score_value = calculate_ranking_score(video)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "video_feed_items.html",
            {"videos": page_obj},
            request=request
        )

        return JsonResponse({
            "html": html,
            "has_next": page_obj.has_next()
        })

    return render(request, "trending.html", {
        "videos": page_obj,
        "has_next": page_obj.has_next(),
    })


@login_required
def moderation_dashboard(request):
    if not request.user.is_staff:
        return redirect("home")

    videos = Video.objects.all().order_by("-created_at")
    reports = ReportVideo.objects.all().order_by("-created_at")

    video_page = paginate_queryset(request, videos, 10)
    report_page = paginate_queryset(request, reports, 10)

    return render(request, "moderation_dashboard.html", {
        "videos": video_page,
        "reports": report_page,
    })


@login_required
def report_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        message = request.POST.get("message", "")

        ReportVideo.objects.create(
            reporter=request.user,
            video=video,
            reason=reason,
            message=message
        )

        return redirect("watch_video", video_id=video.id)

    return render(request, "report_video.html", {
        "video": video
    })


def impressum_view(request):
    return render(request, "impressum.html")


def privacy_view(request):
    return render(request, "privacy.html")


def copyright_view(request):
    return render(request, "copyright.html")


def cookies_view(request):
    return render(request, "cookies.html")