import os
import sys
import django
from django.db import connection
from django.apps import apps
from tabulate import tabulate

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

def get_all_tables():
    """Get all table names from the database"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%';")
        return [row[0] for row in cursor.fetchall()]

def get_table_data(table_name):
    """Get all data from a table"""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name};")
        return cursor.fetchall(), [col[0] for col in cursor.description]

def print_table_info(model):
    """Print information about a model and its fields"""
    print(f"\n{'='*80}")
    print(f"📋 TABLE: {model._meta.db_table} ({model.__name__})")
    print(f"{'='*80}")
    
    print(f"\n📝 DESCRIPTION: {model.__doc__ or 'No description available'}")
    
    # Print field information
    fields_info = []
    for field in model._meta.fields:
        field_type = field.get_internal_type()
        constraints = []
        if field.primary_key:
            constraints.append("PRIMARY KEY")
        if field.unique:
            constraints.append("UNIQUE")
        if not field.null:
            constraints.append("NOT NULL")
        if field.has_default():
            constraints.append(f"DEFAULT={field.get_default()}")
        
        fields_info.append([
            field.name,
            field_type,
            ", ".join(constraints),
            field.help_text or ""
        ])
    
    print("\n🔑 FIELDS:")
    print(tabulate(fields_info, headers=["Field Name", "Type", "Constraints", "Description"], tablefmt="pretty"))

def print_table_data(table_name):
    """Print all data from a table"""
    data, headers = get_table_data(table_name)
    
    if not data:
        print("\n📊 DATA: No records found")
        return
    
    print(f"\n📊 DATA ({len(data)} records):")
    print(tabulate(data, headers=headers, tablefmt="pretty"))
    print("\n")

def main():
    """Main function to display all database tables and their content"""
    print("\n" + "="*100)
    print("📂 QR ATTENDANCE SYSTEM DATABASE 📂".center(100))
    print("="*100)
    
    # Get all models
    all_models = apps.get_models()
    models_by_table = {model._meta.db_table: model for model in all_models}
    
    # Get all tables from database
    all_tables = get_all_tables()
    
    for table in sorted(all_tables):
        # Skip Django-specific tables
        if table.startswith('auth_') or table.startswith('django_'):
            continue
            
        # Print table information if we have the model
        if table in models_by_table:
            print_table_info(models_by_table[table])
        else:
            print(f"\n{'='*80}")
            print(f"📋 TABLE: {table}")
            print(f"{'='*80}")
            print("\n📝 DESCRIPTION: No model information available")
        
        # Print table data
        print_table_data(table)
        
        print("\n" + "-"*100)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 