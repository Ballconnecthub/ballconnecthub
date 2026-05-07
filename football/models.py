from cloudinary_storage.storage import VideoMediaCloudinaryStorage, MediaCloudinaryStorage
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from moviepy import VideoFileClip
import tempfile
import os


def validate_video_duration(video):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

    for chunk in video.chunks():
        temp_file.write(chunk)

    temp_file.close()

    try:
        clip = VideoFileClip(temp_file.name)
        duration = clip.duration
        clip.close()

        if duration > 180:
            raise ValidationError("Video must be maximum 3 minutes.")

    except ValidationError:
        raise

    except Exception:
        raise ValidationError("Invalid video file.")

    finally:
        video.seek(0)

        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


class Profile(models.Model):
    ACCOUNT_TYPES = (
        ("admin", "Admin"),
        ("player", "Player"),
        ("fan", "Fan"),
        ("scout", "Scout"),
        ("coach", "Coach/Club"),
    )

    POSITIONS = (
        ("goalkeeper", "Goalkeeper"),
        ("defender", "Defender"),
        ("midfielder", "Midfielder"),
        ("forward", "Forward"),
    )

    STRONG_FOOT = (
        ("right", "Right"),
        ("left", "Left"),
        ("both", "Both"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default="player"
    )

    country = models.CharField(max_length=100, blank=True)

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True
    )

    fans = models.ManyToManyField(
        User,
        related_name="followed_players",
        blank=True
    )

    admin_role = models.CharField(
        max_length=150,
        blank=True,
        default="Ballconnecthub Platform Administrator"
    )

    admin_access_level = models.CharField(
        max_length=150,
        blank=True,
        default="Full Moderation Access"
    )

    admin_permissions = models.TextField(
        blank=True,
        default="User moderation, video moderation, reports review, verification management, platform protection."
    )

    age = models.PositiveIntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, choices=POSITIONS, blank=True)
    club_or_academy = models.CharField(max_length=150, blank=True)
    height = models.CharField(max_length=50, blank=True)
    strong_foot = models.CharField(max_length=20, choices=STRONG_FOOT, blank=True)
    football_cv = models.TextField(blank=True)

    scout_organization = models.CharField(max_length=150, blank=True)
    scout_region = models.CharField(max_length=150, blank=True)
    scout_experience = models.PositiveIntegerField(null=True, blank=True)
    scout_bio = models.TextField(blank=True)
    verified_scout = models.BooleanField(default=False)

    club_name = models.CharField(max_length=150, blank=True)
    club_league = models.CharField(max_length=150, blank=True)
    academy_name = models.CharField(max_length=150, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    club_bio = models.TextField(blank=True)
    verified_club = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["account_type"]),
            models.Index(fields=["country"]),
            models.Index(fields=["position"]),
            models.Index(fields=["club_or_academy"]),
        ]
    def __str__(self):
        return self.user.username


class Video(models.Model):
    SKILL_CATEGORIES = (
        ("dribbling", "Dribbling"),
        ("shooting", "Shooting"),
        ("passing", "Passing"),
        ("goals", "Goals"),
        ("goalkeeper", "Goalkeeper Saves"),
        ("freestyle", "Freestyle"),
        ("training", "Training Drills"),
        ("match", "Match Highlights"),
    )

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="videos"
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=SKILL_CATEGORIES)

    video_file = models.FileField(
        upload_to="football_videos/",
        storage=VideoMediaCloudinaryStorage(),
        validators=[validate_video_duration]
    )

    thumbnail = models.ImageField(
        upload_to="video_thumbnails/",
        storage=MediaCloudinaryStorage(),
        blank=True,
        null=True
    )

    views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["views"]),
            models.Index(fields=["player"]),
            models.Index(fields=["title"]),
        ]

    @property
    def ranking_score(self):
        return (
            self.views +
            (self.likes.count() * 3) +
            (self.comments.count() * 4) +
            (self.saves.count() * 5) +
            (self.shares * 6) +
            (self.scout_interests.count() * 10)
        )

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    def total_saves(self):
        return self.saves.count()

    def total_scout_interests(self):
        return self.scout_interests.count()

    def __str__(self):
        return self.title


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="likes"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "video")

    def __str__(self):
        return f"{self.user.username} likes {self.video.title}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class SavedVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="saves"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "video")

    def __str__(self):
        return f"{self.user.username} saved {self.video.title}"


class ScoutInterest(models.Model):
    scout = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="scout_interests"
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="scout_interests"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("scout", "video")

    def __str__(self):
        return f"{self.scout.username} interested in {self.video.title}"


class ReportVideo(models.Model):
    REPORT_REASONS = (
        ("spam", "Spam"),
        ("copyright", "Copyright"),
        ("fake", "Fake Account"),
        ("violence", "Violence"),
        ("abuse", "Abusive Content"),
        ("inappropriate", "Inappropriate Content"),
        ("other", "Other"),
    )

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="video_reports"
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reason = models.CharField(
        max_length=50,
        choices=REPORT_REASONS
    )

    message = models.TextField(blank=True)

    resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["resolved"]),
            models.Index(fields=["reason"]),
            models.Index(fields=["video"]),
            models.Index(fields=["reporter"]),
        ]

    def __str__(self):
        return f"{self.reporter.username} reported {self.video.title}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)