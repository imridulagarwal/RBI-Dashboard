from flask import Blueprint, jsonify, request, current_app
from src.utils.scraper import check_for_updates

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/update', methods=['POST'])
def trigger_update():
    """Trigger a manual update of the database"""
    try:
        # Run the update function with the current app context
        check_for_updates(current_app._get_current_object())
        
        return jsonify({
            'success': True,
            'message': 'Update process triggered successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
