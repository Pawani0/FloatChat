"""Data formatters for converting database results to Recharts format"""
from typing import List, Dict, Any
from datetime import datetime

class DataFormatter:
    """Format database results for frontend visualization"""
    
    @staticmethod
    def format_for_recharts(raw_data: List[Dict], x_field: str, y_field: str) -> List[Dict]:
        """
        Transform DB results to Recharts format: [{name: string, value: number}]
        
        Args:
            raw_data: List of dictionaries from database
            x_field: Field name for x-axis (labels)
            y_field: Field name for y-axis (values)
            
        Returns:
            List of formatted data points
        """
        if not raw_data:
            return []
        
        formatted = []
        for row in raw_data:
            try:
                x_val = row.get(x_field)
                y_val = row.get(y_field)
                
                # Skip NaN and None values
                if y_val in ['NaN', None, 'nan', 'NAN'] or x_val in ['NaN', None, 'nan', 'NAN']:
                    continue
                
                # Format datetime objects
                if isinstance(x_val, datetime):
                    name = x_val.strftime('%b %Y')
                else:
                    name = str(x_val)
                
                # Convert to float, handle scientific notation
                try:
                    value = float(y_val)
                except (ValueError, TypeError):
                    continue
                
                formatted.append({"name": name, "value": round(value, 2)})
                
            except (ValueError, TypeError, KeyError) as e:
                # Skip malformed rows
                continue
        
        return formatted
    
    @staticmethod
    def format_temperature_profile(raw_data: List[Dict]) -> List[Dict]:
        """
        Format depth vs temperature data for profile plots
        
        Args:
            raw_data: Database results with 'pres' and 'temp' fields
            
        Returns:
            Formatted data for line charts
        """
        if not raw_data:
            return []
        
        formatted = []
        for row in raw_data:
            try:
                depth = row.get('pres') or row.get('depth')
                temp = row.get('temp_adjusted') or row.get('temp')
                
                if depth is None or temp in ['NaN', None, 'nan']:
                    continue
                
                formatted.append({
                    "name": f"{int(float(depth))}m",
                    "value": round(float(temp), 2)
                })
            except (ValueError, TypeError, KeyError):
                continue
        
        return formatted
    
    @staticmethod
    def format_time_series(raw_data: List[Dict], date_field: str, value_field: str) -> List[Dict]:
        """
        Format time-based data for trend analysis
        
        Args:
            raw_data: Database results with date and value fields
            date_field: Name of date field
            value_field: Name of value field
            
        Returns:
            Formatted time series data
        """
        if not raw_data:
            return []
        
        formatted = []
        for row in raw_data:
            try:
                date_val = row.get(date_field)
                value = row.get(value_field)
                
                if value in ['NaN', None, 'nan'] or date_val is None:
                    continue
                
                # Format date
                if isinstance(date_val, datetime):
                    name = date_val.strftime('%b %Y')
                elif isinstance(date_val, str):
                    name = date_val
                else:
                    name = str(date_val)
                
                formatted.append({
                    "name": name,
                    "value": round(float(value), 2)
                })
                
            except (ValueError, TypeError, KeyError):
                continue
        
        return formatted
    
    @staticmethod
    def format_multi_series(raw_data: List[Dict], x_field: str, y_fields: List[str]) -> List[Dict]:
        """
        Format data with multiple y-values for comparison charts
        
        Args:
            raw_data: Database results
            x_field: Field for x-axis
            y_fields: List of fields for y-axis (multiple lines)
            
        Returns:
            Formatted multi-series data
        """
        if not raw_data:
            return []
        
        formatted = []
        for row in raw_data:
            try:
                x_val = row.get(x_field)
                if x_val is None or x_val in ['NaN', 'nan']:
                    continue
                
                # Format x value
                if isinstance(x_val, datetime):
                    name = x_val.strftime('%b %Y')
                else:
                    name = str(x_val)
                
                # Build data point with multiple values
                data_point = {"name": name}
                
                for field in y_fields:
                    y_val = row.get(field)
                    if y_val not in ['NaN', None, 'nan']:
                        try:
                            data_point[field] = round(float(y_val), 2)
                        except (ValueError, TypeError):
                            pass
                
                # Only add if has at least one valid y value
                if len(data_point) > 1:
                    formatted.append(data_point)
                    
            except (KeyError, TypeError):
                continue
        
        return formatted
