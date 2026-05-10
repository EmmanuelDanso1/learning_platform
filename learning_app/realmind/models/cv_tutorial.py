import re
from datetime import datetime
from learning_app.extensions import db


class CVTutorial(db.Model):
    __tablename__ = 'cv_tutorial'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    youtube_url = db.Column(db.String(500), nullable=False)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    posted_at   = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id    = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

    _YT_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})',
    ]

    @property
    def video_id(self):
        for pattern in self._YT_PATTERNS:
            m = re.search(pattern, self.youtube_url or '')
            if m:
                return m.group(1)
        return None

    @property
    def embed_url(self):
        vid = self.video_id
        return (
            f"https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1"
            if vid else None
        )

    @property
    def watch_url(self):
        vid = self.video_id
        return f"https://www.youtube.com/watch?v={vid}" if vid else self.youtube_url

    @property
    def thumbnail_url(self):
        vid = self.video_id
        # hqdefault (480×360) — always available for public videos
        return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else None

    def __repr__(self):
        return f"<CVTutorial {self.id}: {self.title}>"
