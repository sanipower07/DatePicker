from datetime import datetime
import os
import random

from flask import Flask, flash, redirect, render_template, request, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Index
from sqlalchemy.engine import make_url
import shutil


app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Simple fixed key is fine for local/personal use; change if you ever share publicly.
app.config['SECRET_KEY'] = 'date-glas'

db = SQLAlchemy(app)


def _db_file_path() -> str:
    """Return absolute filesystem path for the SQLite database."""
    url = make_url(app.config['SQLALCHEMY_DATABASE_URI'])
    if url.drivername != 'sqlite' or not url.database:
        raise RuntimeError('Backup/Restore is only supported for SQLite.')
    path = url.database
    if not os.path.isabs(path):
        path = os.path.join(app.root_path, path)
    return path


class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    requires_money = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_activity_name_lower', func.lower(name), unique=True),
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<Activity {self.name!r} ({'money' if self.requires_money else 'free'})>"


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    activities = Activity.query.order_by(Activity.created_at.desc()).all()
    picked_id = request.args.get('picked', type=int)
    picked_activity = None
    if picked_id:
        picked_activity = Activity.query.get(picked_id)
    return render_template(
        'index.html',
        activities=activities,
        picked_activity=picked_activity,
    )


@app.route('/activities', methods=['POST'])
def add_activity():
    name = (request.form.get('name') or '').strip()
    requires_money = bool(request.form.get('requires_money'))

    if not name:
        flash('Bitte gib einen Namen ein.', 'error')
        return redirect(url_for('home'))

    existing = Activity.query.filter(func.lower(Activity.name) == name.lower()).first()
    if existing:
        flash('Diese Aktivität steht schon auf eurer Liste.', 'error')
        return redirect(url_for('home'))

    activity = Activity(name=name, requires_money=requires_money)
    db.session.add(activity)
    db.session.commit()

    flash('Neue Idee gespeichert!', 'success')
    return redirect(url_for('home'))


@app.route('/activities/<int:activity_id>/delete', methods=['POST'])
def delete_activity(activity_id: int):
    activity = Activity.query.get(activity_id)
    if not activity:
        flash('Aktivität nicht gefunden.', 'error')
        return redirect(url_for('home'))

    db.session.delete(activity)
    db.session.commit()

    flash('Aktivität gelöscht.', 'success')
    return redirect(url_for('home'))


@app.route('/pick', methods=['POST'])
def pick_activity():
    money_available = request.form.get('money_available') == 'yes'

    query = Activity.query
    if not money_available:
        query = query.filter_by(requires_money=False)

    activities = query.all()

    if not activities:
        flash('Wir brauchen noch mehr kostenlose Ideen 💕', 'error')
        return redirect(url_for('home'))

    choice = random.choice(activities)
    flash('Das Los sagt:', 'info')
    return redirect(url_for('home', picked=choice.id))


@app.route('/backup', methods=['GET'])
def backup():
    try:
        db_path = _db_file_path()
    except RuntimeError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('home'))
    return send_file(db_path, as_attachment=True, download_name='date-glas-backup.db')


@app.route('/restore', methods=['POST'])
def restore():
    file = request.files.get('backup')
    if not file or file.filename == '':
        flash('Keine Datei ausgewählt.', 'error')
        return redirect(url_for('home'))

    temp_path = os.path.join(app.root_path, 'restore-upload.db')
    file.save(temp_path)

    # Basic sanity check to ensure it looks like a SQLite file
    with open(temp_path, 'rb') as f:
        header = f.read(16)
    if header != b'SQLite format 3\x00':
        os.remove(temp_path)
        flash('Die Datei sieht nicht wie eine SQLite-Sicherung aus.', 'error')
        return redirect(url_for('home'))

    try:
        target_path = _db_file_path()
        db.session.remove()
        db.engine.dispose()
        shutil.copyfile(temp_path, target_path)
        flash('Backup eingespielt. Seite neu laden und weiter gehts.', 'success')
    except Exception as exc:  # noqa: BLE001 - want to surface any copy issue
        flash(f'Konnte Backup nicht einspielen: {exc}', 'error')
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return redirect(url_for('home'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
