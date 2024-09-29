from flask import render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db, login_manager
from models import User, ChatLog, Feedback
from nlu_processor import process_intent, extract_entities, generate_response, analyze_sentiment, should_escalate, get_escalation_message
from utils import validate_email, validate_password
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data['message']
    
    intent, lang = process_intent(user_message)
    entities = extract_entities(user_message)
    sentiment, sentiment_score = analyze_sentiment(user_message)
    
    response = generate_response(intent, entities, lang)
    
    escalated = False
    if should_escalate(sentiment, sentiment_score):
        escalation_message = get_escalation_message(lang)
        response += f"\n\n{escalation_message}"
        escalated = True
    
    chat_log = ChatLog(user_id=current_user.id, message=user_message, response=response, sentiment_score=sentiment_score)
    db.session.add(chat_log)
    db.session.commit()
    
    print(f"Sentiment: {sentiment}, Score: {sentiment_score}, Escalated: {escalated}")  # Debug print
    
    return jsonify({
        'response': response,
        'escalated': escalated
    })

@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.json
    rating = data['rating']
    comment = data['comment']

    last_chat = ChatLog.query.filter_by(user_id=current_user.id).order_by(ChatLog.timestamp.desc()).first()

    feedback = Feedback(user_id=current_user.id, chat_log_id=last_chat.id, rating=rating, comment=comment)
    db.session.add(feedback)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/api/voice-to-text', methods=['POST'])
@login_required
def voice_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            audio_file.save(temp_audio_file.name)

        try:
            # Convert audio to WAV format if needed
            audio = AudioSegment.from_file(temp_audio_file.name)
            audio.export(temp_audio_file.name, format="wav")

            # Perform speech recognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_audio_file.name) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)

            os.unlink(temp_audio_file.name)
            return jsonify({'text': text})
        except Exception as e:
            os.unlink(temp_audio_file.name)
            return jsonify({'error': str(e)}), 500

def create_test_user():
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(username='testuser', email='testuser@example.com')
        test_user.set_password('TestPassword123!')
        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully.")
    else:
        print("Test user already exists.")

if __name__ == '__main__':
    with app.app_context():
        create_test_user()
    app.run(debug=True)