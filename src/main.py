from flask import Flask, render_template, request, jsonify
import logging
from connectors.gsheets_client import AttendanceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize AttendanceManager
try:
    attendance_manager = AttendanceManager()
    logger.info("AttendanceManager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AttendanceManager: {e}")
    attendance_manager = None


@app.route('/')
def index():
    """Render the main attendance page."""
    return render_template('index.html')


@app.route('/register-arrival', methods=['POST'])
def register_arrival():
    """
    Endpoint to register arrival time for a person.
    Expects JSON: {"id_number": "123456"}
    """
    try:
        if not attendance_manager:
            return jsonify({
                "success": False,
                "message": "Sistema no disponible. Contacte al administrador."
            }), 503

        # Get id_number from request
        data = request.get_json()
        
        if not data or 'id_number' not in data:
            return jsonify({
                "success": False,
                "message": "Debe proporcionar un número de identificación"
            }), 400
        
        id_number = str(data['id_number']).strip()
        
        if not id_number:
            return jsonify({
                "success": False,
                "message": "El número de identificación no puede estar vacío"
            }), 400
        
        # Register arrival
        result = attendance_manager.register_arrival(id_number)
        
        # Return result with appropriate status code
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in register_arrival endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "attendance_manager": "connected" if attendance_manager else "disconnected"
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)