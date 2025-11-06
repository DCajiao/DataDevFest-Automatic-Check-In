import os
import gspread
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AttendanceManager:
    def __init__(self):
        """Initialize connection to Google Sheets for attendance control."""
        load_dotenv()

        creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
        
        if not creds_path:
            msg = "Environment variable 'GOOGLE_SHEETS_CREDENTIALS_PATH' must be defined."
            logger.error(msg)
            raise ValueError(msg)

        # Sheet and worksheet names
        self.sheet_name = "Control de asistencia"
        self.worksheet_name = "asistentes"

        # Google Sheets scope
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        # Authenticate
        if not os.path.exists(creds_path):
            msg = f"Credentials file not found at {creds_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)
        
        credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        self.client = gspread.authorize(credentials)

        # Open sheet and worksheet
        try:
            self.sheet = self.client.open(self.sheet_name)
            self.worksheet = self.sheet.worksheet(self.worksheet_name)
            logger.info(f"Connected to '{self.sheet_name}' - '{self.worksheet_name}'")
        except Exception as e:
            logger.error(f"Error opening sheet/worksheet: {e}")
            raise

    def _get_colombia_timestamp(self) -> str:
        """Generate current timestamp in Colombia timezone."""
        colombia_tz = pytz.timezone("America/Bogota")
        now = datetime.now(colombia_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_colombia_datetime(self) -> datetime:
        """Get current datetime in Colombia timezone."""
        colombia_tz = pytz.timezone("America/Bogota")
        return datetime.now(colombia_tz)
    
    def _determine_shift(self, timestamp_dt: datetime) -> str:
        """Determine if arrival is morning or afternoon shift."""
        if timestamp_dt.hour < 12:
            return "Jornada Mañana"
        else:
            return "Jornada Tarde"

    def _find_person_row(self, id_number: str) -> tuple:
        """
        Find person by id_number and return (row_index, row_data).
        Returns (None, None) if not found.
        """
        try:
            all_records = self.worksheet.get_all_records()
            
            for idx, record in enumerate(all_records):
                if str(record.get("id_number", "")).strip() == str(id_number).strip():
                    # idx + 2 because: 1 for header, 1 for 0-indexing
                    return (idx + 2, record)
            
            return (None, None)
        except Exception as e:
            logger.error(f"Error searching for id_number {id_number}: {e}")
            raise

    def register_arrival(self, id_number: str) -> dict:
        """
        Register arrival time for a person given their id_number.
        
        Returns:
            dict: Status message with result including shift (morning/afternoon)
        """
        try:
            row_index, person_data = self._find_person_row(id_number)
            
            if row_index is None:
                logger.warning(f"ID {id_number} not found")
                return {
                    "success": False,
                    "message": "Persona no registrada",
                    "id_number": id_number
                }
            
            # Get current datetime and timestamp
            current_dt = self._get_colombia_datetime()
            new_timestamp = current_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine shift
            shift = self._determine_shift(current_dt)
            
            # Get existing arrival times
            current_arrival = person_data.get("arrival_time", "")
            
            # Build new arrival_time value
            if current_arrival and str(current_arrival).strip():
                # Append to existing timestamps (comma-separated list)
                updated_arrival = f"{current_arrival}, {new_timestamp}"
            else:
                # First timestamp
                updated_arrival = new_timestamp
            
            # Update the cell (column E is arrival_time, index 5)
            self.worksheet.update_cell(row_index, 5, updated_arrival)
            
            logger.info(f"Arrival registered for {person_data.get('name')} (ID: {id_number}) - {shift}")
            
            return {
                "success": True,
                "message": "Asistencia registrada exitosamente",
                "id_number": id_number,
                "name": person_data.get("name"),
                "timestamp": new_timestamp,
                "shift": shift,
                "all_arrivals": updated_arrival
            }
            
        except Exception as e:
            logger.error(f"Error registering arrival for {id_number}: {e}")
            return {
                "success": False,
                "message": f"Error al registrar asistencia: {str(e)}",
                "id_number": id_number
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = AttendanceManager()
    
    # Test with an ID number
    test_id = input("Ingrese el número de identificación: ")
    result = manager.register_arrival(test_id)
    
    print("\n" + "="*50)
    print("RESULTADO:")
    print("="*50)
    for key, value in result.items():
        print(f"{key}: {value}")