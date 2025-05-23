import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, jsonify
from src.models.db import db
from src.routes.api import api_bp
from src.routes.admin import admin_bp
from apscheduler.schedulers.background import BackgroundScheduler
from src.utils.scraper import check_for_updates, force_update
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rbi_stats.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
        
        # Force initial data update
        logger.info("Initiating initial data update from RBI website")
        force_update(app)
    
    # Setup scheduler for periodic updates
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: check_for_updates(app), trigger="interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily updates")
    
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
