import os
import django
import sys
from django.db import connection
from django.apps import apps

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

def print_section(title):
    """Print a section title"""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def get_model_tables():
    """Get all Django models and their table names"""
    return {model._meta.db_table: model for model in apps.get_models()}

def describe_table(table_name, model=None):
    """Print detailed information about a database table"""
    print(f"\n📋 TABLE: {table_name}")
    print("-" * 50)
    
    # Get table columns
    with connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
    
    if not columns:
        print("Table not found or has no columns.")
        return
    
    # Print model docstring if available
    if model and model.__doc__:
        print(f"Description: {model.__doc__}")
    
    # Print column information
    print("\nColumns:")
    print(f"{'Name':<20} {'Type':<15} {'PK':<5} {'Nullable':<10} {'Default':<15}")
    print("-" * 70)
    
    for col in columns:
        col_id, name, col_type, notnull, default_value, pk = col
        print(f"{name:<20} {col_type:<15} {'Yes' if pk else 'No':<5} {'No' if notnull else 'Yes':<10} {default_value if default_value is not None else '':<15}")

def get_foreign_keys(table_name):
    """Get foreign key information for a table"""
    with connection.cursor() as cursor:
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        return cursor.fetchall()

def print_relationships(table_name):
    """Print foreign key relationships for a table"""
    foreign_keys = get_foreign_keys(table_name)
    
    if not foreign_keys:
        print("\nNo foreign key relationships.")
        return
    
    print("\nRelationships:")
    print(f"{'From Column':<20} {'To Table':<25} {'To Column':<20}")
    print("-" * 70)
    
    for fk in foreign_keys:
        id, seq, table, from_col, to_col, on_update, on_delete, match = fk
        print(f"{from_col:<20} {table:<25} {to_col:<20}")

# Main execution
if __name__ == "__main__":
    print_section("QR ATTENDANCE SYSTEM DATABASE SCHEMA")
    print("This report shows the structure of the database tables used in the system.")
    
    # Get all model tables
    model_tables = get_model_tables()
    
    # Get all tables from database that aren't Django internals
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%';")
        tables = [row[0] for row in cursor.fetchall()]
    
    # Print schema for each important table
    for table in sorted(tables):
        # Skip Django internal tables
        if table.startswith('auth_') or table.startswith('django_'):
            continue
            
        model = model_tables.get(table)
        describe_table(table, model)
        print_relationships(table)
        print("\n" + "-" * 80)
    
    print("\n" + "="*80)
    print("DATABASE SCHEMA REPORT COMPLETE")
    print("="*80) 