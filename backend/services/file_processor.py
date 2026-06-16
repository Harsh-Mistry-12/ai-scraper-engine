import pandas as pd
import json
from io import BytesIO

class FileProcessor:
    """
    Handles reading and writing user files (CSV, XLSX, JSON, XML).
    """
    
    def process_upload(self, file_content: bytes, filename: str) -> list[dict]:
        """Convert uploaded file into a standard list of dictionaries."""
        ext = filename.split('.')[-1].lower()
        
        try:
            if ext == 'csv':
                df = pd.read_csv(BytesIO(file_content))
                return df.to_dict(orient='records')
            elif ext in ['xlsx', 'xls']:
                df = pd.read_excel(BytesIO(file_content))
                return df.to_dict(orient='records')
            elif ext == 'json':
                return json.loads(file_content)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise ValueError(f"Failed to process file: {str(e)}")

    def generate_output(self, data: list[dict], format: str) -> tuple[bytes, str]:
        """Convert scraped data list into the desired output format."""
        df = pd.DataFrame(data)
        
        if format == 'csv':
            return df.to_csv(index=False).encode('utf-8'), "text/csv"
        elif format == 'xlsx':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif format == 'json':
            return json.dumps(data, indent=2).encode('utf-8'), "application/json"
        elif format == 'xml':
            return df.to_xml(index=False).encode('utf-8'), "application/xml"
        else:
            raise ValueError(f"Unsupported output format: {format}")
